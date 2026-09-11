import numpy as np
import open3d as o3d
import matplotlib.pyplot as plt
import os
import shutil
import uuid

def STL_Depth(
        stl_file,
        output_png,
        camera_angles,
        image_width,
        image_height,
        radius,
        depth_range
):
    # 檢查原始檔案是否存在
    if not os.path.exists(stl_file):
        raise FileNotFoundError(f"找不到 STL 文件: {stl_file}")

    # --- 修正 1: 解決 Open3D 無法讀取中文路徑的問題 ---
    # 方法：將檔案複製一份暫存檔(英文檔名)，讀取後再刪除
    temp_stl = f"temp_{uuid.uuid4().hex}.stl" 
    try:
        shutil.copyfile(stl_file, temp_stl)
        mesh = o3d.io.read_triangle_mesh(temp_stl)
    except Exception as e:
        print(f"讀取 STL 發生錯誤: {e}")
        if os.path.exists(temp_stl):
            os.remove(temp_stl)
        return
    finally:
        # 確保刪除暫存檔
        if os.path.exists(temp_stl):
            os.remove(temp_stl)

    if not mesh.has_triangles():
        raise ValueError("加載的 STL 文件不包含有效的三角形網格。")

    mesh.compute_vertex_normals()

    # 計算 STL 邊界的中心
    bounding_box = mesh.get_axis_aligned_bounding_box()
    camera_center = bounding_box.get_center()

    print(f"STL 邊界中心: {camera_center}")

    # 創建可視化器
    vis = o3d.visualization.Visualizer()
    vis.create_window(width=image_width, height=image_height, visible=False)
    vis.add_geometry(mesh)

    # 獲取視圖控制器
    view_control = vis.get_view_control()

    # 將角度轉換為弧度
    rx, ry, rz = np.radians(camera_angles)

    # 為每個軸創建旋轉矩陣
    Rx = np.array([
        [1, 0, 0],
        [0, np.cos(rx), -np.sin(rx)],
        [0, np.sin(rx), np.cos(rx)]
    ])

    Ry = np.array([
        [np.cos(ry), 0, np.sin(ry)],
        [0, 1, 0],
        [-np.sin(ry), 0, np.cos(ry)]
    ])

    Rz = np.array([
        [np.cos(rz), -np.sin(rz), 0],
        [np.sin(rz), np.cos(rz), 0],
        [0, 0, 1]
    ])

    # 合併旋轉矩陣
    R = Rz @ Ry @ Rx

    # 計算攝像機位置
    camera_direction = R @ np.array([0, 0, -1])  # 默認攝像機朝向負 Z 軸
    camera_pos = np.array(camera_center) - camera_direction * radius

    # 設置攝像機參數
    view_control.set_lookat(camera_center)
    view_control.set_up([0, 1, 0])  # Y 軸向上
    view_control.set_front(camera_direction)

    # 根據半徑設置縮放比例
    view_control.set_zoom(radius / 100.0)

    # 渲染並捕獲深度圖
    vis.poll_events()
    vis.update_renderer()
    depth = vis.capture_depth_float_buffer()
    depth = np.asarray(depth)

    # 關閉可視化器
    vis.destroy_window()

    # 將深度值歸一化到指定範圍
    depth_clipped = np.clip(depth, depth_range[0], depth_range[1])
    depth_normalized = (depth_clipped - depth_range[0]) / (depth_range[1] - depth_range[0])

    # --- 修正 2: 解決 Matplotlib 無法儲存中文路徑的問題 ---
    # 方法：使用 Python 原生的 open() (支援 Unicode) 開啟檔案，再傳給 plt.imsave
    try:
        # 確保輸出資料夾存在
        output_dir = os.path.dirname(output_png)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        with open(output_png, 'wb') as f:
            plt.imsave(f, depth_normalized, cmap='gray')
        print(f"深度圖已成功保存至 {output_png}")
    except Exception as e:
        print(f"儲存圖片失敗: {e}")

# 參數

# depth_cake() :
"""
stl_file = "10712448 assembly.stl"
output_png = "output_depth_map.png"
camera_angles = [0, 45, 0]  # 歐拉角（以度為單位）
image_width = 1024
image_height = 1024
radius = 200  # 鏡頭與中心點的距離
depth_range = [0.1, 1000.0]  # 深度值範圍（歸一化用）

STL_Depth(
    stl_file, output_png, camera_angles,
    image_width, image_height, radius, depth_range
)
"""




#調用方式
"""from PIL import Image

depth_map_image = Image.open("depth_map.png")
depth_map = np.asarray(depth_map_image) / 255.0  # 將像素值還原到 [0, 1]
"""