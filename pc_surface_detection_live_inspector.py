import pc_surface_detection
import open3d as o3d
import matplotlib.pyplot as plt
import numpy as np
import os 

def plot_simulated_distribution(mode_to_test, radius=15.0, output_dir="./pc_surface_detection_output_plots"):
    print(f"--- 正在分析模式: {mode_to_test} ---")
    
    # 確保輸出資料夾存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. 建立點雲平面 (100x100 Grid)
    grid_size = 100
    x = np.linspace(-50, 50, grid_size)
    y = np.linspace(-50, 50, grid_size)
    X, Y = np.meshgrid(x, y)
    Z = np.zeros_like(X)
    points = np.vstack((X.flatten(), Y.flatten(), Z.flatten())).T
    
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)
    
    # 2. 模擬中心點接觸 (在 0,0 附近)
    dists_to_origin = np.linalg.norm(points, axis=1)
    
    # 【關鍵修改】：把模擬接觸範圍放大到 radius
    mock_contact_indices = np.where(dists_to_origin <= radius)[0]
    
    # 3. 呼叫你的核心函式計算強度
    vals = pc_surface_detection.compute_contact_values(
        pcd, 
        mock_contact_indices, 
        mode=mode_to_test, 
        intensity_radius=radius
    )

    # 4. 數據準備：將一維陣列轉回二維矩陣用於繪圖
    intensity_matrix = vals.reshape(grid_size, grid_size)

    # --- 開始繪製圖形 ---
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    # 圖 A：2D 熱力圖 (俯視圖)
    im = ax1.imshow(intensity_matrix, extent=[-50, 50, -50, 50], origin='lower', cmap='jet')
    plt.colorbar(im, ax=ax1, label='Intensity')
    ax1.set_title(f"2D Heatmap: {mode_to_test}")
    ax1.set_xlabel("X distance")
    ax1.set_ylabel("Y distance")

    # 圖 B：1D 剖面圖 (取中心切線 Y=0)
    center_idx = grid_size // 2
    x_slice = x
    intensity_slice = intensity_matrix[center_idx, :]
    
    ax2.plot(x_slice, intensity_slice, color='red', linewidth=2, label='Center Slice (Y=0)')
    # 標註半徑點 (應該在 Intensity=0.5 左右)
    ax2.axvline(x=radius, color='gray', linestyle='--', alpha=0.7, label=f'Radius R={radius}')
    ax2.axvline(x=-radius, color='gray', linestyle='--', alpha=0.7)
    ax2.axhline(y=0.5, color='green', linestyle=':', label='Intensity = 0.5')
    
    ax2.set_title(f"1D Profile: {mode_to_test}")
    ax2.set_xlabel("Distance from Center")
    ax2.set_ylabel("Intensity Value")
    ax2.set_ylim(-0.1, 1.1)
    ax2.grid(True, alpha=0.3)
    ax2.legend()

    plt.tight_layout()
    
    # --- 自動儲存取代顯示 ---
    filename = f"{mode_to_test}_R{int(radius)}.png"
    filepath = os.path.join(output_dir, filename)
    
    # 儲存高畫質圖片
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    print(f"✅ 成功儲存: {filepath}")
    
    # 關閉圖表釋放記憶體 (非常重要！)
    plt.close(fig)

if __name__ == "__main__":
    # 既然改成自動儲存了，我們可以直接用一個 list 把所有你想看的模式一次跑完
    modes_to_run = [
    # --- 1. 基準對照組 (Baseline) ---
    "binary",               # 硬分割 (0或1)，用來證明純硬標籤的缺陷

    # --- 2. 局部物理特徵 (Local Physics - 著重澆口周邊梯度) ---
    "local_linear",
    "gaussian",
    "flat_core_gaussian",        # [預期 IoU 最高] 模擬熱點擴散與溫度梯度
    "sigmoid",         # 模擬流體充填波前 (VOF)
    "parabolic",        # 模擬管流黏滯與剪切力
    "exponential",         # 模擬冷鐵激冷與晶粒細化率
    "weibull",    # 模擬微觀缺陷與破壞擴張機率
    "region_score",
    "csvm",
    "shortest_l2",

    # --- 3. 全域物理特徵 (Global Physics - 著重整體鑄件形狀與流長) ---
    "global_linear",        # 模擬全域壓降與流動勢能
    "global_gaussian",
    "global_flat_core_gaussian", # 模擬鑄件整體熱傳導邊界
    "global_sigmoid",            # 模擬巨觀流體推進波前
    "global_parabolic",          # 模擬宏觀流動阻力
    "global_exponential",        # 模擬整體鑄件冷卻時序
    "global_weibull"             # 模擬全域巨觀缺陷分佈
    
]
    
    print("開始批次生成分佈圖...")
    for mode in modes_to_run:
        plot_simulated_distribution(mode, radius=15.0)
    print("批次生成完畢！")