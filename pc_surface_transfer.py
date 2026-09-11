import numpy as np
import os
from scipy.spatial import cKDTree
from tqdm import tqdm
import open3d as o3d  # 引入 Open3D 用於 ICP
class PointCloudLabelTransfer:
    def __init__(self, method='normalized_knn'):
        """
        :param method: 
            'knn'            - 原始距離 (適合僅平滑/加噪，無縮放)
            'spherical'      - 球面投影 (僅適合簡單凸物體，有重疊風險)
            'normalized_knn' - [推薦] 歸一化空間 (抗縮放、抗非凸、抗變形)
            'icp_knn'        - [最強] 自動配準 (抗旋轉、抗位移、抗縮放)
        """
        self.method = method

    def _normalize_coords(self, points):
        """
        [核心改良] 將點雲縮放到單位尺度 (Unit Scale)，但保留 3D 幾何結構。
        這比球面投影好，因為不會把凹陷處的點疊在一起。
        """
        # 1. 去中心化
        centroid = np.mean(points, axis=0)
        centered = points - centroid
        
        # 2. 計算最大半徑 (Scale Factor)
        # 這裡使用「最遠點距離」作為縮放基準
        max_dist = np.max(np.linalg.norm(centered, axis=1))
        
        if max_dist == 0: max_dist = 1.0
        
        # 3. 縮放至 0~1 範圍
        normalized = centered / max_dist
        
        return normalized

    def _apply_icp(self, source_points, target_points):
        """
        使用 ICP (Iterative Closest Point) 將 Source 對齊到 Target。
        解決擴增過程中可能的微小旋轉或位移。
        """
        src_pcd = o3d.geometry.PointCloud()
        src_pcd.points = o3d.utility.Vector3dVector(source_points)
        
        tgt_pcd = o3d.geometry.PointCloud()
        tgt_pcd.points = o3d.utility.Vector3dVector(target_points)
        
        # 初始猜測 (Identity)
        trans_init = np.identity(4)
        
        # 執行 ICP (Point-to-Point)
        # threshold 設為 bounding box 的 0.05 倍左右
        bbox = tgt_pcd.get_axis_aligned_bounding_box()
        threshold = bbox.get_max_extent() * 0.05
        
        reg_p2p = o3d.pipelines.registration.registration_icp(
            src_pcd, tgt_pcd, threshold, trans_init,
            o3d.pipelines.registration.TransformationEstimationPointToPoint(),
            o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=30)
        )
        
        # 將 Source 變換到 Target 的位置
        src_pcd.transform(reg_p2p.transformation)
        
        return np.asarray(src_pcd.points)

    def transfer(self, source_points, source_labels, target_points, k=3):
        """
        執行轉移
        """
        ref_features = None
        query_features = None

        # --- 策略選擇 ---
        if self.method == 'spherical':
            # 球面模式 (有重疊風險)
            # print("   [Mode] Spherical")
            ref_features = self._to_spherical_coords(source_points)
            query_features = self._to_spherical_coords(target_points)
            
        elif self.method == 'normalized_knn':
            # [推薦] 歸一化 k-NN (保留幾何，抗縮放)
            # print("   [Mode] Normalized k-NN")
            ref_features = self._normalize_coords(source_points)
            query_features = self._normalize_coords(target_points)
            
        elif self.method == 'icp_knn':
            # [最強] ICP 自動對齊 (直接移動 Source 去貼合 Target)
            # print("   [Mode] ICP alignment")
            # 這裡我們不改變特徵空間，而是直接把 Source 搬過去
            ref_features = self._apply_icp(source_points, target_points)
            query_features = target_points # Target 不動
            
        else:
            # 原始 k-NN
            # print("   [Mode] Standard k-NN")
            ref_features = source_points
            query_features = target_points

        # --- 以下邏輯不變 (KDTree 查詢) ---
        tree = cKDTree(ref_features)
        dists, indices = tree.query(query_features, k=k)

        if k == 1:
            target_labels = source_labels[indices]
        else:
            epsilon = 1e-6
            weights = 1.0 / (dists + epsilon)
            if weights.ndim == 1: weights = weights[:, np.newaxis]
            total_weight = np.sum(weights, axis=1, keepdims=True)
            weights /= total_weight
            neighbor_labels = source_labels[indices]
            target_labels = np.sum(weights * neighbor_labels, axis=1)

        return target_labels

    # (保留原有的 _to_spherical_coords 供相容)
    def _to_spherical_coords(self, points):
        centroid = np.mean(points, axis=0)
        centered_points = points - centroid
        norms = np.linalg.norm(centered_points, axis=1, keepdims=True)
        norms[norms == 0] = 1e-6
        return centered_points / norms