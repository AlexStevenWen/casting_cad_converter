import os
import transform_3D_batch
from SySPath import ChynWangDatapy, ChynWangPojectpy

# 初始化路徑
CP_root = ChynWangPojectpy()
processed_CAD_root = os.path.join(CP_root, "data", "processed_CAD")
csv_identify_dir = os.path.join(processed_CAD_root, "csv_identify_parts")

# 設定實驗參數
exps = range(13, 14)
sampling_methods = ["random", "fps"] #"surface_uniform"]
label_modes = [
    # --- 1. 基準對照組 (Baseline) ---
    #"binary",               # 硬分割 (0或1)，用來證明純硬標籤的缺陷

    # --- 2. 局部物理特徵 (Local Physics - 著重澆口周邊梯度) ---
    "local_linear",
    "gaussian",
    "flat_core_gaussian",        # [預期 IoU 最高] 模擬熱點擴散與溫度梯度
    "sigmoid",         # 模擬流體充填波前 (VOF)
    "parabolic",        # 模擬管流黏滯與剪切力
    "exponential",         # 模擬冷鐵激冷與晶粒細化率
    "weibull",    # 模擬微觀缺陷與破壞擴張機率

    # --- 3. 全域物理特徵 (Global Physics - 著重整體鑄件形狀與流長) ---
    "global_linear",        # 模擬全域壓降與流動勢能
    "global_gaussian",
    "global_flat_core_gaussian", # 模擬鑄件整體熱傳導邊界
    "global_sigmoid",            # 模擬巨觀流體推進波前
    "global_parabolic",          # 模擬宏觀流動阻力
    "global_exponential",        # 模擬整體鑄件冷卻時序
    "global_weibull"             # 模擬全域巨觀缺陷分佈
]
for exp in exps:
    size_str = str(2**exp)
    
    for method in sampling_methods:
        for mode in label_modes:
            print(f"--- 正在處理 2^{exp} | Method: {method} | Mode: {mode} ---")
            
            # 基礎名稱範例: normal_cloud_upright_z_parts_random
            base_name = f"normal_cloud_upright_z_parts_{method}"
            
            # 1. 輸入路徑 (原始點雲)
            input_cloud_dir = os.path.join(processed_CAD_root, "normal_cloud", f"{base_name}_{size_str}")
            
            # 2. 中間路徑 (Contact 產生結果)
            contact_dir = os.path.join(processed_CAD_root, "normal_cloud", f"{base_name}_contact_{mode}_{size_str}")
            
            # 3. 最終輸出路徑 (統一使用 identify)
            # 格式如: normal_cloud_upright_z_parts_random_contact_auto_detect_plateau_identify_8192
            final_output_dir = os.path.join(processed_CAD_root, "normal_cloud", f"{base_name}_contact_{mode}_identify_{size_str}")

            # 步驟 A: 執行 Contact Generation
            transform_3D_batch.batch_process_contact_gen(
                input_cloud_dir,
                contact_dir,
                label_mode=mode
            )

            # 步驟 B: 執行 Rename 與 Copy (目標指向 final_output_dir)
            transform_3D_batch.batch_rename_and_copy_by_mode(
                csv_identify_dir,
                os.path.join(contact_dir, "tree"),
                os.path.join(final_output_dir, "tree")
            )

print("所有批次任務已完成！")