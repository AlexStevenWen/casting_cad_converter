import open3d as o3d
import numpy as np
import h5py
import os
import glob
import itertools
from sklearn.cluster import DBSCAN 
from scipy.spatial import cKDTree
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra 

# ==========================================================
# [Helper 1] 能夠 "保留原始維度" 的載入器
# ==========================================================
def load_data_preserve_dimensions(path):
    """
    讀取檔案，回傳:
    1. pcd: 用於幾何計算 (Open3D物件)
    2. raw_matrix: 原始數據矩陣 (N, D)，保留所有舊特徵
    """
    pcd = o3d.geometry.PointCloud()
    raw_matrix = None
    
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext == '.npz':
            with np.load(path) as f:
                # 自動抓取 'data' 或第一個 key
                key = 'data' if 'data' in f else list(f.keys())[0]
                raw_matrix = f[key] # (N, D)
                
                # 建立 PCD 用於幾何計算 (取前3欄 XYZ)
                pcd.points = o3d.utility.Vector3dVector(raw_matrix[:, 0:3])
                # 如果有 Normal (通常在 3:6)
                if raw_matrix.shape[1] >= 6:
                    pcd.normals = o3d.utility.Vector3dVector(raw_matrix[:, 3:6])
        
        elif ext in ['.pcd', '.ply']:
            pcd = o3d.io.read_point_cloud(path)
            points = np.asarray(pcd.points)
            normals = np.asarray(pcd.normals)
            if len(normals) == 0: normals = np.zeros_like(points)
            raw_matrix = np.hstack([points, normals]) # (N, 6)

        # 確保法向量存在 (計算接觸需要)
        if not pcd.has_normals():
            pcd.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=5.0, max_nn=30))
            
        return pcd, raw_matrix
        
    except Exception as e:
        print(f"Load Error {path}: {e}")
        return None, None

# ==========================================================
# [Helper 2] 計算梯度向量 (流速 Velocity)
# ==========================================================
def compute_gradient_vector(points, scalar_field, k=20):
    """ (N,3) XYZ + (N,1) Dist -> (N,3) Velocity """
    tree = cKDTree(points)
    _, indices = tree.query(points, k=k)
    
    neighbors = points[indices]
    vals_n = scalar_field[indices]
    vals_c = scalar_field[:, None]
    
    diff_val = vals_n - vals_c
    diff_pos = neighbors - points[:, None, :]
    dist = np.linalg.norm(diff_pos, axis=2, keepdims=True)
    dist[dist == 0] = 1.0 
    
    dirs = diff_pos / dist
    raw_grad = np.sum(diff_val[:, :, None] * dirs, axis=1)
    
    norms = np.linalg.norm(raw_grad, axis=1, keepdims=True)
    norms[norms < 1e-6] = 1.0
    return raw_grad / norms

# ==========================================================
# [Core Logic] 物理場計算核心 (原子操作)
# 這裡只負責算 "單一" 特徵，可以無限擴充 elif
# ==========================================================
def compute_single_field_value(points_np, contact_indices, mode, intensity_radius=5.0):
    """
    輸入: 點雲座標, 接觸點索引, 模式
    輸出: (N, ) 單一維度陣列
    """
    num_points = len(points_np)
    values = np.zeros(num_points, dtype=np.float32)
    
    if not contact_indices:
        return values
        
    indices_array = np.array(list(contact_indices))
    
    # -----------------------------------------------------------
    # 群組 A: 歐幾里得距離類 (適用 Gate Probability)
    # -----------------------------------------------------------
    if mode in ['gate_probability', 'gaussian', 'binary', 'intensity']:
        contact_points = points_np[indices_array]
        
        # DBSCAN 聚類
        clustering = DBSCAN(eps=intensity_radius, min_samples=3).fit(contact_points)
        labels = clustering.labels_
        unique_labels = set(labels)
        centroids = []
        for label in unique_labels:
            if label == -1: continue
            centroids.append(np.mean(contact_points[labels == label], axis=0))
            
        if not centroids:
            values[indices_array] = 1.0
            return values
            
        tree = cKDTree(np.array(centroids))
        dists_all, _ = tree.query(points_np)
        
        if mode == 'binary':
            values[indices_array] = 1.0
        else: # gaussian / gate_probability
            sigma = intensity_radius / 3.0
            values = np.exp(- (dists_all**2) / (2 * (sigma**2)))
            values[dists_all > intensity_radius] = 0.
            
        return values

    # -----------------------------------------------------------
    # 群組 B: 測地線距離類 (適用 Flow / Thermal)
    # -----------------------------------------------------------
    elif mode in ['flow_geodesic', 'thermal_geodesic']:
        # 1. 建圖
        k = 15
        tree = cKDTree(points_np)
        dists_k, indices_k = tree.query(points_np, k=k)
        row = np.repeat(np.arange(num_points), k)
        col = indices_k.flatten()
        data = dists_k.flatten()
        graph = csr_matrix((data, (row, col)), shape=(num_points, num_points))
        
        # 2. Dijkstra
        geo_dists = dijkstra(csgraph=graph, directed=False, indices=indices_array, min_only=True)
        
        # 3. 處理無限大
        valid_mask = ~np.isinf(geo_dists)
        if not np.any(valid_mask): return values
        max_dist = np.max(geo_dists[valid_mask])
        if max_dist == 0: max_dist = 1.0
        
        if mode == 'flow_geodesic':
            geo_dists[~valid_mask] = max_dist
            return geo_dists / max_dist # 歸一化 0~1
            
        elif mode == 'thermal_geodesic':
            sigma = max_dist / 3.0
            vals = np.exp(- (geo_dists**2) / (2 * (sigma**2)))
            vals[~valid_mask] = 0.0
            vals[indices_array] = 1.0
            return vals

    else:
        print(f"[Warning] Unknown mode: {mode}")
        return values

# ==========================================================
# [Main Process] 單次遍歷 + 陣列合併
# ==========================================================
def process_assembly_data_gen_single_pass(
        input_dir, 
        output_dir, 
        contact_threshold=1.0, 
        target_modes=None  # 傳入陣列 ['gate', 'flow', ...]
    ):
    
    if target_modes is None:
        target_modes = ['gate_probability'] # 預設只跑一個
        
    print(f"--- 啟動單次遍歷流水線 ---")
    print(f"目標模式陣列: {target_modes}")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. 搜尋檔案
    files = glob.glob(os.path.join(input_dir, "**", "*.npz"), recursive=True)
    if len(files) < 2: return

    # 2. 建立快取 (一次載入，不做重複 I/O)
    print("載入並保留原始維度...")
    dataset_cache = {}
    for path in files:
        # 使用自製的載入器，確保 raw_data 被完整保留
        pcd, raw_data = load_data_preserve_dimensions(path)
        if pcd:
            key = os.path.relpath(path, input_dir)
            dataset_cache[key] = {
                "pcd": pcd,
                "raw_data": raw_data, # 這裡可能已經有 N個特徵
                "indices": set(),     # 這是接觸點
                "fname": os.path.basename(path)
            }

    # 3. 接觸分析 (全域做一次)
    print("分析接觸關係...")
    keys = list(dataset_cache.keys())
    for ka, kb in itertools.combinations(keys, 2):
        da, db = dataset_cache[ka], dataset_cache[kb]
        dists = da["pcd"].compute_point_cloud_distance(db["pcd"])
        idxs = np.where(np.asarray(dists) < contact_threshold)[0]
        if idxs.size > 0:
            da["indices"].update(idxs)
            db["indices"].update(idxs) # 雙向接觸

    # 4. 核心運算迴圈 (In-Memory Processing)
    print("計算物理場並堆疊陣列...")
    
    for key, item in dataset_cache.items():
        pcd = item["pcd"]
        indices = item["indices"]
        raw_data = item["raw_data"] # (N, D_old)
        points_np = np.asarray(pcd.points)
        
        # 用來存放新產生的特徵 (List of Arrays)
        new_features_stack = []
        
        # 暫存流場距離，為了算速度
        temp_flow_dist = None
        
        # --- A. 遍歷 target_modes 陣列 (而不是檔案迴圈) ---
        for mode in target_modes:
            # 呼叫原子函式計算
            val = compute_single_field_value(points_np, indices, mode, contact_threshold*5.0)
            
            # Reshape 成 (N, 1) 並加入堆疊
            new_features_stack.append(val.reshape(-1, 1))
            
            # 如果是流場，存起來給 Velocity 用
            if mode == 'flow_geodesic':
                temp_flow_dist = val
        
        # --- B. 自動衍生 Velocity (如果剛剛有算 Flow) ---
        if temp_flow_dist is not None:
            # 計算梯度 (N, 3)
            velocity_vec = compute_gradient_vector(points_np, temp_flow_dist)
            new_features_stack.append(velocity_vec)
        else:
            # 如果沒要求算流場，補個全零向量保持格式一致 (看需求)
            # new_features_stack.append(np.zeros((len(points_np), 3))) 
            pass

        # --- C. 最終合併 (Stacking) ---
        # 原始資料 (N, D) + 新特徵1 (N,1) + 新特徵2 (N,1) ...
        
        if new_features_stack:
            new_block = np.hstack(new_features_stack).astype(np.float32)
            final_data = np.hstack([raw_data, new_block])
        else:
            final_data = raw_data

        # --- D. 單次存檔 ---
        out_path = os.path.join(output_dir, item["fname"])
        np.savez_compressed(out_path, data=final_data)
        
        # Debug info
        # print(f"Saved {item['fname']} | Shape: {final_data.shape}")

    print(f"處理完成，輸出目錄: {output_dir}")

# ==========================================================
# == 使用範例 ==
# ==========================================================
if __name__ == "__main__":
    
    # 假設 input 資料夾內的 .npz 已經包含了 Stage 1 的特徵 (XYZ, Norm, SDF...)
    INPUT_FOLDER = "./stage1_output" 
    OUTPUT_FOLDER = "./stage2_ready_data"
    
    # 【關鍵配置】: 根據陣列執行運算，而非寫死在迴圈
    # 順序決定了最後 Tensor 的通道順序
    # Velocity (3通道) 會自動附加在 Flow 的後面
    MY_MODES = [
        "gate_probability",  # Feature A
        "flow_geodesic",     # Feature B (+ Velocity C)
        "thermal_geodesic"   # Feature D
    ]
    
    process_assembly_data_gen_single_pass(
        input_dir=INPUT_FOLDER,
        output_dir=OUTPUT_FOLDER,
        contact_threshold=0.5,
        target_modes=MY_MODES
    )
    
    # 驗證結果
    sample = glob.glob(os.path.join(OUTPUT_FOLDER, "*.npz"))
    if sample:
        d = np.load(sample[0])['data']
        print(f"\n[驗證] 檔案: {os.path.basename(sample[0])}")
        print(f"最終形狀: {d.shape}")
        print(f"說明: 包含原始輸入的所有欄位 + {len(MY_MODES)}個純量場 + 1個向量場(若有Flow)")