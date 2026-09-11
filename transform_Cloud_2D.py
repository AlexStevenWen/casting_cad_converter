import numpy as np
import open3d as o3d
import matplotlib.pyplot as plt
import os
import shutil
import uuid
import h5py

def Cloud_Heatmap_Render(
        cloud_file,       # 支援 .npz, .h5, .ply, .pcd
        output_png,
        camera_angles,
        image_width,
        image_height,
        radius,
        depth_range       # 預設強度範圍 (例如 [0, 255])
):
    if not os.path.exists(cloud_file):
        raise FileNotFoundError(f"找不到檔案: {cloud_file}")

    # --- 核心邏輯：統一取額外維度轉熱力圖 ---
    def get_heatmap_colors(data_arr, default_range):
        """
        data_arr shape: (N, D)
        邏輯：
        1. 抓取強度欄位 (Index 6 或 Index 3)。
        2. 判斷數值範圍 (是否為 0-1)。
        3. 轉為 Jet 熱力圖。
        """
        dims = data_arr.shape[1]
        intensity = None
        
        # 1. 抓取強度值 (Intensity)
        if dims >= 7:
            # 6+1 結構 (XYZ + Normal + I)，取 Index 6
            print(f">> 偵測到 {dims} 維度，取 Index 6 為強度值")
            intensity = data_arr[:, 6]
        elif dims >= 4:
            # 3+1 結構 (XYZ + I)，取 Index 3
            print(f">> 偵測到 {dims} 維度，取 Index 3 為強度值")
            intensity = data_arr[:, 3]
        else:
            print(f">> 維度 {dims} 不足，無法產生熱力圖，顯示黑色")
            return np.zeros((data_arr.shape[0], 3))

        # 2. 數值範圍判斷 (處理 0~1 與 0~255 混雜的情況)
        val_min = np.min(intensity)
        val_max = np.max(intensity)
        
        # --- 修正解包錯誤的防呆邏輯 ---
        if isinstance(default_range, (int, float)):
            current_vmin, current_vmax = 0.0, float(default_range)
        else:
            current_vmin, current_vmax = default_range
        # -----------------------------
        
        # 如果數據最大值 <= 1.0 (且不全為0)，但預設範圍很大 (例如 255)，則自動切換為 [0, 1] 模式
        if val_max <= 1.0 and val_max > 0 and current_vmax > 1.0:
            print(f"   [提示] 偵測到數值分佈於 0~1 之間 (Max={val_max:.2f})，自動切換範圍為 [0.0, 1.0]")
            current_vmin, current_vmax = 0.0, 1.0
        
        # 如果數據最大值 <= 1.0 (且不全為0)，但預設範圍很大 (例如 255)，則自動切換為 [0, 1] 模式
        if val_max <= 1.0 and val_max > 0 and current_vmax > 1.0:
            print(f"   [提示] 偵測到數值分佈於 0~1 之間 (Max={val_max:.2f})，自動切換範圍為 [0.0, 1.0]")
            current_vmin, current_vmax = 0.0, 1.0
        else:
            # 否則維持使用傳入的 depth_range (或根據數據動態調整)
            # 這裡維持依照外部設定，若外部設定範圍不合，可考慮用 val_max 動態覆蓋
            pass 

        # 3. 轉熱力圖 (Jet)
        # 正規化
        norm = np.clip((intensity - current_vmin) / (current_vmax - current_vmin), 0, 1)
        cmap = plt.get_cmap("jet")
        return cmap(norm)[:, :3]

    # --- 1. 檔案讀取 ---
    ext = os.path.splitext(cloud_file)[1].lower()
    temp_file = f"temp_{uuid.uuid4().hex}{ext}"
    
    xyz = None
    colors = None

    try:
        shutil.copyfile(cloud_file, temp_file)

        # A. NPZ
        if ext == '.npz':
            with np.load(temp_file) as f:
                key = 'data' if 'data' in f else list(f.keys())[0]
                data = f[key]
                xyz = data[:, 0:3]
                colors = get_heatmap_colors(data, depth_range)

        # B. H5
        elif ext == '.h5':
            with h5py.File(temp_file, 'r') as hf:
                key = 'data' if 'data' in hf else list(hf.keys())[0]
                data = np.array(hf[key])
                xyz = data[:, 0:3]
                colors = get_heatmap_colors(data, depth_range)

        # C. 標準點雲 (.ply, .pcd)
        else:
            pcd_temp = o3d.io.read_point_cloud(temp_file)
            if not pcd_temp.is_empty():
                xyz = np.asarray(pcd_temp.points)
                # 標準檔案若無額外 Channel，很難畫熱力圖，這裡暫時給黑
                # 若 PLY 裡有強度資訊，Open3D 讀取需透過 tensor API，這裡簡化處理
                print(">> 標準檔案 (.ply/.pcd)，預設黑色")
                colors = np.zeros((len(xyz), 3))
            else:
                raise ValueError("點雲檔案為空")

    except Exception as e:
        print(f"讀取錯誤: {e}")
        if os.path.exists(temp_file): os.remove(temp_file)
        return
    finally:
        if os.path.exists(temp_file): os.remove(temp_file)

    # --- 2. Open3D 建模 ---
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(xyz)
    if colors is not None:
        pcd.colors = o3d.utility.Vector3dVector(colors)

    bounding_box = pcd.get_axis_aligned_bounding_box()
    camera_center = bounding_box.get_center()

    vis = o3d.visualization.Visualizer()
    vis.create_window(width=image_width, height=image_height, visible=False)
    vis.add_geometry(pcd)

    opt = vis.get_render_option()
    opt.background_color = np.asarray([255, 255, 255]) # 白底
    opt.point_size = 10.0 # 大點
    opt.light_on = False

    # --- 3. 相機視角 ---
    view_control = vis.get_view_control()
    rx, ry, rz = np.radians(camera_angles)
    
    Rz = np.array([[np.cos(rz), -np.sin(rz), 0], [np.sin(rz), np.cos(rz), 0], [0, 0, 1]])
    Ry = np.array([[np.cos(ry), 0, np.sin(ry)], [0, 1, 0], [-np.sin(ry), 0, np.cos(ry)]])
    Rx = np.array([[1, 0, 0], [0, np.cos(rx), -np.sin(rx)], [0, np.sin(rx), np.cos(rx)]])
    R = Rz @ Ry @ Rx

    camera_direction = R @ np.array([0, 0, -1])
    camera_up = R @ np.array([0, 1, 0])

    view_control.set_lookat(camera_center)
    view_control.set_up(camera_up)
    view_control.set_front(camera_direction)

    if radius is not None:
        view_control.set_zoom(0.7)

    # --- 4. 存檔 ---
    vis.poll_events()
    vis.update_renderer()
    image = vis.capture_screen_float_buffer(do_render=True)
    vis.destroy_window()

    try:
        output_dir = os.path.dirname(output_png)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        plt.imsave(output_png, np.asarray(image))
        print(f"圖片已保存: {output_png}")
    except Exception as e:
        print(f"存檔失敗: {e}")