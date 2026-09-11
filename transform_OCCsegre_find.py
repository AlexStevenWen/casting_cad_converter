import csv
import os
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

def generate_comprehensive_reports(target_dir):
    """
    針對「單件目標辨識（含背景雜訊件）」的情境：
    每個 CSV 視為一個測試場景，只要場景中成功找出一件目標，即算該場景辨識成功。
    Fitness、RMSE 等數據僅針對「成功辨識出的目標件」進行統計。
    """
    input_path = Path(target_dir)
    
    if input_path.is_file() and input_path.suffix.lower() == '.csv':
        csv_files = [input_path]
    elif input_path.is_dir():
        csv_files = list(input_path.glob("*.csv"))
    else:
        print(f"❌ 錯誤：找不到有效路徑 {input_path}")
        return

    summary_filename = "Match_Rates_Summary.csv"
    details_filename = "Rejected_Clutter_Details.csv" # 改名為「排除之非目標件明細」
    
    csv_files = [f for f in csv_files if f.name not in [summary_filename, details_filename]]

    if not csv_files:
        print(f"⚠️ 在 {input_path} 中找不到可以分析的原始 CSV 檔案。")
        return

    fail_labels = {"NoMatch", "NoVolumeMatch", "StepReadError", "StlConvertError", "PcdError", "None"}
    
    rejected_data = [["來源場景 (CSV)", "被排除的雜訊/非目標件檔名", "排除原因"]]
    
    # 統計指標用
    total_scenes = 0       # 總測試場景數 (CSV數量)
    successful_scenes = 0  # 成功找出目標的場景數
    
    fitness_list = []
    rmse_list = []
    vol_diff_list = []

    print("="*60)
    print("📊 正在分析單件辨識量化指標 (已排除非目標件雜訊)...")
    print("="*60)

    for csv_file in csv_files:
        total_scenes += 1
        scene_has_target = False # 標記這個場景是否成功找到目標
        
        try:
            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                
                if "TestPartFile" not in reader.fieldnames or "MatchedReference" not in reader.fieldnames:
                    print(f"  ⏭️ 跳過 {csv_file.name}: 格式不符")
                    total_scenes -= 1 # 格式不符不計入總場景數
                    continue

                for row in reader:
                    test_part = row["TestPartFile"]
                    matched_ref = row["MatchedReference"]
                    
                    # 判斷這個零件是否配對成功
                    is_success = matched_ref not in fail_labels and matched_ref.strip() != ""
                    
                    if is_success:
                        scene_has_target = True
                        
                        # 只有成功配對的目標件，才抓取數值來計算平均
                        try:
                            fitness = float(row.get("ICP_Fitness (越高越好)", 0))
                            rmse = float(row.get("ICP_RMSE (越低越好)", 999))
                            vol_str = row.get("VolumeDiff_Percent (%)", "100").replace('%', '').strip()
                            vol_diff = float(vol_str)
                            
                            fitness_list.append(fitness)
                            rmse_list.append(rmse)
                            vol_diff_list.append(vol_diff)
                        except ValueError:
                            pass
                    else:
                        # 將未配對的零件記錄為被排除的雜訊
                        rejected_data.append([csv_file.name, test_part, matched_ref])

            if scene_has_target:
                successful_scenes += 1
                print(f"  ✅ {csv_file.name}: 成功尋獲目標件！")
            else:
                print(f"  ⚠️ {csv_file.name}: 整個場景皆未尋獲目標件。")

        except Exception as e:
            print(f"  ❌ 讀取 {csv_file.name} 時發生錯誤: {e}")

    # --- 計算表 4-5 指標 ---
    if total_scenes == 0:
        print("⚠️ 無有效場景可分析。")
        return

    # 計算目標件的平均品質
    avg_fitness = np.mean(fitness_list) if fitness_list else 0.0
    avg_rmse = np.mean(rmse_list) if rmse_list else 0.0
    avg_vol_diff = np.mean(vol_diff_list) if vol_diff_list else 0.0

    # 計算目標件的品質達標率 (只拿成功找出的目標件來算分母)
    total_found_targets = len(fitness_list)
    if total_found_targets > 0:
        fit_achieved = sum(1 for f in fitness_list if f > 0.8)
        rmse_achieved = sum(1 for r in rmse_list if r < 5.0)
        vol_achieved = sum(1 for v in vol_diff_list if v <= 1.5)

        fit_rate = (fit_achieved / total_found_targets) * 100
        rmse_rate = (rmse_achieved / total_found_targets) * 100
        vol_rate = (vol_achieved / total_found_targets) * 100
    else:
        fit_rate = rmse_rate = vol_rate = 0.0

    # 整體場景辨識成功率
    overall_rate = (successful_scenes / total_scenes) * 100

    # --- 輸出終端機報表 (表 4-5 格式) ---
    print("\n" + "="*55)
    print(" 表 4-5 毛胚辨識量化指標 (單件目標辨識情境)")
    print("="*55)
    print(f"{'驗證指標':<15} | {'接受門檻':<12} | {'平均結果':<12} | {'達成率'}")
    print("-" * 55)
    print(f"{'Fitness':<19} | > 0.8        | {avg_fitness:.3f}        | {fit_rate:.1f}%")
    print(f"{'Inlier RMSE':<19} | < 5 mm       | {avg_rmse:.2f} mm      | {rmse_rate:.1f}%")
    print(f"{'體積容差':<15} | <= 1.5%      | {avg_vol_diff:.2f}%       | {vol_rate:.1f}%")
    print(f"{'整體辨識成功率':<13} | ---          | ({successful_scenes}/{total_scenes}) 場景 | {overall_rate:.1f}%")
    print("="*55)

    # --- 匯出被排除的雜訊明細 ---
    details_path = Path("./") / details_filename
    if len(rejected_data) > 1:
        with open(details_path, 'w', newline='', encoding='utf-8-sig') as f:
            csv.writer(f).writerows(rejected_data)
        print(f"\n📁 [非目標件排除明細] 已儲存至: {details_path.name}")

    # --- 生成 matplotlib 圖表 ---
    generate_chart(fit_rate, rmse_rate, vol_rate, overall_rate)

def generate_chart(fit_rate, rmse_rate, vol_rate, overall_rate):
    """生成達成率的長條圖並存檔"""
    
    # [字體修改區]
    # 設定英文字體優先為 Times New Roman，遇到中文退回使用 DFKai-SB (Windows標楷體) 或 BiauKai (Mac標楷體)
    plt.rcParams['font.family'] = ['Times New Roman', 'DFKai-SB', 'KaiTi', 'BiauKai', 'TW-Kai', 'Microsoft JhengHei']
    plt.rcParams['axes.unicode_minus'] = False 
    
    # 設定全域預設字體大小
    plt.rcParams['font.size'] = 18
    
    categories = ['Fitness > 0.8', 'RMSE < 5 mm', '體積容差 ≤ 1.5%', '整體辨識成功率']
    rates = [fit_rate, rmse_rate, vol_rate, overall_rate]
    
    # 稍微放大畫布，避免字體變大後擁擠
    fig, ax = plt.subplots(figsize=(10, 7)) 
    
    # 改變整體辨識成功率的顏色以做區隔
    colors = ['#4C72B0', '#4C72B0', '#4C72B0', '#DD8452']
    bars = ax.bar(categories, rates, color=colors)
    
    for bar in bars:
        yval = bar.get_height()
        # 長條圖上方的文字數字也調大至 16
        ax.text(bar.get_x() + bar.get_width()/2, yval + 1.5, f'{yval:.1f}%', 
                ha='center', va='bottom', fontsize=18, fontweight='bold')
        
    ax.set_ylim(0, 119) 
    
    # 標籤與標題字體再加大
    ax.set_ylabel('達成率 (%)', fontsize=22, fontweight='bold')
    ax.set_title('毛胚辨識量化指標達成率 (單件辨識含雜訊環境)', fontsize=24, fontweight='bold', pad=15)
    
    # 刻度(X與Y軸)字體加大至 16
    ax.tick_params(axis='x', labelsize=18)
    ax.tick_params(axis='y', labelsize=18)
    
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    output_img = "Table_4-5_Chart.png"
    plt.tight_layout()
    plt.savefig(output_img, dpi=300)
    print(f"📈 [數據圖表] 已生成並儲存至: {output_img}")
    print("="*60)

if __name__ == "__main__":
    TARGET_DIR = r"D:\ChynWangProject\data\processed_CAD\csv_identify_parts"  
    generate_comprehensive_reports(TARGET_DIR)