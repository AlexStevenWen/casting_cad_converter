import numpy as np
import open3d as o3d
import matplotlib.pyplot as plt
import os
import shutil
import uuid
import h5py

def Render_Hybrid_Cloud_STL_li(
        cloud_file,       # 點雲路徑 (.npz, .h5, .ply, .pcd)
        stl_file,         # STL 模型路徑 (.stl)
        output_png,       # 輸出圖片路徑
        camera_angles,    # [Rx, Ry, Rz] 角度
        image_width,
        image_height,
        radius=None,      # 若 None 則自動縮放
        depth_range=[0, 1], # 點雲強度範圍
        stl_color=[0.7, 0.7, 0.7], # STL 模型的底色 (灰色)
        spotlight_center=None,     # 探照燈中心 (例如: [x, y, z])，若設為 'auto' 則取場景中心
        spotlight_radius=None      # 探照燈半徑 (影響光暈範圍大小)
):
    """
    同時讀取點雲與 STL，將點雲疊加在 STL 上並輸出圖片。
    支援「探照燈模式」，凸顯特定區域並將周圍壓暗。
    """
    
    # -----------------------------
    # 內部函式：熱力圖計算
    # -----------------------------
    def get_heatmap_colors(data_arr, default_range):
        dims = data_arr.shape[1]
        intensity = None
        
        if dims >= 7:
            intensity = data_arr[:, 6]
        elif dims >= 4:
            intensity = data_arr[:, 3]
        else:
            return np.tile([1, 0, 0], (data_arr.shape[0], 1))

        val_min = np.min(intensity)
        val_max = np.max(intensity)
        current_vmin, current_vmax = default_range
        
        if val_max <= 1.0 and val_max > 0 and current_vmax > 1.0:
            current_vmin, current_vmax = 0.0, 1.0

        norm = np.clip((intensity - current_vmin) / (current_vmax - current_vmin), 0, 1)
        cmap = plt.get_cmap("jet")
        return cmap(norm)[:, :3]

    # -----------------------------
    # 內部函式：計算探照燈衰減係數
    # -----------------------------
    def apply_spotlight(points, original_colors, center, radius):
        """ 計算點到中心的距離，並回傳壓暗後的顏色 """
        if center is None or radius is None:
            return original_colors
        
        # 計算每個點到探照燈中心的直線距離
        dists = np.linalg.norm(points - center, axis=1)
        
        # 計算衰減係數 (1.0 代表中心最亮，0.0 代表半徑外最暗)
        # 這裡使用線性衰減，你可以改成 (dists/radius)**2 來做非線性柔和邊緣
        falloff = np.clip(1.0 - (dists / radius), 0.05, 1.0) # 最暗保留 0.05 亮度才不會全黑
        
        return original_colors * falloff[:, np.newaxis]

    # -----------------------------
    # 1. 讀取與處理資料 (無光照原始狀態)
    # -----------------------------
    # [STL 處理]
    mesh = None
    if os.path.exists(stl_file):
        temp_stl = f"temp_stl_{uuid.uuid4().hex}.stl"
        try:
            shutil.copyfile(stl_file, temp_stl)
            mesh = o3d.io.read_triangle_mesh(temp_stl)
            if mesh.has_triangles():
                mesh.compute_vertex_normals()
                mesh_verts = np.asarray(mesh.vertices)
                mesh_colors = np.tile(stl_color, (len(mesh_verts), 1))
            else:
                mesh = None
        except Exception as e:
            print(f"STL 讀取錯誤: {e}")
            mesh = None
        finally:
            if os.path.exists(temp_stl): os.remove(temp_stl)

    # [點雲處理]
    xyz = None
    cloud_colors = None
    if os.path.exists(cloud_file):
        ext = os.path.splitext(cloud_file)[1].lower()
        temp_cloud = f"temp_cloud_{uuid.uuid4().hex}{ext}"
        try:
            shutil.copyfile(cloud_file, temp_cloud)
            if ext == '.npz':
                with np.load(temp_cloud) as f:
                    key = 'data' if 'data' in f else list(f.keys())[0]
                    data = f[key]
                    xyz = data[:, 0:3]
                    cloud_colors = get_heatmap_colors(data, depth_range)
            elif ext == '.h5':
                with h5py.File(temp_cloud, 'r') as hf:
                    key = 'data' if 'data' in hf else list(hf.keys())[0]
                    data = np.array(hf[key])
                    xyz = data[:, 0:3]
                    cloud_colors = get_heatmap_colors(data, depth_range)
            else:
                pcd_temp = o3d.io.read_point_cloud(temp_cloud)
                if not pcd_temp.is_empty():
                    xyz = np.asarray(pcd_temp.points)
                    cloud_colors = np.tile([0, 0, 1], (len(xyz), 1))
        except Exception as e:
            print(f"點雲讀取錯誤: {e}")
        finally:
            if os.path.exists(temp_cloud): os.remove(temp_cloud)

    # -----------------------------
    # 2. 自動決定探照燈中心
    # -----------------------------
    # 取得場景 Bounding Box 以計算中心
    geometry_list = []
    temp_geometries = []
    if mesh is not None: temp_geometries.append(mesh)
    if xyz is not None: 
        tmp_pcd = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(xyz))
        temp_geometries.append(tmp_pcd)

    if temp_geometries:
        min_bound = np.min([g.get_min_bound() for g in temp_geometries], axis=0)
        max_bound = np.max([g.get_max_bound() for g in temp_geometries], axis=0)
        center_box = o3d.geometry.AxisAlignedBoundingBox(min_bound, max_bound)
        scene_center = center_box.get_center()
    else:
        print("沒有有效的幾何資料可供渲染。")
        return

    # 若設定為 auto，則把光打在模型正中心
    if spotlight_center == 'auto':
        spotlight_center = scene_center

    # -----------------------------
    # 3. 應用探照燈效果 (顏色衰減) 並建立 Open3D 物件
    # -----------------------------
    vis = o3d.visualization.Visualizer()
    vis.create_window(width=image_width, height=image_height, visible=False)

    # 加入 STL (應用探照燈)
    if mesh is not None:
        final_mesh_colors = apply_spotlight(mesh_verts, mesh_colors, spotlight_center, spotlight_radius)
        mesh.vertex_colors = o3d.utility.Vector3dVector(final_mesh_colors)
        vis.add_geometry(mesh)
        geometry_list.append(mesh)

    # 加入 點雲 (應用探照燈)
    if xyz is not None:
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(xyz)
        
        final_cloud_colors = apply_spotlight(xyz, cloud_colors, spotlight_center, spotlight_radius)
        pcd.colors = o3d.utility.Vector3dVector(final_cloud_colors)
        
        vis.add_geometry(pcd)
        geometry_list.append(pcd)

    # -----------------------------
    # 4. 相機視角控制
    # -----------------------------
    vis.poll_events()
    vis.update_renderer()
    view_control = vis.get_view_control()

    rx, ry, rz = np.radians(camera_angles)
    Rz = np.array([[np.cos(rz), -np.sin(rz), 0], [np.sin(rz), np.cos(rz), 0], [0, 0, 1]])
    Ry = np.array([[np.cos(ry), 0, np.sin(ry)], [0, 1, 0], [-np.sin(ry), 0, np.cos(ry)]])
    Rx = np.array([[1, 0, 0], [0, np.cos(rx), -np.sin(rx)], [0, np.sin(rx), np.cos(rx)]])
    R = Rz @ Ry @ Rx

    camera_direction = R @ np.array([0, 0, -1])
    camera_up = R @ np.array([0, 1, 0])

    view_control.set_lookat(scene_center)
    view_control.set_up(camera_up)
    view_control.set_front(camera_direction)
    
    if radius is not None:
        view_control.set_zoom(0.7) 
    else:
        view_control.set_zoom(0.8)

    # -----------------------------
    # 5. 渲染設定與存檔
    # -----------------------------
    opt = vis.get_render_option()
    
    # 【關鍵】如果開啟探照燈，建議把背景調成黑色或深灰色，光暈效果才會好
    if spotlight_center is not None:
        opt.background_color = np.asarray([0.05, 0.05, 0.05]) # 深色背景
    else:
        opt.background_color = np.asarray([1, 1, 1]) # 白底
        
    opt.point_size = 20.0      
    opt.light_on = True        

    vis.poll_events()
    vis.update_renderer()
    
    image = vis.capture_screen_float_buffer(do_render=True)
    vis.destroy_window()

    try:
        output_dir = os.path.dirname(output_png)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        image_uint8 = (np.asarray(image) * 255).astype(np.uint8)
        plt.imsave(output_png, image_uint8)
        print(f"合併渲染圖片已保存: {output_png}")
    except Exception as e:
        print(f"存檔失敗: {e}")

# ==========================================
# 測試呼叫範例
# ==========================================
if __name__ == "__main__":
    my_cloud = "data.npz"        
    my_stl = "model.stl"          
    
    output_path = "output_hybrid_spotlight.png"
    angles = [0, 45, 0]           
    width, height = 1024, 1024
    
    # 啟動探照燈模式：
    # spotlight_center='auto' 會自動打在物體正中心。你也可以傳入特定座標如 [10.0, 5.0, 0.0]
    # spotlight_radius=50.0 請依照你實際模型的尺寸大小來設定 (可能需要測試調整數值)
    # Render_Hybrid_Cloud_STL(
    #     my_cloud, my_stl, output_path, angles, width, height, 
    #     depth_range=[0, 255],
    #     spotlight_center='auto',  
    #     spotlight_radius=100.0   
    # )