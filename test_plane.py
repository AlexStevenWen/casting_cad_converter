import open3d as o3d
import numpy as np
import copy # 用於複製點雲

def find_contact_labels(pcd_a_path, pcd_b_path, contact_threshold, needs_registration=False):
    """
    載入兩個點雲，（可選）對齊它們，並找出接觸點的標籤。
    (此函式本身功能正確)
    """

    # 1. 載入點雲
    pcd_a = o3d.io.read_point_cloud(pcd_a_path)
    pcd_b = o3d.io.read_point_cloud(pcd_b_path)
    
    pcd_a_colored = copy.deepcopy(pcd_a)
    pcd_b_colored = copy.deepcopy(pcd_b)

    # 2. 點雲對齊 (如果需要)
    if needs_registration:
        print("正在執行 ICP 對齊...")
        trans_init = np.identity(4) 
        reg_p2p = o3d.pipelines.registration.registration_icp(
            pcd_a, pcd_b, contact_threshold * 5, trans_init,
            o3d.pipelines.registration.TransformationEstimationPointToPoint(),
            o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=2000))
        pcd_a.transform(reg_p2p.transformation)
        pcd_a_colored.transform(reg_p2p.transformation)
        print("對齊完成。")

    # 3. 鄰近距離計算
    dists_a_to_b = pcd_a.compute_point_cloud_distance(pcd_b)
    dists_a_to_b = np.asarray(dists_a_to_b)
    
    dists_b_to_a = pcd_b.compute_point_cloud_distance(pcd_a)
    dists_b_to_a = np.asarray(dists_b_to_a)

    # 4. 閾值篩選與標記
    contact_indices_a = np.where(dists_a_to_b < contact_threshold)[0]
    contact_indices_b = np.where(dists_b_to_a < contact_threshold)[0]

    labels_a = np.zeros(len(pcd_a.points), dtype=np.int32)
    labels_a[contact_indices_a] = 1

    labels_b = np.zeros(len(pcd_b.points), dtype=np.int32)
    labels_b[contact_indices_b] = 1

    print(f"點雲 A 中找到 {len(contact_indices_a)} / {len(pcd_a.points)} 個接觸點。")
    print(f"點雲 B 中找到 {len(contact_indices_b)} / {len(pcd_b.points)} 個接觸點。")

    # 5. 視覺化
    pcd_a_colored.paint_uniform_color([0.7, 0.7, 0.7]) 
    pcd_b_colored.paint_uniform_color([0.7, 0.7, 0.7])

    colors_a = np.asarray(pcd_a_colored.colors)
    colors_b = np.asarray(pcd_b_colored.colors)

    colors_a[contact_indices_a] = [1, 0, 0] # A 接觸點為紅色
    colors_b[contact_indices_b] = [0, 1, 0] # B 接觸點為綠色

    pcd_a_colored.colors = o3d.utility.Vector3dVector(colors_a)
    pcd_b_colored.colors = o3d.utility.Vector3dVector(colors_b)

    return labels_a, labels_b, pcd_a_colored, pcd_b_colored

# --- 使用範例 ---
# ==========================================================
# == (V6) 兩個立方體範例資料 - 保證重疊 ==
# ==========================================================

# 1. 建立一個 "底座" 長方體 (pcd_a)
# 建立 2x2x0.5 的盒子網格
mesh_a = o3d.geometry.TriangleMesh.create_box(width=2.0, height=2.0, depth=0.5)
# 將它平移，使其中心在 (0,0,0.25)，頂部表面在 Z=0.5
mesh_a.translate([-1.0, -1.0, 0.0]) # Z 軸區間: [0.0, 0.5]
pcd_a = mesh_a.sample_points_uniformly(number_of_points=3000)
o3d.io.write_point_cloud("cube_a_v6.pcd", pcd_a)


# 2. 建立一個 "接觸" 立方體 (pcd_b)
# 建立 1x1x1 的盒子網格
mesh_b = o3d.geometry.TriangleMesh.create_box(width=1.0, height=1.0, depth=1.0)

# ==========================================================
# == !! 關鍵修改在此 (V7) !! ==
# 將它平移，使其底部在 Z=0.5
# 這將使其與 A 的頂部 (Z=0.5) "完美接觸" (距離為 0)
mesh_b.translate([-0.5, -0.5, 0.5]) # Z 軸區間: [0.5, 1.5]
# ==========================================================
# ==========================================================

pcd_b = mesh_b.sample_points_uniformly(number_of_points=2000)
o3d.io.write_point_cloud("cube_b_v6.pcd", pcd_b)


# ==========================================================
# == 執行函式 ==
# ==========================================================

labels_a, labels_b, pcd_a_viz, pcd_b_viz = find_contact_labels(
    pcd_a_path="cube_a_v6.pcd", # 使用 V6 檔案
    pcd_b_path="cube_b_v6.pcd", # 使用 V6 檔案
    contact_threshold=0.1,  # 閾值 (遠小於穿插深度 0.05)
    needs_registration=False 
)

# 視覺化顯示
print("\n顯示視覺化結果... (A 接觸點為紅, B 接觸點為綠)")
o3d.visualization.draw_geometries([pcd_a_viz, pcd_b_viz])