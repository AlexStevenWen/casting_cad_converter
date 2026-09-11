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
from sklearn.svm import SVC
from scipy.spatial import cKDTree, ConvexHull

# ==========================================================
# == 核心函式 1：計算接觸強度 (Binary / Intensity) ==
# ==========================================================
def compute_contact_values(pcd, contact_indices, mode='binary', intensity_radius=5.0):

    points_np = np.asarray(pcd.points)
    num_points = len(points_np)
    values = np.zeros(num_points, dtype=np.float32)
    
    if contact_indices is None or len(contact_indices) == 0:
        return values
        
    indices_array = np.array(list(contact_indices))
    contact_points = points_np[indices_array]
    if mode == 'binary':
        values[indices_array] = 1.0
        return values
    # --- 關鍵修正 1：縮小聚類半徑，區隔多個接觸面 ---
    # 不要用很大的 intensity_radius 來做聚類
    # 建議使用固定的小數值 (例如 2.0mm) 或 contact_threshold 的 2 倍
    cluster_eps = 2.0  
    clustering = DBSCAN(eps=cluster_eps, min_samples=2).fit(contact_points)
    labels = clustering.labels_
    
    unique_labels = set(labels)
    centroids = []
    
    for label in unique_labels:
        if label == -1: continue # 雜訊
        cluster_pts = contact_points[labels == label]
        centroids.append(np.mean(cluster_pts, axis=0))
    
    # 如果完全沒成群，退而求其次使用所有接觸點
    if not centroids:
        centroids = [np.mean(contact_points, axis=0)]
    
    centroids = np.array(centroids)
    tree = cKDTree(centroids)

    # --- 關鍵修正 2：計算每個點到「最近中心」的距離 ---
    # 這樣 B 點會對齊 B 中心，C 點會對齊 C 中心
    dists_all, _ = tree.query(points_np)

    # --- 模式 B: Intensity (0 ~ 1, 只計算接觸點內部) ---
    if mode == 'local_linear':
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
    elif mode == 'global_linear':
        tree = cKDTree(centroids)
        
        # 1. 計算所有點到最近澆口中心的距離
        dists_all, _ = tree.query(points_np)
        
        # 2. 找出全域最大距離 (L_max)
        max_dist = np.max(dists_all)
        
        # 防呆：避免只有一個點或是重疊導致除以零
        if max_dist == 0:
            values[:] = 1.0 # 或 0.0，視需求而定
            return values
            
        # 3. 計算全域線性遞減公式
        # V = 1 - (d / L_max)
        values = 1.0 - (dists_all / max_dist)
        
        # 4. 保險截斷 (處理浮點數誤差，確保不小於 0)
        values = np.clip(values, 0.0, 1.0)
        
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
        # 建立樹並查詢
        tree = cKDTree(centroids)
        dists_all, _ = tree.query(points_np)
        edge_threshold = 0.5 
        
        # 建立 KDTree (以質心為準)
        power = 1.5 # 預設是 2 (高斯)。調小 (如 1.5) 會讓尾巴變長，衰減變慢。

        target_threshold = np.clip(edge_threshold, 1e-6, 0.999)
        
        # 重新推導 Sigma (考慮功率參數 p)
        # 公式: sigma = R / (-ln(T))^(1/p)
        sigma = intensity_radius / (np.power(-np.log(target_threshold), 1/power))
        
        # 計算分布 (使用自定義功率)
        # 這裡不使用原本的 exp(-d^2 / 2sigma^2)，改用更廣義的寫法
        values = np.exp(- (np.power(dists_all / sigma, power)))
        
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
    elif mode == 'cauchy_gaussian':
        tree = cKDTree(centroids)
        dists_all, _ = tree.query(points_np)
        
        # --- 參數設定 ---
        edge_threshold = 0.5  # 半徑 R 處的強度
        
        # 柯西分布公式: values = 1 / (1 + (d/gamma)^2)
        # 為了讓 dist = intensity_radius 時 values = edge_threshold
        # 反推 gamma = R / sqrt(1/T - 1)
        gamma = intensity_radius / np.sqrt(1.0 / edge_threshold - 1.0)
        
        # 計算分布
        values = 1.0 / (1.0 + np.power(dists_all / gamma, 2))
        
        return values
    elif mode == 'relativistic_plateau':
        # 1. 基礎距離計算
        tree = cKDTree(centroids)
        dists_all, _ = tree.query(points_np)

        # --- 參數調整區 ---
        # p 控制高原的「平坦度」
        # p = 2.0 (圓潤弧形) / p = 4.0 (標準高原) / p = 8.0 (極致平坦)
        p = 4.0 
        
        # 2. 自動推導歸零邊界 (R_max)
        # 為了保證在 dist = intensity_radius 時強度剛好是 0.5
        # 根據公式反推：R_max = intensity_radius / (0.75^(1/p))
        R_max = intensity_radius / np.power(0.75, 1/p)
        
        # 3. 計算相對論風格分佈 (Lorentz-inspired)
        # beta (v/c) 映射到 0~1 空間
        beta = np.clip(dists_all / R_max, 0, 1)
        
        # 核心公式：sqrt(1 - beta^p)
        # 當 dist = 0 -> beta = 0 -> value = 1 (最高點)
        # 當 dist = intensity_radius -> value = 0.5 (精準符合要求)
        # 當 dist = R_max -> beta = 1 -> value = 0 (精準歸零)
        values = np.sqrt(np.maximum(0, 1 - np.power(beta, p)))

        # 4. 確保物理邊界外絕對為 0
        values[dists_all > R_max] = 0.0

        return values
    elif mode == 'long_tail_plateau':
        # 1. 基礎距離計算
        tree = cKDTree(centroids)
        dists_all, _ = tree.query(points_np)

        # --- 參數調整區 ---
        p = 4.0        # 高原係數：越高則中心越平、0.5 之後掉得越快
        R_max = intensity_radius * 5.0  # 定義「最終歸零」的距離 (設大一點才有長尾感)
        
        # 2. 核心代數高原公式
        # 這保證了 dist = intensity_radius 時，值恰好為 0.5
        base_values = 1.0 / np.sqrt(1.0 + 3.0 * np.power(dists_all / intensity_radius, p))
        
        # 3. 歸零修正 (線性淡出)
        # 讓長尾在 R_max 處平滑地接觸到 0，而不是直接被切斷
        window = np.clip((R_max - dists_all) / (R_max - intensity_radius), 0, 1)
        # 只有在 0.5 以後（d > R）才開始套用 window，確保 0~R 區間不被影響
        mask = dists_all > intensity_radius
        
        values = base_values.copy()
        values[mask] *= window[mask]

        # 4. 極限清理
        values[dists_all >= R_max] = 0.0

        return values
    elif mode == 'relativistic_scoop':
        # 1. 基礎距離計算
        tree = cKDTree(centroids)
        dists_all, _ = tree.query(points_np)

        # --- 參數調整區 ---
        # p 控制「高原的寬度」與「上凹的程度」
        # p = 2.0: 標準上凹 (像個漏斗)
        # p = 4.0: 較寬的高原，然後進入上凹長尾
        p = 2.0 
        
        # 2. 核心公式：1 / (1 + (d/R)^p)
        # 當 d = intensity_radius (R) 時：
        # value = 1 / (1 + 1^p) = 1 / 2 = 0.5 (精準符合要求)
        values = 1.0 / (1.0 + np.power(dists_all / intensity_radius, p))
        
        # 3. 設定一個極遠處的歸零邊界 (可選)
        # 因為上凹函數尾巴極長，如果需要強制歸零，可以加一個遠端切斷
        R_max = intensity_radius * 10.0
        values[dists_all > R_max] = 0.0

        return values

    
    elif mode == 'auto_detect_plateau':
        tree = cKDTree(centroids)
        dists_all, _ = tree.query(points_np)

        # --- 自動偵測參數 ---
        # 自動定義歸零邊界：目前的點雲中，離澆口最遠的點的距離
        R_max = np.max(dists_all) 
        R = intensity_radius
        
        # 形狀參數
        p_spike = 2.0        # 中心上凹程度 (1.0~2.0 較尖，>2.0 較圓潤)
        q_plateau = 2.5     # 高原平坦度 (越大 0.5 之後越平，邊界掉落越快)
        
        values = np.zeros_like(dists_all)

        # 1. 處理【中心尖峰區】 (0 <= d <= R)
        # 確保 d=0 是 1.0, d=R 精準是 0.5
        mask_in = dists_all <= R
        if np.any(mask_in):
            # 使用 (1 - d/R)^p 產生上凹曲線
            values[mask_in] = 0.5 + 0.5 * np.power((R - dists_all[mask_in]) / R, p_spike)

        # 2. 處理【自動高原斷崖區】 (R < d <= R_max)
        # 確保 d=R 是 0.5, d=R_max 精準歸零
        mask_out = (dists_all > R)
        if np.any(mask_out):
            # 正規化 R 之後的距離，t=0 代表在 R 處，t=1 代表在鑄件最遠端
            t = (dists_all[mask_out] - R) / (R_max - R)
            
            # 使用高階超圓公式，保證在 t=0 (即 R 點) 處斜率為 0 (水平對接)
            # 數值會在 0.5 處維持很久，直到最後才急降
            values[mask_out] = 0.5 * np.power(1.0 - np.power(t, q_plateau), 1.0/q_plateau)

        return values
    elif mode == 'flat_core_gaussian':
        tree = cKDTree(centroids)
        dists_all, _ = tree.query(points_np)

        # --- 參數設定 ---
        R = intensity_radius
        
        # sigma 控制澆口外衰減的「快慢」
        # 數值越大，外面衰減越慢 (長尾)；數值越小，外面掉得越快
        # 這裡預設設為 R / 2.0，你可以根據實際視覺感受微調
        sigma = R / 2.0 
        
        values = np.zeros_like(dists_all)

        # 1. 【澆口內】 (d <= R)：強制全部為 1.0
        mask_in = dists_all <= R
        values[mask_in] = 1.0

        # 2. 【澆口外】 (d > R)：從 R 邊緣開始高斯衰減
        mask_out = dists_all > R
        if np.any(mask_out):
            # 將距離平移，把 d=R 當作高斯分布的中心點 (0)
            shifted_dists = dists_all[mask_out] - R
            
            # 標準高斯公式：exp(-x^2 / 2σ^2)
            values[mask_out] = np.exp(- (shifted_dists**2) / (2 * (sigma**2)))

        # 3. 過濾極小值 (保持運算乾淨)
        values[values < 1e-5] = 0.0

        return values
    elif mode == 'global_flat_core_gaussian':
        tree = cKDTree(centroids)
        dists_all, _ = tree.query(points_np)

        R = intensity_radius
        max_dist = np.max(dists_all)
        values = np.zeros_like(dists_all)

        # 1. 核心保持平坦 1.0
        mask_in = dists_all <= R
        values[mask_in] = 1.0

        # 2. 尾巴延伸到全域最遠點
        mask_out = dists_all > R
        if np.any(mask_out) and max_dist > R:
            shifted_dists = dists_all[mask_out] - R
            # 讓 3-sigma 剛好等於剩餘的最大距離，確保最遠點接近 0
            sigma = (max_dist - R) / 3.0 
            values[mask_out] = np.exp(- (shifted_dists**2) / (2 * (sigma**2)))

        return values
    elif mode == 'shortest_l2':
        # 論文做法：點到表面的最短距離。我們這裡使用點到「所有已知接觸點」的最短距離
        # 先過濾雜訊，取得乾淨的接觸點
        valid_mask = labels != -1
        clean_contact_points = contact_points[valid_mask] if len(contact_points[valid_mask]) > 0 else contact_points
        
        tree = cKDTree(clean_contact_points)
        dists_all, _ = tree.query(points_np)
        
        # 論文的自適應閾值 t：找出高信心區域內的最大距離，這裡我們簡化為 intensity_radius
        t = intensity_radius
        
        # 線性映射: 距離在 t 以內為 1 - (d/t)，大於 t 則為 0
        values = 1.0 - (dists_all / t)
        values = np.clip(values, 0.0, 1.0)
        
        return values

    # --- 模式 G: C-SVM Probability (論文中的 SVM Score) ---
    elif mode == 'csvm':
        # 論文做法：訓練一個二元分類器來劃分物件與背景的非線性邊界
        # 1. 準備正樣本 (Label 1)：接觸點本身
        X_pos = contact_points
        y_pos = np.ones(len(X_pos))
        
        # 2. 準備負樣本 (Label 0)：距離接觸中心很遠的點
        tree = cKDTree(centroids)
        dists_all, _ = tree.query(points_np)
        
        # 定義背景：距離大於半徑 1.5 倍的點視為絕對背景
        bg_mask = dists_all > (intensity_radius * 1.5)
        X_neg = points_np[bg_mask]
        
        # 為了效能與平衡，從背景中隨機抽樣與正樣本等量的點
        if len(X_neg) > len(X_pos):
            idx = np.random.choice(len(X_neg), size=len(X_pos), replace=False)
            X_neg = X_neg[idx]
            
        y_neg = np.zeros(len(X_neg))
        
        # 合併訓練集
        X_train = np.vstack((X_pos, X_neg))
        y_train = np.hstack((y_pos, y_neg))
        
        if len(np.unique(y_train)) < 2:
            values[indices_array] = 1.0 # 如果無法區分正負，退回二元模式
            return values
            
        # 3. 訓練 C-SVM (使用 RBF kernel，並開啟機率預測)
        svm_clf = SVC(kernel='rbf', C=1.0, probability=True, gamma='scale')
        svm_clf.fit(X_train, y_train)
        
        # 4. 預測整片點雲的「屬於接觸區的機率」
        # predict_proba 會回傳 [P(y=0), P(y=1)]，我們取 P(y=1)
        values = svm_clf.predict_proba(points_np)[:, 1]
        
        return values

    # --- 模式 H: Region Growing Approx (論文中的 Region Score) ---
    elif mode == 'region_score':
        # 論文做法：將點雲切塊，若該區塊多數點落在目標凸包內，整塊給高分
        # 1. 建立接觸點的 Convex Hull (凸包) 作為目標幾何範圍
        try:
            hull = ConvexHull(contact_points)
        except:
            # 若接觸點太少或共面無法建構凸包，退回最短距離模式
            tree = cKDTree(contact_points)
            dists, _ = tree.query(points_np)
            return np.clip(1.0 - (dists / intensity_radius), 0.0, 1.0)
            
        # 2. 對「全域點雲」進行密度分群 (模擬 Region Growing 的平滑幾何切塊)
        global_clustering = DBSCAN(eps=intensity_radius * 0.5, min_samples=5).fit(points_np)
        global_labels = global_clustering.labels_
        
        # 3. 評估每個群集 (Region) 與接觸區凸包的重疊程度
        for region_id in set(global_labels):
            if region_id == -1:
                continue
            
            region_mask = global_labels == region_id
            region_pts = points_np[region_mask]
            
            # 檢查該區域的點是否在接觸區凸包內 (使用 Delaunay 三角剖分逼近，或以質心距離簡化)
            # 這裡採用計算區域質心到接觸中心的距離來給予該區域統一的分數
            region_centroid = np.mean(region_pts, axis=0)
            
            # 計算這個區域質心到最近接觸中心的距離
            tree = cKDTree(centroids)
            dist_to_contact, _ = tree.query(region_centroid)
            
            # 給予整個區域一致的軟分數 (距離越近，整塊區域分數越高)
            score = 1.0 - (dist_to_contact / intensity_radius)
            values[region_mask] = np.clip(score, 0.0, 1.0)
            
        return values
    elif mode == 'exponential':
        # 1. 指數衰減 (Laplace / Sharp Peak)
        # 特性：中心極度尖銳，一離開中心就快速掉落
        tree = cKDTree(centroids)
        dists_all, _ = tree.query(points_np)
        
        # 設定 decay_rate，這裡設計讓距離到達 intensity_radius 時，強度剛好剩下約 5% (e^-3)
        decay_rate = 3.0 / intensity_radius
        values = np.exp(-decay_rate * dists_all)
        return values
    elif mode == 'global_exponential':
        tree = cKDTree(centroids)
        dists_all, _ = tree.query(points_np)

        max_dist = np.max(dists_all)
        if max_dist == 0: return np.ones_like(dists_all)

        # 為了讓 exp(-lambda * max_dist) = 0.01
        # lambda = -ln(0.01) / max_dist 約等於 4.605 / max_dist
        decay_rate = 4.605 / max_dist

        values = np.exp(-decay_rate * dists_all)
        return values

    elif mode == 'sigmoid':
        # 2. 羅吉斯/S型曲線 (Logistic / Soft Mask)
        # 特性：中心維持完美平坦，在邊界 R 處「平滑但急速」地下墜
        tree = cKDTree(centroids)
        dists_all, _ = tree.query(points_np)
        
        # k 控制邊緣掉落的「陡峭程度」，數值越大越接近完美垂直的懸崖
        k = 10.0 / intensity_radius
        
        # Sigmoid 公式：以 intensity_radius 為中點 (剛好 0.5) 進行平滑急降
        values = 1.0 / (1.0 + np.exp(k * (dists_all - intensity_radius)))
        return values
    elif mode == 'global_sigmoid':
        tree = cKDTree(centroids)
        dists_all, _ = tree.query(points_np)

        max_dist = np.max(dists_all)
        if max_dist == 0: return np.ones_like(dists_all)

        # 將 S 曲線的中心點設在全域距離的一半
        mid_point = max_dist / 2.0
        # 調整 k 值，確保在 d=0 時接近 1，在 d=max_dist 時接近 0
        k = 10.0 / max_dist 

        values = 1.0 / (1.0 + np.exp(k * (dists_all - mid_point)))
        return values
    elif mode == 'weibull':
        # 3. 威布爾分佈 (Weibull / 形狀變形金剛)
        # 特性：單靠一個參數就能變成尖峰、高斯圓頂或平頂高原
        tree = cKDTree(centroids)
        dists_all, _ = tree.query(points_np)
        
        # k (shape) 參數：
        # k = 1.0 -> 等同指數尖峰
        # k = 2.0 -> 等同高斯圓頂
        # k > 3.0 -> 平頂高原 (數值越大頂部越平)
        k = 3.5 
        
        # lambda (scale) 參數：定義衰減範圍
        lam = intensity_radius
        values = np.exp(-np.power(dists_all / lam, k))
        return values
    elif mode == 'global_weibull':
        tree = cKDTree(centroids)
        dists_all, _ = tree.query(points_np)

        max_dist = np.max(dists_all)
        if max_dist == 0: return np.ones_like(dists_all)

        # 形狀參數維持 3.5 (產生平頂高原效果)
        k = 3.5 
        # 尺度參數 lambda 設為最大距離的 2/3，讓高原覆蓋大部分區域，邊緣才下降
        lam = max_dist * 0.66 

        values = np.exp(-np.power(dists_all / lam, k))
        return values
    elif mode == 'cosine_smooth_window':
        # 4. 餘弦窗 (Raised Cosine / Hann Window)
        # 特性：在半徑內平滑過渡，半徑外【保證絕對為 0】，且邊界沒有銳利折角
        tree = cKDTree(centroids)
        dists_all, _ = tree.query(points_np)
        
        values = np.zeros_like(dists_all)
        mask = dists_all <= intensity_radius
        
        # 餘弦公式：(1 + cos(π * d / R)) / 2
        # 當 d=0 為 1.0，當 d=R 完美且平滑地接觸到 0.0
        if np.any(mask):
            values[mask] = 0.5 * (1.0 + np.cos(np.pi * dists_all[mask] / intensity_radius))
            
        return values

    elif mode == 'inverse_distance_weighting':
        # 5. 反距離加權 (IDW / Gravity Decay)
        # 特性：極度尖銳，且尾巴無限延伸 (不會歸零，受距離平方反比影響)
        tree = cKDTree(centroids)
        dists_all, _ = tree.query(points_np)
        
        # p 控制距離懲罰的強度，越大掉落越快 (地理空間內插通常用 1.0 或 2.0)
        p = 2.0
        
        # 為了讓距離為 0 時數值剛好是 1.0，使用正規化倒數公式：1 / ((d/R)^p + 1)
        # 這樣在距離 d = intensity_radius 時，強度會剛好是 0.5
        values = 1.0 / (np.power(dists_all / intensity_radius, p) + 1.0)
        return values
    elif mode == 'parabolic':
        # 泊肅葉流動 (Poiseuille Flow) 二次衰減
        # 特性：中心最高(1.0)，抵達邊界 R 時呈現平滑的拋物線歸零，無外部長尾
        tree = cKDTree(centroids)
        dists_all, _ = tree.query(points_np)
        
        values = np.zeros_like(dists_all)
        mask = dists_all <= intensity_radius
        
        # 二次函數公式： 1 - (d/R)^2
        if np.any(mask):
            values[mask] = 1.0 - np.power(dists_all[mask] / intensity_radius, 2)
            
        return values
    elif mode == 'global_parabolic':
        tree = cKDTree(centroids)
        dists_all, _ = tree.query(points_np)

        max_dist = np.max(dists_all)
        if max_dist == 0: return np.ones_like(dists_all)

        # 公式: 1 - (d / D_max)^2
        values = 1.0 - np.power(dists_all / max_dist, 2)
        # 防呆，確保不出現負值
        values = np.clip(values, 0.0, 1.0) 

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