import numpy as np
import open3d as o3d
import matplotlib.pyplot as plt
import os
import shutil
import uuid
import h5py

def Render_Hybrid_Cloud_STL(
        cloud_file,       # 點雲路徑 (.npz, .h5, .ply, .pcd)
        stl_file,         # STL 模型路徑 (.stl)
        output_png,       # 輸出圖片路徑
        camera_angles,    # [Rx, Ry, Rz] 角度
        image_width,
        image_height,
        radius=None,      # 若 None 則自動縮放
        depth_range=[0, 1], # 點雲強度範圍
        stl_color=[0.7, 0.7, 0.7] # STL 模型的底色 (灰色)
):
    """
    同時讀取點雲與 STL，將點雲疊加在 STL 上並輸出圖片。
    """
    
    # -----------------------------
    # 內部函式：熱力圖計算
    # -----------------------------
    def get_heatmap_colors(data_arr, default_range):
        dims = data_arr.shape[1]
        intensity = None
        
        # 1. 抓取強度值
        if dims >= 7: # XYZ + Normal + I
            print(f">> [點雲] 偵測到 {dims} 維度，取 Index 6 為強度值")
            intensity = data_arr[:, 6]
        elif dims >= 4: # XYZ + I
            print(f">> [點雲] 偵測到 {dims} 維度，取 Index 3 為強度值")
            intensity = data_arr[:, 3]
        else:
            print(f">> [點雲] 維度 {dims} 不足，無法產生熱力圖，顯示紅色以示區別")
            return np.tile([1, 0, 0], (data_arr.shape[0], 1)) # 純紅

        # 2. 數值範圍判斷
        val_min = np.min(intensity)
        val_max = np.max(intensity)
        current_vmin, current_vmax = default_range
        
        # 自動切換 [0,1] 模式
        if val_max <= 1.0 and val_max > 0 and current_vmax > 1.0:
            print(f"   [提示] 偵測到數值分佈於 0~1 (Max={val_max:.2f})，自動切換範圍為 [0.0, 1.0]")
            current_vmin, current_vmax = 0.0, 1.0

        # 3. 轉熱力圖 (Jet)
        norm = np.clip((intensity - current_vmin) / (current_vmax - current_vmin), 0, 1)
        cmap = plt.get_cmap("jet")
        return cmap(norm)[:, :3]

    # -----------------------------
    # 1. 讀取 STL (處理中文路徑)
    # -----------------------------
    if not os.path.exists(stl_file):
        raise FileNotFoundError(f"找不到 STL: {stl_file}")

    temp_stl = f"temp_stl_{uuid.uuid4().hex}.stl"
    mesh = None
    try:
        shutil.copyfile(stl_file, temp_stl)
        mesh = o3d.io.read_triangle_mesh(temp_stl)
        if not mesh.has_triangles():
            print(">> [警告] STL 檔案無效或為空")
            mesh = None
        else:
            mesh.compute_vertex_normals()
            mesh.paint_uniform_color(stl_color) # 設定模型顏色
    except Exception as e:
        print(f"STL 讀取錯誤: {e}")
        mesh = None
    finally:
        if os.path.exists(temp_stl): os.remove(temp_stl)

    # -----------------------------
    # 2. 讀取點雲 (處理中文路徑 + 多格式)
    # -----------------------------
    if not os.path.exists(cloud_file):
        raise FileNotFoundError(f"找不到點雲: {cloud_file}")

    ext = os.path.splitext(cloud_file)[1].lower()
    temp_cloud = f"temp_cloud_{uuid.uuid4().hex}{ext}"
    
    xyz = None
    colors = None
    
    try:
        shutil.copyfile(cloud_file, temp_cloud)

        # A. NPZ
        if ext == '.npz':
            with np.load(temp_cloud) as f:
                key = 'data' if 'data' in f else list(f.keys())[0]
                data = f[key]
                xyz = data[:, 0:3]
                colors = get_heatmap_colors(data, depth_range)
        # B. H5
        elif ext == '.h5':
            with h5py.File(temp_cloud, 'r') as hf:
                key = 'data' if 'data' in hf else list(hf.keys())[0]
                data = np.array(hf[key])
                xyz = data[:, 0:3]
                colors = get_heatmap_colors(data, depth_range)
        # C. 標準點雲
        else:
            pcd_temp = o3d.io.read_point_cloud(temp_cloud)
            if not pcd_temp.is_empty():
                xyz = np.asarray(pcd_temp.points)
                # 這裡假設標準檔沒有強度，給藍色以示區別
                colors = np.tile([0, 0, 1], (len(xyz), 1)) 
            else:
                print(">> [警告] 點雲檔案為空")

    except Exception as e:
        print(f"點雲讀取錯誤: {e}")
    finally:
        if os.path.exists(temp_cloud): os.remove(temp_cloud)

    # -----------------------------
    # 3. 建立 Open3D 物件並合併場景
    # -----------------------------
    vis = o3d.visualization.Visualizer()
    vis.create_window(width=image_width, height=image_height, visible=False)

    geometry_list = []

    # 加入 STL
    if mesh is not None:
        vis.add_geometry(mesh)
        geometry_list.append(mesh)

    # 加入 點雲
    if xyz is not None:
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(xyz)
        if colors is not None:
            pcd.colors = o3d.utility.Vector3dVector(colors)
        vis.add_geometry(pcd)
        geometry_list.append(pcd)

    if not geometry_list:
        print("沒有有效的幾何資料可供渲染。")
        vis.destroy_window()
        return

    # -----------------------------
    # 4. 計算相機視角與中心
    # -----------------------------
    # 計算所有物件的合併 Bounding Box
    min_bound = np.min([g.get_min_bound() for g in geometry_list], axis=0)
    max_bound = np.max([g.get_max_bound() for g in geometry_list], axis=0)
    center_box = o3d.geometry.AxisAlignedBoundingBox(min_bound, max_bound)
    camera_center = center_box.get_center()

    print(f"場景中心: {camera_center}")

    # 視圖控制
    vis.poll_events()
    vis.update_renderer()
    view_control = vis.get_view_control()

    # 旋轉矩陣計算
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
    
    # 縮放設定
    if radius is not None:
        # 如果指定半徑，使用 Zoom 近似控制 (Open3D 的 zoom 邏輯較為抽象)
        view_control.set_zoom(0.7) 
    else:
        view_control.set_zoom(0.8) # 預設自動縮放

    # -----------------------------
    # 5. 渲染設定與存檔
    # -----------------------------
    opt = vis.get_render_option()
    opt.background_color = np.asarray([1, 1, 1]) # 白底
    opt.point_size =20.0       # 點雲大小 (可根據需求調整)
    opt.light_on = True         # 開啟光照讓 STL 有立體感

    vis.poll_events()
    vis.update_renderer()
    
    # 擷取 RGB 畫面
    image = vis.capture_screen_float_buffer(do_render=True)
    vis.destroy_window()

    try:
        output_dir = os.path.dirname(output_png)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # 使用 open() 處理中文路徑存檔
        image_uint8 = (np.asarray(image) * 255).astype(np.uint8)
        plt.imsave(output_png, image_uint8)
        
        print(f"合併渲染圖片已保存: {output_png}")
    except Exception as e:
        print(f"存檔失敗: {e}")

# ==========================================
# 測試呼叫範例
# ==========================================
if __name__ == "__main__":
    # 假設你有這兩個檔案
    my_cloud = "data.npz"         # 內含 XYZ + Intensity
    my_stl = "model.stl"          # STL 模型
    
    # 設定參數
    output_path = "output_hybrid.png"
    angles = [0, 45, 0]           # [Rx, Ry, Rz]
    width, height = 1024, 1024
    
    # 執行 (需要確保檔案存在才能跑)
    # Render_Hybrid_Cloud_STL(my_cloud, my_stl, output_path, angles, width, height, depth_range=[0, 255])