import open3d as o3d
import numpy as np
import h5py
import os
import glob
import itertools
import csv
from sklearn.cluster import DBSCAN # 用於強度模式的聚類分析
from scipy.spatial import cKDTree
import matplotlib.pyplot as plt

# ==========================================================
# == 核心函式 1：計算接觸強度 (Binary / Intensity) ==
# ==========================================================
def compute_contact_values(pcd, contact_indices, mode='binary', intensity_radius=5.0):
    """
    根據接觸索引計算每個點的接觸值 (第7維度)。
    
    新增模式:
    - 'signed_decay': 中心=1.0, 邊界=0.0, 外部=負值 (線性遞減)
    """
    points_np = np.asarray(pcd.points)
    num_points = len(points_np)
    values = np.zeros(num_points, dtype=np.float32)
    
    # 若完全無接觸，且模式是 signed_decay，則全體設為一個大的負值 (代表離接觸很遠)
    if not contact_indices:
        if mode == 'signed_decay':
            values[:] = -1.0 # 或其他負底限
        return values
        
    indices_array = np.array(list(contact_indices))
    
    # --- 模式 A: Binary (0 或 1) ---
    if mode == 'binary':
        values[indices_array] = 1.0
        return values
    
    # --- 模式 B & C: 需要聚類分析中心點 ---
    # 1. 取得接觸點
    contact_points = points_np[indices_array]
    
    # 2. DBSCAN 聚類 (找出多個接觸區)
    clustering = DBSCAN(eps=intensity_radius, min_samples=3).fit(contact_points)
    labels = clustering.labels_
    unique_labels = set(labels)
    
    # 收集所有接觸簇的中心點 (Centroids)
    centroids = []
    for label in unique_labels:
        if label == -1: continue
        cluster_pts = contact_points[labels == label]
        centroids.append(np.mean(cluster_pts, axis=0))
    
    if not centroids:
        return values
    
    centroids = np.array(centroids)

    # --- 模式 B: Intensity (0 ~ 1, 只計算接觸點內部) ---
    if mode == 'intensity':
        # 建立 KDTree 以快速查找最近的中心
        tree = cKDTree(centroids)
        
        # 只計算「接觸點」到「最近中心」的距離
        dists, _ = tree.query(contact_points)
        
        # 線性遞減: 1.0 -> 0.0
        # 這裡假設 intensity_radius 是最大影響範圍
        intensities = 1.0 - (dists / intensity_radius)
        intensities = np.clip(intensities, 0, 1) # 確保不小於 0
        
        values[indices_array] = intensities
        return values

    # --- 模式 C: Signed Decay (1.0 -> 0.0 -> 負值, 計算全域點) ---
    elif mode == 'signed_decay':
        # 這是您要的第三種模式
        # 我們必須計算 "所有點" (而不僅是接觸點) 到 "最近接觸中心" 的距離
        
        tree = cKDTree(centroids)
        
        # 對整顆點雲所有點進行查詢 (注意：這裡運算量會稍大，但 KDTree 很快)
        dists_all, _ = tree.query(points_np)
        
        # 公式： Val = 1.0 - (距離 / 半徑)
        # 距離 = 0 (中心) -> Val = 1.0
        # 距離 = 半徑 (邊界) -> Val = 0.0
        # 距離 > 半徑 (外部) -> Val = 負數
        values = 1.0 - (dists_all / intensity_radius)
        
        # 選項：是否要限制負值的下限？ (例如最低 -10，避免數值過大影響梯度)
        # values = np.clip(values, -10.0, 1.0) 
        return values
    elif mode == 'clamped_decay':
        # 這是您要的第四種模式
        tree = cKDTree(centroids)
        
        # 1. 計算全域點到最近中心的距離
        dists_all, _ = tree.query(points_np)
        
        # 2. 計算線性遞減
        decay_values = 1.0 - (dists_all / intensity_radius)
        
        # 3. 關鍵步驟：直接截斷在 0 到 1 之間
        # 大於半徑的點 (原本會是負數) 全部變成 0
        values = np.clip(decay_values, 0.0, 1.0)
        return values
    # --- 模式 E: Gaussian Decay (高斯分布 0~1, 最適合 Heatmap 回歸) ---
    elif mode == 'gaussian':
        tree = cKDTree(centroids)
        
        # 1. 計算全域距離
        dists_all, _ = tree.query(points_np)
        
        # 2. 定義高斯分布的 "寬度" (Sigma)
        # 我們讓 intensity_radius 等於 3 倍標準差 (3 sigma)
        # 這樣在 radius 處，數值會自然衰減到約 0.01 (接近 0)
        sigma = intensity_radius / 3.0
        
        # 3. 高斯公式: exp( -dist^2 / (2 * sigma^2) )
        values = np.exp(- (dists_all**2) / (2 * (sigma**2)))
        
        # 4. (選用) 硬閥值截斷: 強制半徑以外歸零
        # 雖然高斯在遠處本來就很小，但在工程上強制設為 0 可以減少雜訊
        values[dists_all > intensity_radius] = 0.
        
        return values
    elif mode == 'region_gaussian':
        # 關鍵差異 1: 我們不計算 centroids，而是直接使用所有 "接觸點" 作為參考源
        # 這樣做會計算 "點到集合(Set)的距離"，而不是 "點到中心(Point)的距離"
        
        # 為了效率，先確保 contact_points 已經過 DBSCAN 過濾掉雜訊 (Label != -1)
        valid_mask = labels != -1
        clean_contact_points = contact_points[valid_mask]

        if len(clean_contact_points) == 0:
             return values # 如果沒有有效點，回傳全黑
        
        # 建立 KDTree (包含所有接觸點)
        tree = cKDTree(clean_contact_points)
        
        # 1. 計算全域點到 "最近接觸點" 的距離
        # 如果點本身就在接觸區內，距離會是 0
        dists_all, _ = tree.query(points_np)
        
        # 2. 定義高斯分布參數
        sigma = intensity_radius / 3.0
        
        # 3. 高斯公式
        values = np.exp(- (dists_all**2) / (2 * (sigma**2)))
        
        # 4. 強制截斷 (選用)
        values[dists_all > intensity_radius] = 0.0
        
        # 5. 保險措施：強制把原本標記為接觸區的點設為 1.0
        # (因為浮點數運算可能會有微小誤差，這樣做最穩)
        values[indices_array] = 1.0
        
        return values
    elif mode == 'controlled_gaussian':
        # --- 設定參數 ---
        # 這裡定義：在「澆口半徑邊緣 (R)」那個圈圈上，強度要是多少？
        # 0.35 代表邊界處保留 35% 強度，並從這裡繼續往外衰減
        edge_threshold = 0.35 
        
        # 建立 KDTree (以質心為準)
        tree = cKDTree(centroids)
        
        # 1. 計算全域距離 (算所有點，不管有沒有超過半徑)
        dists_all, _ = tree.query(points_np)

        # 2. 根據「澆口半徑」反推 Sigma
        # R = intensity_radius
        # T = edge_threshold
        target_threshold = np.clip(edge_threshold, 1e-6, 0.999)
        
        # 公式: sigma = R / sqrt(-2 * ln(T))
        # 這行數學保證了：當距離等於 R 時，數值剛好等於 edge_threshold
        sigma = intensity_radius / np.sqrt(-2 * np.log(target_threshold))
        
        # 3. 計算高斯分布 (Apply to ALL points)
        values = np.exp(- (dists_all**2) / (2 * (sigma**2)))
        
        # 4. 【關鍵修改】：
        # 請確保這裡 "沒有" 寫 values[dists_all > intensity_radius] = 0
        # 只要不寫這一行，數值就會自然地擴散到澆口外
        
        # 5. 只過濾極小值 (保持運算乾淨，只有遠到接近 0 的才切掉)
        values[values < 1e-5] = 0.0
        
        return values
    elif mode == 'global_gaussian':
        tree = cKDTree(centroids) 
        
        # 1. 計算全域距離 (每個點到最近澆口的距離)
        dists_all, _ = tree.query(points_np)
        
        # 2. 【關鍵修改】找出這個工件中，離澆口「最遠的距離」
        max_dist = np.max(dists_all)
        
        if max_dist == 0:
             return values # 避免除以零錯誤
        
        # 3. 反推 Sigma
        # 我們希望在距離 = max_dist 的地方，數值剛好衰減到接近 0
        # 根據高斯常態分佈規則 (3-Sigma Rule):
        # 1 sigma 處 = 0.60
        # 2 sigma 處 = 0.13
        # 3 sigma 處 = 0.01 (1%) -> 視覺上的 0
        # 4 sigma 處 = 0.0003   -> 極致的 0
        
        # 這裡設定 3.0，讓最遠點剩下 1% 的熱度 (自然的收尾)
        # 如果你想要「絕對死黑」，可以改成 4.0
        sigma = max_dist / 3.0  
        
        # 4. 高斯公式
        values = np.exp(- (dists_all**2) / (2 * (sigma**2)))
        
        # 5. (選用) 歸一化：強迫拉伸到 0~1
        # 如果你非常堅持最遠點必須是「數學上的 0.000000」
        # 可以加上下面這兩行，把數值強行拉開 (Min-Max Normalization)
        # v_min = np.min(values)
        # v_max = np.max(values)
        # values = (values - v_min) / (v_max - v_min)

        return values
    else:
        print(f"警告：未知的模式 {mode}，回傳全零。")
        return values
    


# ==========================================================
# == 核心函式 2：儲存器 (N, 7) ==
# ==========================================================
def save_contact_dataset(path, points, normals, contact_values):
    """
    將 Points(N,3), Normals(N,3), Contact(N,1) 合併並存檔。
    """
    # 確保形狀正確
    if len(normals) == 0:
        normals = np.zeros_like(points) # 若無補零
        
    contact_col = contact_values.reshape(-1, 1)
    
    # 合併成 (N, 7)
    data_block = np.hstack([points, normals, contact_col]).astype(np.float32)
    
    ext = os.path.splitext(path)[1].lower()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    try:
        if ext == '.npz':
            # 壓縮儲存，key 名稱設為 'data' 或 'point_cloud'
            np.savez_compressed(path, data=data_block)
            
        elif ext == '.h5':
            with h5py.File(path, 'w') as hf:
                hf.create_dataset('data', data=data_block)
                
        elif ext == '.txt' or ext == '.xyz':
            np.savetxt(path, data_block, fmt='%.6f')
            
        else:
            print(f"錯誤：不支援的儲存格式 {ext} (建議使用 .npz 或 .h5)")
            
    except Exception as e:
        print(f"儲存失敗 {path}: {e}")

# ==========================================================
# == (載入器) Load Function ==
# == 專門讀取上述存出的 (N, 7) 格式 ==
# ==========================================================
def load_dataset(path, data_key='data'):
    """
    讀取由 V10 產生的檔案。
    
    返回:
    - numpy array (N, 7): [x, y, z, nx, ny, nz, contact]
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} 不存在")
        
    ext = os.path.splitext(path)[1].lower()
    
    try:
        if ext == '.npz':
            with np.load(path) as f:
                # 自動尋找可能的 key
                key = data_key if data_key in f else list(f.keys())[0]
                return f[key]
                
        elif ext == '.h5':
            with h5py.File(path, 'r') as hf:
                key = data_key if data_key in hf else list(hf.keys())[0]
                return np.array(hf[key])
                
        elif ext == '.npy':
            return np.load(path)
            
        else:
            raise ValueError(f"不支援讀取的格式: {ext}")
            
    except Exception as e:
        print(f"讀取錯誤: {e}")
        return None

# ==========================================================
# == 輔助函式：通用點雲載入 (保留您的 V9 用於讀取原始檔) ==
# ==========================================================
def load_point_cloud_input(path):
    """(V9 精簡版) 用於讀取原始輸入檔案，準備進行分析。"""
    pcd = o3d.geometry.PointCloud()
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext in ['.pcd', '.ply']:
            pcd = o3d.io.read_point_cloud(path)
        elif ext == '.npz':
            data = np.load(path)
            if 'point_cloud' in data:
                pcd.points = o3d.utility.Vector3dVector(data['point_cloud'])
                if 'normals' in data:
                    pcd.normals = o3d.utility.Vector3dVector(data['normals'])
        elif ext == '.h5':
            with h5py.File(path, 'r') as hf:
                if 'point_cloud' in hf:
                    pcd.points = o3d.utility.Vector3dVector(np.array(hf['point_cloud']))
                    if 'normals' in hf:
                        pcd.normals = o3d.utility.Vector3dVector(np.array(hf['normals']))
        
        # 強制計算/確保法向量存在 (因為輸出格式需要)
        if not pcd.has_normals() and not pcd.is_empty():
            pcd.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=5.0, max_nn=30))
            
        return pcd
    except Exception:
        return None

# ==========================================================
# == 主程式：批量分析與資料生成 (V10) ==
# ==========================================================
def process_assembly_data_gen(
        input_dir, 
        output_dir, 
        contact_threshold=1.0, 
        label_mode='binary', # 'binary' 或 'intensity'
        output_format='.npz' # '.npz' 或 '.h5'
    ):
    """
    (V10) 遍歷資料夾，計算接觸，並儲存為 (N, 7) 的訓練用數據。
    """
    print(f"--- 開始執行資料生成 (V10) ---")
    print(f"模式: {label_mode}")
    print(f"輸出格式: {output_format} (N, 7)")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. 搜尋檔案
    input_extensions = ['.pcd', '.ply', '.npz', '.h5']
    pcd_files = []
    for ext in input_extensions:
        pcd_files.extend(glob.glob(os.path.join(input_dir, '**', f"*{ext}"), recursive=True))
    
    if len(pcd_files) < 2:
        print("檔案數量不足，無法進行配對分析。")
        return

    # 2. 載入所有檔案到記憶體
    pcd_data = {} 
    print(f"載入 {len(pcd_files)} 個檔案...")
    for path in pcd_files:
        relative_path = os.path.relpath(path, input_dir)
        key_name = relative_path.replace(os.path.sep, '/') 
        
        pcd = load_point_cloud_input(path)
        if pcd and not pcd.is_empty():
            pcd_data[key_name] = { 
                "path": path, 
                "pcd": pcd, 
                "contact_indices": set() # 用 set 避免重複
            }

    # 3. 兩兩比對，找出接觸點索引
    file_keys = list(pcd_data.keys())
    print(f"進行接觸分析...")
    
    for key_a, key_b in itertools.combinations(file_keys, 2):
        data_a = pcd_data[key_a]
        data_b = pcd_data[key_b]

        # 計算距離
        dists_a = data_a["pcd"].compute_point_cloud_distance(data_b["pcd"])
        dists_b = data_b["pcd"].compute_point_cloud_distance(data_a["pcd"])
        
        # 篩選小於閾值的點
        idxs_a = np.where(np.asarray(dists_a) < contact_threshold)[0]
        idxs_b = np.where(np.asarray(dists_b) < contact_threshold)[0]
        
        if idxs_a.size > 0 and idxs_b.size > 0:
            # 更新 Set
            data_a["contact_indices"].update(idxs_a)
            data_b["contact_indices"].update(idxs_b)
            # print(f"  [接觸] {key_a} <-> {key_b}")

    # 4. 計算標籤並存檔
    print(f"計算標籤並儲存...")
    count = 0
    for key_name, data in pcd_data.items():
        pcd = data["pcd"]
        indices = data["contact_indices"]
        
        # A. 提取點與法向量
        points_np = np.asarray(pcd.points)
        normals_np = np.asarray(pcd.normals)
        
        # B. 計算接觸維度 (核心修改)
        # 這裡會根據 indices 和 label_mode 產生 (N,) 的陣列
        contact_vals = compute_contact_values(
            pcd, indices, 
            mode=label_mode, 
            intensity_radius=contact_threshold * 5 # 給 DBSCAN 一個合理的搜尋半徑
        )
        
        # C. 決定輸出路徑
        base_name = os.path.splitext(key_name)[0]
        out_path = os.path.join(output_dir, base_name + output_format)
        
        # D. 存檔
        save_contact_dataset(out_path, points_np, normals_np, contact_vals)
        count += 1
        
    print(f"處理完成。共生成 {count} 個檔案。")



def visualize_dataset(input_path, data_key='data', 
                         force_range=None,  # 新增: 強制指定範圍 (min, max)
                         bg_color='white'): # 'white' or 'black'
    """
    (V12 改良版) 解決 Intensity 模式不明顯的問題。
    
    改進點:
    1. 自動偵測數據範圍: 區分 Signed Decay (-5~1) 與 Intensity (0~1)。
    2. 強化對比: 將數值為 0 的點設為淺灰色，讓有顏色的點凸顯出來。
    """
    # 1. 取得檔案列表
    file_list = []
    if os.path.isfile(input_path):
        file_list.append(input_path)
    elif os.path.isdir(input_path):
        for ext in ['*.npz', '*.h5', '*.npy']:
            file_list.extend(glob.glob(os.path.join(input_path, '**', ext), recursive=True))
            
    if not file_list: 
        print("找不到檔案")
        return

    print(f"--- 啟動高對比視覺化 (V12) ---")
    
    geometries = []
    
    # 設定 Colormap (建議用 Turbo 或 Jet)
    cmap = plt.get_cmap("jet") 

    for fpath in file_list:
        try:
            # --- 讀取數據 ---
            if fpath.endswith('.npz'):
                with np.load(fpath) as f:
                    key = data_key if data_key in f else list(f.keys())[0]
                    data = f[key]
            elif fpath.endswith('.h5'):
                import h5py
                with h5py.File(fpath, 'r') as hf:
                    key = data_key if data_key in hf else list(hf.keys())[0]
                    data = np.array(hf[key])
            else: continue

            xyz = data[:, 0:3]
            normals = data[:, 3:6]
            vals = data[:, 6]

            # --- 關鍵修正：範圍判定 ---
            # 如果使用者沒有指定範圍，則自動判斷
            if force_range is None:
                min_val_in_data = np.min(vals)
                # 判斷邏輯: 如果數據最小值 >= 0，代表是 Binary 或 Intensity 模式
                if min_val_in_data >= -0.01:
                    vmin, vmax = 0.0, 1.0
                    mode_desc = "Intensity/Binary Mode (0~1)"
                else:
                    # 否則就是 Signed Decay 模式，範圍設大一點以顯示遠處
                    vmin, vmax = -5.0, 1.0
                    mode_desc = "Signed Decay Mode (-5~1)"
            else:
                vmin, vmax = force_range
                mode_desc = f"Custom Range ({vmin}~{vmax})"

            print(f"File: {os.path.basename(fpath)} | {mode_desc}")

            # --- 顏色計算 ---
            num_points = len(xyz)
            colors = np.zeros((num_points, 3))
            
            # 1. 歸一化 (將數值映射到 0.0 ~ 1.0)
            vals_clamped = np.clip(vals, vmin, vmax)
            norm_vals = (vals_clamped - vmin) / (vmax - vmin)
            
            # 2. 應用 Colormap
            colors = cmap(norm_vals)[:, :3]

            # --- 3. 視覺優化技法：背景淡化 (Masking) ---
            # 如果是 Intensity 模式 (0~1)，我們把數值接近 0 的點變成淡灰色
            # 這樣有顏色的部分就會非常明顯
            if vmin >= 0:
                # 建立遮罩：只有強度 > 0.01 的點才上色
                mask = vals > 0.01
                
                # 設定背景色 (淡灰)
                bg_grey = [0.9, 0.9, 0.9] if bg_color == 'white' else [0.2, 0.2, 0.2]
                
                # 先把所有點塗成背景色
                base_colors = np.tile(bg_grey, (num_points, 1))
                
                # 只將「有接觸」的點填入 Colormap 的顏色
                base_colors[mask] = colors[mask]
                colors = base_colors

            # 建立 Open3D 物件
            pcd = o3d.geometry.PointCloud()
            pcd.points = o3d.utility.Vector3dVector(xyz)
            pcd.normals = o3d.utility.Vector3dVector(normals)
            pcd.colors = o3d.utility.Vector3dVector(colors)
            
            geometries.append(pcd)

        except Exception as e:
            print(f"Error reading {fpath}: {e}")

    # --- 顯示視窗 ---
    if geometries:
        # 加個座標軸
        geometries.append(o3d.geometry.TriangleMesh.create_coordinate_frame(size=10.0, origin=[0,0,0]))
        
        vis = o3d.visualization.Visualizer()
        vis.create_window(window_name="Improved Visualization", width=1024, height=768)
        
        opt = vis.get_render_option()
        opt.point_size = 4.0 # 點大一點看得比較清楚
        
        if bg_color == 'white':
            opt.background_color = np.asarray([1.0, 1.0, 1.0])
        else:
            opt.background_color = np.asarray([0.0, 0.0, 0.0])

        for geom in geometries:
            vis.add_geometry(geom)
            
        vis.run()
        vis.destroy_window()
# ==========================================================
# == 使用範例 ==
# ==========================================================
if __name__ == "__main__":
    # 設定
    INPUT_FOLDER = "./my_assembly_raw"   # 原始點雲資料夾
    OUTPUT_FOLDER = "./training_data_bin" # 輸出資料夾
    
    # 執行轉換 (Binary 模式)
    process_assembly_data_gen(
        input_dir=INPUT_FOLDER,
        output_dir=OUTPUT_FOLDER,
        contact_threshold=0.5,
        label_mode='binary',     # 'binary' 或 'intensity'
        output_format='.npz'     # 推薦使用 .npz
    )
    
    # 測試 Loader
    # 假設轉出了一個檔案，我們試著讀回來看看
    sample_file = glob.glob(os.path.join(OUTPUT_FOLDER, "*.npz"))
    if sample_file:
        print(f"\n--- 測試讀取: {sample_file[0]} ---")
        data = load_dataset(sample_file[0])
        print(f"資料形狀: {data.shape}") # 預期 (N, 7)
        print(f"前 5 點數據:\n{data[:5]}")
        print(f"最大接觸值: {np.max(data[:, 6])}") # 第7欄是 index 6