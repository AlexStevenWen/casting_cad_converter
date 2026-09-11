import os
from tqdm import tqdm
from collections import defaultdict
import numpy as np
from transform_3D import transform_3D,Parameter_DATA , STL_DATA ,STL_Simplified, transform_Step_OCC,transform_moving_step , transform_Step_OCCseg,transform_stlmerge,transform_OCCstl, transform_step_cloud,transform_Step_OCCsegre,transform_Cloud_2D,STEPto2D,transform_Cloud_STL_2D,transform_Cloud_STL_2D_light
from pc_surface_detection import process_assembly_data_gen ,visualize_dataset
import shutil
import pandas as pd
import glob
import pc_surface_detection
import csv
#Step to Stl



def copy_cad_files_based_on_csv(CAD_source_root,target_root,csv_path,report_csv_name="CAD_Debug_Fixed.csv"):
    """
    根據 CSV 文件中的Item_Name和Item_Name_Version，從來源目錄複製 CAD 文件到目標目錄。
    
    1. 讀取 CSV 文件，獲取Item_Name與Item_Name_Version。
    2. 遍歷 CAD 源目錄，查找符合條件的Item_Name資料。
    3. 複製毛胚（僅複製一次每個Item_Name的對應 STEP 文件）。
    4. 複製組樹（依照Item_Name_Version複製 STEP 文件）。
    5. 顯示進度條，追蹤複製進度。
    
    參數:
        CAD_source_root (str):來源 CAD 文件的根目錄
        target_root (str): 目標存放 CAD 文件的根目錄，預設為 processed_CAD_root + "\Step_file_raw"。
        csv_path = processed_table_root + "\加工生產全(未篩).csv"
    """
    # 讀取 CSV 文件
    if not os.path.exists(csv_path):
        print(f"錯誤：找不到指定的 CSV 檔案 {csv_path}")
        return
        
    df = pd.read_csv(csv_path)

    # 創建目標目錄
    os.makedirs(os.path.join(target_root, 'blank'), exist_ok=True)
    os.makedirs(os.path.join(target_root, 'tree'), exist_ok=True)

    # 用於記錄已處理過的毛胚 Item_Name，避免重複
    copied_blanks = set()

    # 計算總任務數：每個 Item_Name_Version (組樹) + 每個唯一的 Item_Name (毛胚)
    total_tasks = len(df) + len(df['Item_Name'].unique())
    
    # 準備儲存檢查報告的資料 (對應你的 generate_corrected_cad_csv 欄位)
    report_header = ['Folder_Name', 'Expected_FileName', 'Full_Path', 'Status', 'Search_Prefix']
    report_data = []

    print("開始執行檔案複製與狀態檢查...")
    
    # 創建進度條
    with tqdm(total=total_tasks, desc="複製進度", unit="任務") as pbar:
        for index, row in df.iterrows():
            product_code = str(row['Item_Name']).strip()         # 例如 103-200159
            version = str(row['Item_Name_Version']).strip()      # 例如 103-200159-M210416

            expected_name = f"{product_code} assembly.step"
            expected_step = expected_name.lower()
            expected_stp = f"{product_code} assembly.stp".lower()
            
            # 預設該列的檢查狀態 (如果連客戶資料夾都沒配對到，就會維持這個狀態)
            tree_status = "錯誤：在來源目錄中完全找不到該 Item_Name 的資料夾"
            target_file_path = "N/A"

            # 遍歷所有客戶找到匹配的 Item_Name
            for customer in os.listdir(CAD_source_root):
                customer_path = os.path.join(CAD_source_root, customer)
                if not os.path.isdir(customer_path):
                    continue

                product_path = os.path.join(customer_path, product_code)
                if not os.path.exists(product_path):
                    continue

                # ---------------------------------------------------------
                # 1. 複製毛胚文件（僅在第一次遇到該 Item_Name 時處理）
                # ---------------------------------------------------------
                if product_code not in copied_blanks:
                    copied_blanks.add(product_code) # 先登記，避免後續重複尋找
                    source_blank_dir = os.path.join(product_path, '毛胚')
                    
                    if os.path.exists(source_blank_dir):
                        for file in os.listdir(source_blank_dir):
                            if file.strip().lower() in [f"{product_code.lower()}.step", f"{product_code.lower()}.stp"]:
                                source_file = os.path.join(source_blank_dir, file)
                                target_file = os.path.join(target_root, 'blank', f"{product_code}.step")
                                shutil.copy2(source_file, target_file)
                                break  # 假設只有一個毛胚
                    
                    pbar.update(1) # 更新毛胚進度 (無論成功或失敗都推進)

                # ---------------------------------------------------------
                # 2. 複製組樹文件並同步記錄「檢查狀態」
                # ---------------------------------------------------------
                source_tree_dir = os.path.join(product_path, '組樹', version)
                if os.path.exists(source_tree_dir):
                    actual_files = os.listdir(source_tree_dir)
                    step_files = [f for f in actual_files if f.lower().endswith(('.step', '.stp'))]
                    
                    match_found = False
                    for file in actual_files:
                        if file.strip().lower() in [expected_step, expected_stp]:
                            source_file = os.path.join(source_tree_dir, file)
                            target_dir = os.path.join(target_root, 'tree', version)
                            os.makedirs(target_dir, exist_ok=True)
                            
                            # 目標一律統一命名為 .step
                            target_file_path = os.path.join(target_dir, expected_name)
                            shutil.copy2(source_file, target_file_path)
                            
                            tree_status = "OK"
                            match_found = True
                            break
                    
                    # 找不到符合檔名的檔案時，執行你的除錯邏輯
                    if not match_found:
                        if step_files:
                            tree_status = f"找不到，但來源資料夾內有: {', '.join(step_files)}"
                        else:
                            tree_status = "錯誤：來源資料夾內無 .step 檔案"
                else:
                    tree_status = "錯誤：來源無此版本的組樹資料夾"

                break  # 找到產品資料夾後即可跳出客戶遍歷迴圈
            
            # 將該列的檢查結果寫入清單
            report_data.append([version, expected_name, target_file_path, tree_status, product_code])
            pbar.update(1) # 更新組樹任務進度

    # ---------------------------------------------------------
    # 3. 匯出檢查報告
    # ---------------------------------------------------------
    output_csv_path = os.path.join(target_root, report_csv_name)
    with open(output_csv_path, mode='w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(report_header)
        writer.writerows(report_data)

    print("\n資料複製完成！")
    print(f"檢查報告已自動產出：{output_csv_path}")


def copy_cad_files_based_on_csv_v2(CAD_source_root, target_root, csv_path, report_csv_name="CAD_Debug_Fixed.csv"):
    """
    根據 CSV 文件中的 Item_Name 和 Item_Name_Version，從來源目錄複製 CAD 文件到目標目錄。
    強制單一版本篩選邏輯：
    1. 必須要有 CAD 檔 (若都沒有才隨機選一版)
    2. Final_Version_Option 為 TRUE 優先
    3. 承上，若有多版符合或都不符合，以 Creation_Date 最新者優先
    """
    if not os.path.exists(csv_path):
        print(f"錯誤：找不到指定的 CSV 檔案 {csv_path}")
        return
        
    df = pd.read_csv(csv_path)

    # 1. 強制清理字串，去除頭尾不可見的空白，避免分組失敗
    df['Item_Name'] = df['Item_Name'].astype(str).str.strip()
    df['Item_Name_Version'] = df['Item_Name_Version'].astype(str).str.strip()

    # 轉換日期以供後續比對最新版本
    if 'Creation_Date' in df.columns:
        df['Creation_Date_Parsed'] = pd.to_datetime(df['Creation_Date'], errors='coerce')
    else:
        df['Creation_Date_Parsed'] = pd.NaT

    os.makedirs(os.path.join(target_root, 'blank'), exist_ok=True)
    os.makedirs(os.path.join(target_root, 'tree'), exist_ok=True)

    print("正在掃描來源目錄結構 (建立快取以加速搜尋)...")
    product_paths = {}
    if os.path.exists(CAD_source_root):
        for customer in os.listdir(CAD_source_root):
            customer_path = os.path.join(CAD_source_root, customer)
            if not os.path.isdir(customer_path):
                continue
            for prod in os.listdir(customer_path):
                prod_path = os.path.join(customer_path, prod)
                if os.path.isdir(prod_path):
                    product_paths[prod] = prod_path

    # 檢查該版本是否具備 CAD 檔的輔助函式
    def check_has_cad(prod_path, product_code, version):
        expected_step = f"{product_code} assembly.step".lower()
        expected_stp = f"{product_code} assembly.stp".lower()
        source_tree_dir = os.path.join(prod_path, '組樹', version)
        if os.path.exists(source_tree_dir):
            for file in os.listdir(source_tree_dir):
                if file.strip().lower() in [expected_step, expected_stp]:
                    return True
        return False

    print("正在執行多重條件篩選 (每個 Item_Name 僅保留唯一最優版本)...")
    final_rows = []
    
    # 將相同 Item_Name 的資料群組化處理
    for product_code, group in df.groupby('Item_Name'):
        prod_path = product_paths.get(product_code)

        with_cad = []
        without_cad = []

        # 分類是否有 CAD 檔
        for _, row in group.iterrows():
            version = str(row['Item_Name_Version'])
            has_cad = False
            if prod_path:
                has_cad = check_has_cad(prod_path, product_code, version)

            if has_cad:
                with_cad.append(row)
            else:
                without_cad.append(row)

        # 決定候選池 (優先選擇有 CAD 的版本)
        pool = with_cad if with_cad else without_cad
        
        if not pool:
            # 極端情況：該產品無任何資料，退回隨機(第一筆)
            final_rows.append(group.iloc[0])
            continue
            
        pool_df = pd.DataFrame(pool)
        
        # 處理 Final_Version_Option 欄位
        if 'Final_Version_Option' in pool_df.columns:
            pool_df['Is_Final'] = pool_df['Final_Version_Option'].apply(
                lambda x: str(x).strip().upper() in ['TRUE', '1', 'T'] if pd.notnull(x) else False
            )
        else:
            pool_df['Is_Final'] = False
            
        # 核心篩選：1. 是否為最終版(True優先) -> 2. 日期(最新優先)
        # ascending=[False, False] 確保 True 排在 False 前面，新日期排在舊日期前面
        pool_df = pool_df.sort_values(by=['Is_Final', 'Creation_Date_Parsed'], ascending=[False, False])
        
        # 選取排名第一(最優)的那一筆資料
        best_row = pool_df.iloc[0]
        final_rows.append(best_row)

    # 建立全新的 DataFrame
    filtered_df = pd.DataFrame(final_rows)
    print(f" 篩選完成！原始資料: {len(df)} 筆 -> 篩選後唯一零件: {len(filtered_df)} 筆。")
    # ---------------------------------------------------------
    # 開始實際的檔案複製作業與狀態記錄
    # ---------------------------------------------------------
    total_tasks = len(filtered_df) * 2
    
    # 報表欄位升級：拆分出 Blank_Status(毛胚狀態) 與 Tree_Status(組樹狀態)
    report_header = [
        'Item_Name', 'Selected_Version', 'Final_Version_Option', 
        'Creation_Date', 'Expected_FileName', 'Blank_Status', 'Tree_Status', 'Tree_Target_Path'
    ]
    report_data = []

    with tqdm(total=total_tasks, desc="複製進度", unit="任務") as pbar:
        for index, row in filtered_df.iterrows():
            product_code = str(row['Item_Name'])
            version = str(row['Item_Name_Version'])
            
            # 讀取當初篩選時的原始欄位數值
            final_opt = row.get('Final_Version_Option', 'N/A')
            create_dt = row.get('Creation_Date', 'N/A')

            expected_name = f"{product_code} assembly.step"
            expected_step = expected_name.lower()
            expected_stp = f"{product_code} assembly.stp".lower()
            
            # 預設兩者的狀態 (假設連根目錄都找不到)
            blank_status = "錯誤：在來源目錄中找不到該 Item_Name 資料夾"
            tree_status = "錯誤：在來源目錄中找不到該 Item_Name 資料夾"
            target_file_path = "N/A"

            prod_path = product_paths.get(product_code)

            if prod_path:
                # ==========================================
                # 1. 檢查並複製「毛胚」
                # ==========================================
                blank_status = "錯誤：來源無毛胚資料夾"
                source_blank_dir = os.path.join(prod_path, '毛胚')
                
                if os.path.exists(source_blank_dir):
                    blank_status = "錯誤：毛胚資料夾內無符合的 .step 檔案"
                    actual_blank_files = os.listdir(source_blank_dir)
                    blank_step_files = [f for f in actual_blank_files if f.lower().endswith(('.step', '.stp'))]
                    
                    for file in actual_blank_files:
                        if file.strip().lower() in [f"{product_code.lower()}.step", f"{product_code.lower()}.stp"]:
                            source_file = os.path.join(source_blank_dir, file)
                            target_file = os.path.join(target_root, 'blank', f"{product_code}.step")
                            shutil.copy2(source_file, target_file)
                            blank_status = "OK"
                            break
                    
                    # 如果找不到完全相符的檔名，但資料夾裡面有其他 step 檔，記錄下來方便除錯
                    if blank_status != "OK" and blank_step_files:
                        blank_status = f"找不到符合檔名，但有: {', '.join(blank_step_files)}"
                
                pbar.update(1)

                # ==========================================
                # 2. 檢查並複製「組樹」
                # ==========================================
                source_tree_dir = os.path.join(prod_path, '組樹', version)
                
                if os.path.exists(source_tree_dir):
                    actual_tree_files = os.listdir(source_tree_dir)
                    tree_step_files = [f for f in actual_tree_files if f.lower().endswith(('.step', '.stp'))]
                    
                    match_found = False
                    for file in actual_tree_files:
                        if file.strip().lower() in [expected_step, expected_stp]:
                            source_file = os.path.join(source_tree_dir, file)
                            target_dir = os.path.join(target_root, 'tree', version)
                            os.makedirs(target_dir, exist_ok=True)
                            
                            target_file_path = os.path.join(target_dir, expected_name)
                            shutil.copy2(source_file, target_file_path)
                            
                            tree_status = "OK"
                            match_found = True
                            break
                    
                    if not match_found:
                        if tree_step_files:
                            tree_status = f"找不到符合檔名，但有: {', '.join(tree_step_files)}"
                        else:
                            tree_status = "錯誤：組樹資料夾內無 .step 檔案"
                else:
                    tree_status = "錯誤：來源無此版本的組樹資料夾"
                    
                pbar.update(1)
            else:
                # 找不到主資料夾，進度條直接推兩格 (毛胚+組樹)
                pbar.update(2)

            # 將結果記錄到報表 (同時包含 Blank_Status 與 Tree_Status)
            report_data.append([
                product_code, version, final_opt, 
                create_dt, expected_name, blank_status, tree_status, target_file_path
            ])

    # 3. 匯出報告
    output_csv_path = os.path.join(target_root, report_csv_name)
    with open(output_csv_path, mode='w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(report_header)
        writer.writerows(report_data)

    print("\n資料複製完成！")
    print(f"檢查報告已自動產出：{output_csv_path}")


def batch_transform_Step_to_3D(input_dir, output_dir, mode='.stl',
                               Fvector=(0,0,0), Frotation=0, Fmoving=(0,0,0), # 補上 Fmoving
                               tolerance=0.1, tessellate=0.1, 
                               do_align=False, align_target=(0,0,0)):         # 補上對正參數
    """
    遞迴掃描 input_dir 內的所有 .step 檔案，轉換為指定格式檔案，
    並保持與 input_dir 相同的資料夾結構存放到 output_dir。

    :param input_dir: 要掃描的目錄
    :param output_dir: 輸出檔案的根目錄
    :param tolerance: 轉換 STL 的精度參數
    """
    if not os.path.exists(input_dir):
        print(f"目錄不存在: {input_dir}")
        return

    # 取得所有 .step 檔案
    step_files = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            # 建議也可以把 .stp 加進來一起判斷
            if file.lower().endswith((".step", ".stp")): 
                step_files.append(os.path.join(root, file))

    if not step_files:
        print("未找到任何 .step 檔案")
        return

    # 進度條顯示處理過程
    for step_file in tqdm(step_files, desc="Converting .step to {}".format(mode), unit="file"):
        relative_path = os.path.relpath(os.path.dirname(step_file), input_dir)
        target_folder = os.path.join(output_dir, relative_path)
        os.makedirs(target_folder, exist_ok=True)

        # 優化：使用 os.path.splitext 來替換副檔名，避免檔名中間剛好有 .step 被誤換
        base_name = os.path.splitext(os.path.basename(step_file))[0]
        cad_file = os.path.join(target_folder, base_name + mode)

        try:
            # 將所有參數完整傳遞給下游函數
            transform_3D(
                in_path=step_file,
                out_put=cad_file,
                Fvector=Fvector,
                Frotation=Frotation,
                Fmoving=Fmoving,             # 傳遞平移參數
                tolerance=tolerance,
                tessellate_value=tessellate,
                do_align=do_align,           # 傳遞對正開關
                align_target=align_target    # 傳遞對正目標
            )
        except Exception as e:
            print(f"轉換失敗: {step_file}, 錯誤: {e}")
import os
from tqdm import tqdm

def batch_process_assemblies(root_input_dir, root_output_dir, contact_threshold=1, input_extensions=['.pcd', '.ply', '.npz', '.h5']):
    """
    遞迴掃描 root_input_dir。
    如果發現某個資料夾內包含指定副檔名的檔案（視為一個組合件資料夾），
    則呼叫 process_assembly_folder 進行整包處理。
    
    結構範例:
    root_input/
      ├─ Assembly_A/ (內含 part1.ply, part2.ply...) -> 被視為一個目標
      └─ Category_B/
           └─ Assembly_C/ (內含 partX.pcd...)       -> 被視為另一個目標

    :param root_input_dir: 包含多個組合件資料夾的根目錄
    :param root_output_dir: 輸出結果的根目錄
    :param contact_threshold: 接觸閾值
    :param input_extensions: 用來判斷資料夾是否包含有效數據的副檔名列表
    """

    if not os.path.exists(root_input_dir):
        print(f"目錄不存在: {root_input_dir}")
        return

    # 1. 先掃描出所有「含有目標檔案的資料夾」 (Assembly Folders)
    # 這樣做的好處是進度條可以正確顯示總共有幾個資料夾要跑
    valid_assembly_folders = []
    
    print("正在掃描資料夾結構...")
    for current_root, dirs, files in os.walk(root_input_dir):
        # 檢查當前資料夾內是否包含指定的點雲副檔名
        has_valid_files = any(f.lower().endswith(tuple(input_extensions)) for f in files)
        
        if has_valid_files:
            valid_assembly_folders.append(current_root)

    if not valid_assembly_folders:
        print(f"在 {root_input_dir} 中未找到包含 {input_extensions} 的資料夾")
        return

    print(f"共發現 {len(valid_assembly_folders)} 個組合件資料夾，準備開始處理...")

    # 2. 開始批次迴圈
    for input_folder_path in tqdm(valid_assembly_folders, desc="Processing Assemblies", unit="folder"):
        try:
            # --- 計算路徑 ---
            # 計算相對路徑，例如 "Category_B/Assembly_C"
            relative_path = os.path.relpath(input_folder_path, root_input_dir)
            
            # 組合輸出路徑，例如 "root_output/Category_B/Assembly_C"
            target_output_folder = os.path.join(root_output_dir, relative_path)
            
            # 確保輸出資料夾存在
            os.makedirs(target_output_folder, exist_ok=True)

            # --- 呼叫核心函式 ---
            # 這裡傳入的是「資料夾路徑」
            process_assembly_folder(
                input_dir=input_folder_path,   # 來源資料夾 (裡面有多個點雲)
                output_dir=target_output_folder, # 目的資料夾
                contact_threshold=contact_threshold,
                input_extensions=input_extensions,
                output_format="auto" # 根據您的定義傳入
            )

        except Exception as e:
            print(f"\n[Error] 處理資料夾失敗: {input_folder_path}")
            print(f"錯誤訊息: {e}")
def batch_transform_Step_to_3D_OCC(input_dir, output_dir,mode = '.step'):
    """
    遞迴掃描 input_dir 內的所有 .step 檔案，轉換為 .stl 檔案，
    並保持與 input_dir 相同的資料夾結構存放到 output_dir。

    :param input_dir: 要掃描的目錄
    :param output_dir: 輸出 .stl 檔案的根目錄
    :param tolerance: 轉換 STL 的精度參數
    """
    if not os.path.exists(input_dir):
        print(f"目錄不存在: {input_dir}")
        return

    # 取得所有 .step 檔案
    step_files = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith(".step"):
                step_files.append(os.path.join(root, file))

    if not step_files:
        print("未找到任何 .step 檔案")
        return

    # 進度條顯示處理過程
    for step_file in tqdm(step_files, desc="Converting .step to {}".format(mode), unit="file"):
        relative_path = os.path.relpath(os.path.dirname(step_file), input_dir)
        target_folder = os.path.join(output_dir, relative_path)
        os.makedirs(target_folder, exist_ok=True)
        print(step_file)

        cad_file = os.path.join(target_folder, os.path.basename(step_file).replace(".step", mode))
        print(cad_file)

        try:
            transform_Step_OCC(step_file, cad_file)
        except Exception as e:
            print(f"轉換失敗: {step_file}, 錯誤: {e}")
def batch_transform_Step_to_3D_OCCseg(input_dir, output_dir,mode = '.step'):
    """
    遞迴掃描 input_dir 內的所有 .step 檔案，轉換為 .stl 檔案，
    並保持與 input_dir 相同的資料夾結構存放到 output_dir。

    :param input_dir: 要掃描的目錄
    :param output_dir: 輸出 .stl 檔案的根目錄
    :param tolerance: 轉換 STL 的精度參數
    """
    if not os.path.exists(input_dir):
        print(f"目錄不存在: {input_dir}")
        return

    # 取得所有 .step 檔案
    step_files = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith(".step"):
                step_files.append(os.path.join(root, file))

    if not step_files:
        print("未找到任何 .step 檔案")
        return

    # 進度條顯示處理過程
    for step_file in tqdm(step_files, desc="Converting .step to {}".format(mode), unit="file"):
        relative_path = os.path.relpath(os.path.dirname(step_file), input_dir)
        target_folder = os.path.join(output_dir, relative_path)
        os.makedirs(target_folder, exist_ok=True)
        print(step_file)

        cad_file = os.path.join(target_folder, os.path.basename(step_file).replace(".step", ""))
        print(cad_file)

        try:
            transform_Step_OCCseg(step_file, cad_file)
        except Exception as e:
            print(f"轉換失敗: {step_file}, 錯誤: {e}")
def batch_rename_and_copy_by_mode(csv_dir, base_parts_root, output_root, mode='.h5',process_mode = 'selection'):
    if not os.path.exists(output_root):
        os.makedirs(output_root, exist_ok=True)

    csv_files = [f for f in os.listdir(csv_dir) if f.lower().endswith('.csv')]
    error_log = []
    debug_triggered = False # 只印出一次詳細資訊進行除錯

    for csv_name in tqdm(csv_files, desc=f"模式: {process_mode}"):
        csv_path = os.path.join(csv_dir, csv_name)
        full_id = os.path.splitext(csv_name)[0] 
        
        # 提取原始編號 (如 1617501A)
        expected_ref = full_id.rsplit('-', 1)[0] if '-' in full_id else full_id

        try:
            # 自動處理編碼問題，避免欄位名稱亂碼導致抓不到
            df = pd.read_csv(csv_path, encoding='utf-8-sig')
            
            # --- 除錯：印出欄位名稱 (只印一次) ---
            if not debug_triggered:
                print(f"\n[除錯資訊] CSV 欄位名稱: {list(df.columns)}")
                debug_triggered = True

            # 搜尋匹配
            matches = df[df['MatchedReference'].astype(str) == expected_ref]

            if not matches.empty:
                # 尋找 Fitness 欄位 (考量到亂碼，我們用關鍵字搜尋)
                fitness_col = [c for c in df.columns if 'Fitness' in c][0]
                best_match = matches.sort_values(by=fitness_col, ascending=False).iloc[0]
                
                part_id = str(best_match['TestPartFile'])
                ref_id = str(best_match['MatchedReference'])
                
                # --- 核心檢查點：路徑組合 ---
                # 測試路徑：tree / 1617501A-O1 / 1617501A assembly / parts / part_001.h5
                source_file = os.path.join(
                    base_parts_root, 
                    full_id, 
                    f"{ref_id} assembly", 
                    "parts", 
                    f"{part_id}{mode}"
                )
                
                if process_mode == 'version':
                    final_name = f"{full_id}{mode}"
                else:
                    final_name = f"{ref_id}{mode}"

                dest_file = os.path.join(output_root, final_name)

                if os.path.exists(source_file):
                    shutil.copy2(source_file, dest_file)
                else:
                    error_log.append(f"【檔案不存在】: 預期路徑 {source_file}")
            else:
                # 抓出 CSV 裡面實際有的編號，看看為什麼對不起來
                actual_refs = df['MatchedReference'].unique()
                error_log.append(f"【匹配失敗】: {csv_name} 找不到 {expected_ref}。CSV 內只有: {actual_refs}")

        except Exception as e:
            error_log.append(f"【系統錯誤】: {csv_name} -> {str(e)}")

    # 顯示前 5 個錯誤來除錯
    if error_log:
        print("\n--- 錯誤原因分析 (前 5 筆) ---")
        for log in error_log:
            print(log)
    
    print(f"\n[總結] 成功: {len(csv_files) - len(error_log)} / 失敗: {len(error_log)}")
def generate_no_match_report(csv_dir, report_output_path):
    """
    檢查每個 CSV 檔案，如果該檔案中完全沒有出現與檔名匹配的 MatchedReference，則標記為有問題。
    """
    if not os.path.exists(csv_dir):
        print(f"找不到目錄: {csv_dir}")
        return

    csv_files = [f for f in os.listdir(csv_dir) if f.lower().endswith('.csv')]
    problematic_files = []

    for file_name in tqdm(csv_files, desc="檢查檔案完整性"):
        file_path = os.path.join(csv_dir, file_name)
        
        # 1. 從檔名提取預期的 Reference ID
        # 假設檔名是 103-200159-M210416.csv，我們取前兩段：103-200159
        name_parts = file_name.split('-')
        if len(name_parts) >= 2:
            expected_ref = f"{name_parts[0]}-{name_parts[1]}"
        else:
            expected_ref = os.path.splitext(file_name)[0] # 備用方案

        try:
            df = pd.read_csv(file_path)
            
            # 2. 檢查 'MatchedReference' 欄位中是否包含 expected_ref
            # 我們檢查是否「至少有一個」成功的匹配
            has_match = df['MatchedReference'].astype(str).str.contains(expected_ref).any()

            if not has_match:
                # 如果整份檔案都沒有該 ID，記錄下來
                total_rows = len(df)
                no_volume_match_count = (df['MatchedReference'] == 'NoVolumeMatch').sum()
                
                problematic_files.append({
                    'Problematic_File': file_name,
                    'Expected_Reference': expected_ref,
                    'Total_Parts': total_rows,
                    'NoVolumeMatch_Count': no_volume_match_count,
                    'Status': 'CRITICAL: No matches found in entire file'
                })
                
        except Exception as e:
            print(f"讀取 {file_name} 失敗: {e}")

    # 3. 產出調查報表
    if problematic_files:
        report_df = pd.DataFrame(problematic_files)
        report_df.to_csv(report_output_path, index=False, encoding='utf-8-sig')
        print(f"\n[警報] 發現 {len(problematic_files)} 份檔案有問題！")
        print(f"詳細報告已存至: {report_output_path}")
    else:
        print("\n[通過] 所有 CSV 檔案皆包含至少一個有效的匹配參考。")
def batch_transform_Step_to_3D_mergestl(input_dir, output_dir,mode = '.stl'):
    """
    遞迴掃描 input_dir 內的所有 .step 檔案，轉換為 .stl 檔案，
    並保持與 input_dir 相同的資料夾結構存放到 output_dir。

    :param input_dir: 要掃描的目錄
    :param output_dir: 輸出 .stl 檔案的根目錄
    :param tolerance: 轉換 STL 的精度參數
    """
    if not os.path.exists(input_dir):
        print(f"目錄不存在: {input_dir}")
        return

    # 取得所有 .step 檔案
    step_files = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith(".stl"):
                step_files.append(os.path.join(root, file))

    if not step_files:
        print("未找到任何 .step 檔案")
        return

    # 進度條顯示處理過程
    for step_file in tqdm(step_files, desc="Converting .step to {}".format(mode), unit="file"):
        relative_path = os.path.relpath(os.path.dirname(step_file), input_dir)
        target_folder = os.path.join(output_dir, relative_path)
        os.makedirs(target_folder, exist_ok=True)
        print(step_file)

        cad_file = os.path.join(target_folder, os.path.basename(step_file).replace(".stl", mode))
        print(cad_file)

        try:
            transform_stlmerge(step_file, cad_file)
        except Exception as e:
            print(f"轉換失敗: {step_file}, 錯誤: {e}")



def batch_transform_Step_to_stl(input_dir, output_dir,mode = '.stl'):
    """
    遞迴掃描 input_dir 內的所有 .step 檔案，轉換為 .stl 檔案，
    並保持與 input_dir 相同的資料夾結構存放到 output_dir。

    :param input_dir: 要掃描的目錄
    :param output_dir: 輸出 .stl 檔案的根目錄
    :param tolerance: 轉換 STL 的精度參數
    """
    if not os.path.exists(input_dir):
        print(f"目錄不存在: {input_dir}")
        return

    # 取得所有 .step 檔案
    step_files = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith(".step"):
                step_files.append(os.path.join(root, file))

    if not step_files:
        print("未找到任何 .step 檔案")
        return

    # 進度條顯示處理過程
    for step_file in tqdm(step_files, desc="Converting .step to {}".format(mode), unit="file"):
        relative_path = os.path.relpath(os.path.dirname(step_file), input_dir)
        target_folder = os.path.join(output_dir, relative_path)
        os.makedirs(target_folder, exist_ok=True)
        print(step_file)

        cad_file = os.path.join(target_folder, os.path.basename(step_file).replace(".step", mode))
        print(cad_file)

        try:
            transform_OCCstl(step_file, cad_file)
        except Exception as e:
            print(f"轉換失敗: {step_file}, 錯誤: {e}")

def batch_transform_Step_to_3D_moving(input_dir_assembly, input_dir_merged, output_dir, mode=".step", Fvector=(0, 0, 1), Frotation=0):
    """
    遞迴掃描 input_dir_assembly 和 input_dir_merged 內的所有 .step 檔案，根據檔名配對，轉換為 .stl 檔案，
    並保持原本資料夾結構輸出到 output_dir，檔名區分為 name_assembly.stl 和 name_merge.stl。

    :param input_dir_assembly: 組合檔案資料夾
    :param input_dir_merged: 合併檔案資料夾
    :param output_dir: 輸出檔案的根目錄
    :param mode: 輸出的檔案格式，預設為 .stl
    :param Fvector: 旋轉向量，預設為 (0, 0, 1)
    :param Frotation: 旋轉角度，預設為 0
    """

    if not os.path.exists(input_dir_assembly) or not os.path.exists(input_dir_merged):
        print(f"目錄不存在: {input_dir_assembly} 或 {input_dir_merged}")
        return

    # 建立所有 .step 檔案的字典 (根據檔名配對)
    step_files_assembly = {}
    step_files_merged = {}

    # 遞迴掃描 `input_dir_assembly`
    for root, _, files in os.walk(input_dir_assembly):
        for file in files:
            if file.lower().endswith(".step"):
                step_files_assembly[file] = os.path.join(root, file)

    # 遞迴掃描 `input_dir_merged`
    for root, _, files in os.walk(input_dir_merged):
        for file in files:
            if file.lower().endswith(".step"):
                step_files_merged[file] = os.path.join(root, file)

    # 找出兩個資料夾內相同檔名的 `.step` 檔案
    common_files = set(step_files_assembly.keys()) & set(step_files_merged.keys())

    if not common_files:
        print("未找到相對應的 .step 檔案，請確保 assembly 和 merged 內的檔案名稱相同")
        return

    # 保留原本資料夾結構，建立新的資料夾
    for file_name in tqdm(common_files, desc=f"轉換匹配的 .step 為 {mode}", unit="pair"):
        step_path_assembly = step_files_assembly[file_name]
        step_path_merged = step_files_merged[file_name]

        # 產生輸出檔案名稱
        base_name = os.path.splitext(file_name)[0]
        
        # 取得相對路徑，保持原本的資料夾結構
        relative_path = os.path.relpath(os.path.dirname(step_path_assembly), input_dir_assembly)
        output_folder = os.path.join(output_dir, relative_path)

        # 確保輸出資料夾存在
        os.makedirs(output_folder, exist_ok=True)

        # 輸出檔案
        output_path_assembly = os.path.join(output_folder, f"{base_name}{mode}")
        output_path_merged = os.path.join(output_folder, f"{base_name}{mode}")

        try:
            # 呼叫 transform_moving_step 進行轉換
            transform_moving_step(step_path_assembly, step_path_merged, 
                                  output_path_assembly, output_path_merged, 
                                  mode=mode, Fvector=Fvector, Frotation=Frotation)
        except Exception as e:
            print(f"轉換失敗: {file_name}, 錯誤: {e}")

    print("所有檔案處理完畢")
def batch_transform_Step_to_3D_moving_double(
    input_dir_assembly,
    input_dir_merged,
    output_dir_assembly,
    output_dir_merged,
    mode=".stl",
    Fvector=(0, 0, 1),
    Frotation=0
    ):
    """
    遞迴掃描 input_dir_assembly 和 input_dir_merged 內的所有 .step 檔案，
    根據「檔名＋父資料夾名稱（版本號）」配對，轉換為 .stl 檔案，
    並保持原本資料夾結構輸出到 output_dir_assembly 與 output_dir_merged。
    """

    if not os.path.exists(input_dir_assembly) or not os.path.exists(input_dir_merged):
        print(f"目錄不存在: {input_dir_assembly} 或 {input_dir_merged}")
        return

    # 1) 用 defaultdict(list) 收集所有同名檔案的路徑
    step_asm = defaultdict(list)
    step_mer = defaultdict(list)

    for root, _, files in os.walk(input_dir_assembly):
        for f in files:
            if f.lower().endswith(".step"):
                step_asm[f].append(os.path.join(root, f))

    for root, _, files in os.walk(input_dir_merged):
        for f in files:
            if f.lower().endswith(".step"):
                step_mer[f].append(os.path.join(root, f))

    # 2) 只處理兩邊都有的檔名
    common_names = set(step_asm) & set(step_mer)
    if not common_names:
        print("找不到任何同名的 .step 檔案")
        return

    for name in tqdm(common_names, desc="轉換匹配的 .step 為 " + mode, unit="file"):
        asm_list = step_asm[name]
        mer_list = step_mer[name]

        # 3) 依 parent folder（版本號）配對
        for asm_path in asm_list:
            asm_ver = os.path.basename(os.path.dirname(asm_path))
            # 在 merged 清單中找同版本
            matches = [m for m in mer_list if os.path.basename(os.path.dirname(m)) == asm_ver]
            if not matches:
                print(f"警告：Assembly {name} 在版本 {asm_ver} 找不到對應的 merged 檔案")
                continue

            for mer_path in matches:
                base = os.path.splitext(name)[0]

                # 組出輸出路徑（保持原結構）
                rel_asm = os.path.relpath(os.path.dirname(asm_path), input_dir_assembly)
                out_asm_dir = os.path.join(output_dir_assembly, rel_asm)
                os.makedirs(out_asm_dir, exist_ok=True)
                #out_asm = os.path.join(out_asm_dir, f"{base}_assembly{mode}")
                out_asm = os.path.join(out_asm_dir, f"{base}{mode}")
                rel_mer = os.path.relpath(os.path.dirname(mer_path), input_dir_merged)
                out_mer_dir = os.path.join(output_dir_merged, rel_mer)
                os.makedirs(out_mer_dir, exist_ok=True)
                #out_mer = os.path.join(out_mer_dir, f"{base}_merge{mode}")
                out_mer = os.path.join(out_mer_dir, f"{base}{mode}")

                try:
                    transform_moving_step(
                        asm_path, mer_path,
                        out_asm, out_mer,
                        mode=mode, Fvector=Fvector, Frotation=Frotation
                    )
                except Exception as e:
                    print(f"轉換失敗: {name} (版本 {asm_ver}), 錯誤: {e}")

    print("所有檔案處理完畢")
def batch_transform_step_cloud_moving_double(
    input_dir_step, 
    input_dir_cloud, 
    output_dir_step, 
    output_dir_cloud, 
    Fvector=(0, 0, 0), 
    Frotation=0,
    align_target=(0, 0, 0)
    ):
    """
    強韌版批次轉換：
    不依賴完全一致的目錄結構，而是透過「特徵配對」來尋找對應檔案。
    特徵定義：(grandparent_folder, parent_folder, filename)
    例如：s123/src/part1.step 會對應到 s123/src/part1.npz (忽略更上層目錄的差異)
    """

    if not os.path.exists(input_dir_step) or not os.path.exists(input_dir_cloud):
        print("❌ 輸入目錄不存在")
        return

    print("正在建立索引，請稍候...")

    # ==========================================
    # 1. 建立 STEP 檔案索引
    # Key = (上上層資料夾, 上層資料夾, 檔名) -> 這是為了區分 s123/src/part1 和 s456/src/part1
    # Value = 完整路徑
    # ==========================================
    step_index = {}
    
    for root, _, files in os.walk(input_dir_step):
        for f in files:
            if f.lower().endswith(('.step', '.stp')):
                # 取得路徑結構
                # root 可能長這樣: /path/to/step/folder/s123/src
                parent_dir = os.path.basename(root)       # src
                grandparent_dir = os.path.basename(os.path.dirname(root)) # s123
                
                filename_no_ext = os.path.splitext(f)[0] # part1
                
                # 建立特徵 Key: ('s123', 'src', 'part1')
                # 這樣就可以忽略 s123 上面那層 'folder'
                key = (grandparent_dir, parent_dir, filename_no_ext)
                
                step_index[key] = os.path.join(root, f)

    # ==========================================
    # 2. 建立 Cloud 檔案索引 (支援多種格式)
    # ==========================================
    cloud_index = {}
    valid_exts = ['.npz', '.ply', '.h5', '.npy']

    for root, _, files in os.walk(input_dir_cloud):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in valid_exts:
                parent_dir = os.path.basename(root)       # src
                grandparent_dir = os.path.basename(os.path.dirname(root)) # s123
                filename_no_ext = os.path.splitext(f)[0] # part1
                
                key = (grandparent_dir, parent_dir, filename_no_ext)
                cloud_index[key] = os.path.join(root, f)

    # ==========================================
    # 3. 進行配對 (Intersection)
    # ==========================================
    common_keys = set(step_index.keys()) & set(cloud_index.keys())
    
    if not common_keys:
        print("❌ 找不到任何配對檔案。請確認 s123/src/part1 這種結構是否存在。")
        # 除錯用：印出前幾個 keys 看看長怎樣
        if len(step_index) > 0:
            print(f"STEP 範例 Key: {list(step_index.keys())[0]}")
        if len(cloud_index) > 0:
            print(f"Cloud 範例 Key: {list(cloud_index.keys())[0]}")
        return

    print(f"✅ 配對成功！共找到 {len(common_keys)} 組檔案。")

    # ==========================================
    # 4. 開始轉換
    # ==========================================
    for key in tqdm(common_keys, desc="Processing", unit="file"):
        step_path = step_index[key]
        cloud_path = cloud_index[key]
        
        # 組出輸出路徑
        # 我們希望輸出結構跟著 STEP 走，保持 STEP 的相對結構
        rel_path = os.path.relpath(step_path, input_dir_step)
        
        out_s_path = os.path.join(output_dir_step, rel_path)
        
        # 點雲輸出路徑：換副檔名
        cloud_ext = os.path.splitext(cloud_path)[1]
        rel_path_no_ext = os.path.splitext(rel_path)[0]
        out_c_path = os.path.join(output_dir_cloud, rel_path_no_ext + cloud_ext)

        # 建立目錄
        os.makedirs(os.path.dirname(out_s_path), exist_ok=True)
        os.makedirs(os.path.dirname(out_c_path), exist_ok=True)

        try:
            transform_step_cloud(
                step_path, 
                cloud_path, 
                out_s_path, 
                out_c_path,
                Fvector=Fvector, 
                Frotation=Frotation,
                align_target=align_target
            )
        except Exception as e:
            print(f"❌ 錯誤: {key} -> {e}")

    print("全部完成")
def batch_transform_Step_to_Parameter(input_dir, output_dir):
    """
    遞迴掃描 input_dir 內的所有 .step 檔案，轉換為 .stl 檔案，
    並保持與 input_dir 相同的資料夾結構存放到 output_dir。

    :param input_dir: 要掃描的目錄
    :param output_dir: 輸出 .stl 檔案的根目錄
    :param tolerance: 轉換 STL 的精度參數
    """
    if not os.path.exists(input_dir):
        print(f"目錄不存在: {input_dir}")
        return

    # 取得所有 .step 檔案
    step_files = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith(".step"):
                step_files.append(os.path.join(root, file))

    if not step_files:
        print("未找到任何 .step 檔案")
        return

    # 進度條顯示處理過程
    for step_file in tqdm(step_files, desc="Converting .step to .h5", unit="file"):
        relative_path = os.path.relpath(os.path.dirname(step_file), input_dir)
        target_folder = os.path.join(output_dir, relative_path)
        os.makedirs(target_folder, exist_ok=True)
        #print(step_file)

        cad_file = os.path.join(target_folder, os.path.basename(step_file).replace(".step", ".h5"))
        #print(cad_file)

        try:
            a = Parameter_DATA(step_file).to_hdf5(cad_file)
            print(a)
        except Exception as e:
            print(f"轉換失敗: {step_file}, 錯誤: {e}")
def batch_transform_Stl_to_cloud(input_dir, output_dir, point_num= 1024,sampling = "random",mode = ".h5"):
    """
    遞迴掃描 input_dir 內的所有 .stl 檔案，轉換為 點雲 mode檔案，
    並保持與 input_dir 相同的資料夾結構存放到 output_dir。

    :param input_dir: 要掃描的目錄
    :param output_dir: 輸出 mode 檔案的根目錄
    : point_num:  點雲 參數 與數量
    """
    if not os.path.exists(input_dir):
        print(f"目錄不存在: {input_dir}")
        return

    # 取得所有 .stl 檔案
    stl_files = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith(".stl"):
                stl_files.append(os.path.join(root, file))

    if not stl_files:
        print("未找到任何 .stl 檔案")
        return

    # 進度條顯示處理過程
    for stl_file in tqdm(stl_files, desc="Converting STL to cloud", unit="file"):
        relative_path = os.path.relpath(os.path.dirname(stl_file), input_dir)
        target_folder = os.path.join(output_dir, relative_path)
        os.makedirs(target_folder, exist_ok=True)

        cloud_file = os.path.join(target_folder, os.path.basename(stl_file).replace(".stl", mode ))

        try:
            STL_DATA(stl_file, cloud_file).STLtoCloud(number_of_points=point_num,mode=sampling)
        except Exception as e:
            print(f"轉換失敗: {stl_file}, 錯誤: {e}")
def batch_transform_Stl_to_normalcloud(input_dir, output_dir, point_num= 1024,sampling = 'random',mode = ".h5"):
    """
    遞迴掃描 input_dir 內的所有 .stl 檔案，轉換為 點雲 mode檔案，
    並保持與 input_dir 相同的資料夾結構存放到 output_dir。

    :param input_dir: 要掃描的目錄
    :param output_dir: 輸出 mode 檔案的根目錄
    : point_num:  點雲 參數 與數量
    """
    if not os.path.exists(input_dir):
        print(f"目錄不存在: {input_dir}")
        return

    # 取得所有 .stl 檔案
    stl_files = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith(".stl"):
                stl_files.append(os.path.join(root, file))

    if not stl_files:
        print("未找到任何 .stl 檔案")
        return

    # 進度條顯示處理過程
    for stl_file in tqdm(stl_files, desc="Converting STL to cloud", unit="file"):
        relative_path = os.path.relpath(os.path.dirname(stl_file), input_dir)
        target_folder = os.path.join(output_dir, relative_path)
        os.makedirs(target_folder, exist_ok=True)

        cloud_file = os.path.join(target_folder, os.path.basename(stl_file).replace(".stl", mode ))

        try:
            STL_DATA(stl_file, cloud_file).STLtoNormalCloud(number_of_points=point_num,mode=sampling)
        except Exception as e:
            print(f"轉換失敗: {stl_file}, 錯誤: {e}")
def batch_transform_Stl_to_voxel(input_dir, output_dir, voxel_size= 10,mode = ".h5"):
    """
    遞迴掃描 input_dir 內的所有 .stl 檔案，轉換為 點雲 mode檔案，
    並保持與 input_dir 相同的資料夾結構存放到 output_dir。

    :param input_dir: 要掃描的目錄
    :param output_dir: 輸出 mode 檔案的根目錄
    : voxel_size:  體素大小
    """
    if not os.path.exists(input_dir):
        print(f"目錄不存在: {input_dir}")
        return

    # 取得所有 .stl 檔案
    stl_files = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith(".stl"):
                stl_files.append(os.path.join(root, file))

    if not stl_files:
        print("未找到任何 .stl 檔案")
        return

    # 進度條顯示處理過程
    for stl_file in tqdm(stl_files, desc="Converting STL to voxel", unit="file"):
        relative_path = os.path.relpath(os.path.dirname(stl_file), input_dir)
        target_folder = os.path.join(output_dir, relative_path)
        os.makedirs(target_folder, exist_ok=True)

        voxel_file = os.path.join(target_folder, os.path.basename(stl_file).replace(".stl", mode ))

        try:
            STL_DATA(stl_file, voxel_file).STLtoVoxel(voxel_size)
        except Exception as e:
            print(f"轉換失敗: {stl_file}, 錯誤: {e}")



def batch_transform_Stl_to_Deep(input_dir, output_dir, 
                                camera_angles_list=[[0, 0, 0], 
                                                    [180, 0, 0], 
                                                    [90, 0, 0], 
                                                    [-90, 0, 0], 
                                                    [0, 90, 0], 
                                                    [0, -90, 0]], 
                                image_width=1024, image_height=1024, radius=128, depth_range=[0.2, 1024], mode=""):
    """
    遞迴掃描 input_dir 內的所有 .stl 檔案，轉換為 Deep Learning 用的多視角圖片/數據，
    並為每個 STL 檔案建立專屬資料夾以避免檔案覆蓋。
    """

    if not os.path.exists(input_dir):
        print(f"目錄不存在: {input_dir}")
        return

    # 取得所有 .stl 檔案
    stl_files = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith(".stl"):
                stl_files.append(os.path.join(root, file))

    if not stl_files:
        print("未找到任何 .stl 檔案")
        return

    # 進度條顯示處理過程
    for stl_file in tqdm(stl_files, desc="Converting STL to Deep", unit="file"):
        # 1. 取得相對於 input_dir 的路徑 (保持原始資料夾結構)
        relative_path = os.path.relpath(os.path.dirname(stl_file), input_dir)
        
        # 2. 取得不含副檔名的檔名 (例如: "gear_01.stl" -> "gear_01")
        file_name_no_ext = os.path.splitext(os.path.basename(stl_file))[0]
        
        # 3. 組合最終路徑: 輸出根目錄 / 相對路徑 / STL檔名資料夾
        # 修正重點：這裡多了一層 file_name_no_ext
        target_folder = os.path.join(output_dir, relative_path, file_name_no_ext)
        
        # 建立該 STL 專屬的資料夾
        os.makedirs(target_folder, exist_ok=True)

        try:
            # 傳入這個專屬資料夾作為輸出的 pngfolder_path
            STL_DATA(stl_file, target_folder).STLtoDeep(
                camera_angles_list=camera_angles_list, 
                image_width=image_width, 
                image_height=image_height, 
                radius=radius, 
                depth_range=depth_range
            )
        except Exception as e:
            print(f"轉換失敗: {stl_file}, 錯誤: {e}")


def batch_transform_Cloud_to_2D(input_dir, output_dir, 
                                       camera_angles_list=[[0, 0, 0], 
                                                           [180, 0, 0], 
                                                           [90, 0, 0], 
                                                           [-90, 0, 0], 
                                                           [0, 90, 0], 
                                                           [0, -90, 0]], 
                                       image_width=1024, image_height=1024, 
                                       radius=128, depth_range=[0.0, 1.0]):
    """
    遞迴掃描 input_dir 內的所有點雲檔案 (.npz, .h5, .ply, .pcd)，
    轉換為多視角熱力圖，並為每個檔案建立專屬資料夾以避免檔案覆蓋。
    """

    if not os.path.exists(input_dir):
        print(f"目錄不存在: {input_dir}")
        return

    # 定義支援的副檔名
    valid_extensions = ('.npz', '.h5', '.ply', '.pcd')

    # 取得所有符合條件的檔案
    cloud_files = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith(valid_extensions):
                cloud_files.append(os.path.join(root, file))

    if not cloud_files:
        print(f"未找到任何支援的點雲檔案 {valid_extensions}")
        return

    # 進度條顯示處理過程
    for file_path in tqdm(cloud_files, desc="Converting Cloud to Multiview", unit="file"):
        # 1. 取得相對於 input_dir 的路徑 (保持原始資料夾結構)
        relative_path = os.path.relpath(os.path.dirname(file_path), input_dir)
        
        # 2. 取得不含副檔名的檔名 (例如: "data_01.npz" -> "data_01")
        file_name_no_ext = os.path.splitext(os.path.basename(file_path))[0]
        
        # 3. 組合最終路徑: 輸出根目錄 / 相對路徑 / 檔名資料夾
        # (結構：Output/SubDir/FileName/View_xx.png)
        target_folder = os.path.join(output_dir, relative_path, file_name_no_ext)
        
        # 建立該檔案專屬的資料夾 (由 Class 內部處理或這裡預先處理皆可，這裡保留您的邏輯)
        os.makedirs(target_folder, exist_ok=True)

        try:
            # 呼叫 Cloud_DATA 類別的方法
            # 這裡對應您原本的 STL_DATA(file, folder).STLtoDeep(...)
            
            STL_DATA(file_path, target_folder).Cloudto2D(
                camera_angles_list=camera_angles_list, 
                image_width=image_width, 
                image_height=image_height, 
                radius=radius, 
                depth_range=depth_range
            )
        except Exception as e:
            print(f"轉換失敗: {file_path}, 錯誤: {e}")

def batch_transform_Cloud_STL_to_2D(
        stl_input_dir,    # STL 檔案所在的根目錄
        cloud_input_dir,  # 點雲檔案所在的根目錄
        output_dir,       # 輸出圖片的根目錄
        cloud_extensions=['.npz', '.h5', '.ply'], # 支援尋找的點雲格式
        camera_angles_list=[
            [0, 0, 0], 
            [180, 0, 0], 
            [90, 0, 0], 
            [-90, 0, 0], 
            [0, 90, 0], 
            [0, -90, 0]
        ], 
        image_width=1024, 
        image_height=1024, 
        radius=128, 
        depth_range=[0, 1]
):
    """
    分別從 stl_input_dir 和 cloud_input_dir 讀取檔案進行配對與混合渲染。
    配對邏輯：假設兩個資料夾內的「相對路徑」與「檔名(不含副檔名)」是相同的。
    """

    if not os.path.exists(stl_input_dir):
        print(f"STL 目錄不存在: {stl_input_dir}")
        return
    if not os.path.exists(cloud_input_dir):
        print(f"點雲目錄不存在: {cloud_input_dir}")
        return

    # --- 1. 掃描 STL 並尋找對應的 Cloud ---
    task_list = []

    print(f"正在掃描並配對檔案...")
    print(f"STL 來源: {stl_input_dir}")
    print(f"點雲來源: {cloud_input_dir}")

    # 遍歷 STL 資料夾
    for root, _, files in os.walk(stl_input_dir):
        for file in files:
            if file.lower().endswith(".stl"):
                # 取得 STL 完整路徑
                stl_full_path = os.path.join(root, file)
                
                # 計算相對路徑 (例如: "category_A/part_01")
                # 這樣我們可以去 Cloud 資料夾對應的位置找檔案
                relative_path = os.path.relpath(root, stl_input_dir)
                filename_no_ext = os.path.splitext(file)[0]
                
                # 在 cloud_input_dir 中尋找對應檔案
                found_cloud_path = None
                
                # 嘗試所有可能的副檔名
                for ext in cloud_extensions:
                    # 預測的點雲路徑: Cloud根目錄 / 相對路徑 / 檔名 + 副檔名
                    potential_path = os.path.join(cloud_input_dir, relative_path, filename_no_ext + ext)
                    
                    if os.path.exists(potential_path):
                        found_cloud_path = potential_path
                        break
                
                # 如果找到配對，加入任務列表
                if found_cloud_path:
                    task_list.append({
                        'stl_path': stl_full_path,
                        'cloud_path': found_cloud_path,
                        'relative_dir': relative_path,  # 用於輸出資料夾結構
                        'filename': filename_no_ext
                    })
                # else:
                #     print(f" [跳過] 找不到對應點雲: {file}")

    if not task_list:
        print("未找到任何有效的成對檔案 (STL + Cloud)。請確認兩邊的資料夾結構與檔名是否對應。")
        return

    print(f"共找到 {len(task_list)} 組配對，開始轉換...")

    # --- 2. 執行轉換 ---
    for task in tqdm(task_list, desc="Dual Input Rendering", unit="obj"):
        try:
            # 組合輸出路徑: Output根目錄 / 相對路徑 / 檔名資料夾
            # 例如: Output/category_A/part_01/
            target_folder = os.path.join(output_dir, task['relative_dir'], task['filename'])
            
            # 呼叫轉換類別
            converter = transform_Cloud_STL_2D(
                cloud_path=task['cloud_path'], 
                stl_path=task['stl_path'], 
                out_path=target_folder
            )

            converter.Cloudto2D(
                camera_angles_list=camera_angles_list, 
                image_width=image_width, 
                image_height=image_height, 
                radius=radius, 
                depth_range=depth_range
            )
            
        except Exception as e:
            print(f"\n[Error] 處理失敗: {task['filename']}, 錯誤: {e}")
def batch_transform_Step_to_3D_OCCsegre(
    dir_step_root,   # 來源 STEP 資料夾
    dir_tree_root,   # 目標 Tree 根目錄
    dir_output_csv   # CSV 輸出目錄
    ):
    """
    支援多版本處理的直接調用版：
    當一個 ID (如 103-200159) 對應多個版本資料夾時 (如 -M210416, -O1)，
    會針對每個版本分別執行轉換並生成對應的 CSV。
    """
    
    if not os.path.exists(dir_step_root) or not os.path.exists(dir_tree_root):
        print("❌ 路徑錯誤，請檢查輸入目錄是否存在")
        return

    os.makedirs(dir_output_csv, exist_ok=True)

    # 1. 獲取所有 STEP 檔案
    step_files = glob.glob(os.path.join(dir_step_root, "*.step"))
    if not step_files:
        print("沒有找到任何 .step 檔案")
        return

    # 2. 獲取 Tree 目錄下所有的資料夾名稱
    try:
        tree_subdirs = [d for d in os.listdir(dir_tree_root) if os.path.isdir(os.path.join(dir_tree_root, d))]
    except Exception as e:
        print(f"讀取 Tree 目錄失敗: {e}")
        return

    print(f"✅ 開始處理 {len(step_files)} 個 STEP 檔案的多版本配對...")

    success_count = 0
    
    for step_path in tqdm(step_files, desc="OCC Segre 多版本處理", unit="file"):
        core_id = os.path.splitext(os.path.basename(step_path))[0]

        # --- 核心修改：找出「所有」匹配的版本資料夾 ---
        # 不再用 next()，改用列表推導式找出所有匹配項
        matched_versions = [d for d in tree_subdirs if d.startswith(core_id)]
        
        if not matched_versions:
            # print(f"⚠️ 跳過: 找不到任何版本符合 {core_id}")
            continue

        # 針對每一個匹配到的版本資料夾進行迴圈
        for matched_ver in matched_versions:
            ver_path = os.path.join(dir_tree_root, matched_ver)

            # 1. 匹配 Assembly 資料夾 (例如 103-200159 assembly)
            try:
                # 在該版本路徑下找 assembly 字樣的資料夾
                matched_asm = next((d for d in os.listdir(ver_path) 
                                   if core_id in d and "assembly" in d.lower()), None)
            except Exception:
                continue

            if not matched_asm:
                continue

            # 2. 定位零件資料夾 (parts)
            in_out_parts_path = os.path.join(ver_path, matched_asm, "parts")

            if not os.path.isdir(in_out_parts_path):
                continue

            # 3. 設定輸出 CSV：檔名與版本資料夾同名
            # 輸出範例：103-200159-M210416.csv 與 103-200159-O1.csv
            out_csv_path = os.path.join(dir_output_csv, f"{matched_ver}.csv")

            # 4. 直接調用函式
            try:
                transform_Step_OCCsegre(step_path, in_out_parts_path, out_csv_path)
                success_count += 1
            except Exception as e:
                print(f"\n❌ 處理失敗 [版本: {matched_ver}]: {e}")

    print(f"\n 批次處理完成！共生成 {success_count} 個 CSV 檔案。")
def batch_process_contact_gen(
    root_dir,           # 根目錄 (例如 .../cloud_upright_z_part/tree/)
    output_root,        # 輸出根目錄 (例如 .../processed_contact_output/)
    contact_threshold=1.0,
    label_mode='binary',
    output_format='.h5'
    ):
    """
    針對單一 input_dir 參數的批次處理（版本安全版）：
    會保留從 root_dir 開始的所有子資料夾結構，確保不同版本的 ID 不會互相覆蓋。
    """
    
    target_folders = []
    valid_exts = ('.h5', '.npz', '.pcd', '.ply')

    print("正在掃描目錄結構...")
    for root, dirs, files in os.walk(root_dir):
        # 尋找最終的零件資料夾 (例如名為 parts 的資料夾)
        if os.path.basename(root).lower() == "parts":
            target_folders.append(root)
        # 或是包含點雲檔案的末端資料夾 (相容 blank 模式)
        elif any(f.lower().endswith(valid_exts) for f in files) and not dirs:
            target_folders.append(root)

    if not target_folders:
        print("❌ 找不到任何有效的點雲資料夾單元。")
        return

    print(f"✅ 找到 {len(target_folders)} 個待處理單元。")

    # 2. 開始執行
    for input_folder in tqdm(target_folders, desc="批次接觸分析"):
        
        # --- 核心修改：計算相對路徑 ---
        # 假設 input_folder 是: ROOT_IN / 103-200159-M210416 / 103-200159 assembly / parts
        # rel_path 就會是: 103-200159-M210416 / 103-200159 assembly / parts
        rel_path = os.path.relpath(input_folder, root_dir)
        
        # 這樣 final_output_dir 就會包含完整的版本資料夾名稱
        final_output_dir = os.path.join(output_root, rel_path)
        
        os.makedirs(final_output_dir, exist_ok=True)

        try:
            # 執行分析
            process_assembly_data_gen(
                input_dir=input_folder, 
                output_dir=final_output_dir, # 這裡現在是唯一的、包含版本號的路徑
                contact_threshold=contact_threshold, 
                label_mode=label_mode, 
                output_format=output_format
            )
        except Exception as e:
            print(f"❌ 處理失敗: {rel_path}, 錯誤: {e}")

    print("\n✅ 所有版本數據已分類輸出完畢。")
def batch_transform_STEP_to_2D(
    input_dir, 
    output_dir, 
    camera_angles_list=[
        [0, 0, 0], 
        [180, 0, 0], 
        [90, 0, 0], 
        [-90, 0, 0], 
        [0, 90, 0], 
        [0, -90, 0]
    ], 
    image_width=1024, 
    image_height=1024, 
    zoom_factor=0.8
):
    if not os.path.exists(input_dir):
        print(f"目錄不存在: {input_dir}")
        return

    # 1. 搜尋所有 STEP 檔案
    step_files = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith(('.step', '.stp')):
                step_files.append(os.path.join(root, file))

    if not step_files:
        print("未找到 STEP 檔案")
        return

    print(f"找到 {len(step_files)} 個檔案，開始批次處理...")

    # 2. 迴圈處理每個檔案
    for file_path in tqdm(step_files, desc="Batch Rendering", unit="file"):
        
        # 計算對應的輸出資料夾結構
        # 原始: Input/Category/Part.step
        # 輸出: Output/Category/Part/View_xx.png
        relative_path = os.path.relpath(os.path.dirname(file_path), input_dir)
        file_name_no_ext = os.path.splitext(os.path.basename(file_path))[0]
        
        # 這是要傳給 STEPto2D 的「資料夾路徑」
        target_folder = os.path.join(output_dir, relative_path, file_name_no_ext)
        
        # 預先建立資料夾 (雖然 script 內也有寫，但外部建立較保險)
        os.makedirs(target_folder, exist_ok=True)

        # 呼叫中間層
        STEPto2D(
            step_file=file_path,
            output_folder=target_folder,  # 傳入資料夾
            camera_angles=camera_angles_list, # 傳入 List
            image_width=image_width,
            image_height=image_height,
            zoom_factor=zoom_factor
        )
def batch_transform_Stl_simplification(input_dir, output_dir, ratio=0.5, mode=".stl"):
    """
    批次網格簡化 (LOD)
    :param ratio: 簡化比例 (0.1 = 保留 10% 面數)
    """
    if not os.path.exists(input_dir):
        print(f"目錄不存在: {input_dir}")
        return

    stl_files = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith(".stl"):
                stl_files.append(os.path.join(root, file))

    if not stl_files:
        print("未找到 .stl 檔案")
        return

    for stl_file in tqdm(stl_files, desc=f"LOD Simplification (Ratio={ratio})", unit="file"):
        relative_path = os.path.relpath(os.path.dirname(stl_file), input_dir)
        target_folder = os.path.join(output_dir, relative_path)
        os.makedirs(target_folder, exist_ok=True)

        out_file = os.path.join(target_folder, os.path.basename(stl_file).replace(".stl", mode))

        try:
            # 1. 初始化
            processor = STL_Simplified(in_path=stl_file, out_path=out_file)
            # 2. 讀取
            v, f = processor.LoadMesh()
            # 3. 處理 (簡化)
            v_new, f_new = processor.simplify_mesh(v, f, ratio=ratio)
            # 4. 存檔
            processor.MeshtoSTL(v_new, f_new)
        except Exception as e:
            print(f"LOD 轉換失敗: {stl_file}, 錯誤: {e}")
def batch_transform_Stl_alpha_shape(input_dir, output_dir, alpha=None, mode=".stl"):
    """
    批次 Alpha Shape 重建
    :param alpha: 控制包絡鬆緊度。若為 None，程式內需自行計算或給定預設值。
    """
    if not os.path.exists(input_dir): return

    stl_files = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith(".stl"):
                stl_files.append(os.path.join(root, file))

    for stl_file in tqdm(stl_files, desc="Alpha Shape Reconstruction", unit="file"):
        relative_path = os.path.relpath(os.path.dirname(stl_file), input_dir)
        target_folder = os.path.join(output_dir, relative_path)
        os.makedirs(target_folder, exist_ok=True)

        out_file = os.path.join(target_folder, os.path.basename(stl_file).replace(".stl", mode))

        try:
            processor = STL_Simplified(in_path=stl_file, out_path=out_file)
            v, f = processor.LoadMesh()
            
            # 如果使用者沒給 alpha，這裡做一個簡單的動態估算 (例如平均邊長的 2 倍)
            # 注意：這需要 import trimesh 或 numpy 計算
            if alpha is None:
                import trimesh
                temp_mesh = trimesh.Trimesh(vertices=v, faces=f)
                avg_edge = np.mean(temp_mesh.edges_unique_length)
                current_alpha = avg_edge * 3.0 # 係數可調整
            else:
                current_alpha = alpha

            # 處理 (Alpha Shape)
            v_new, f_new = processor.compute_alpha_shape(v, alpha=current_alpha)
            
            # 檢查是否有生成面，避免存空檔
            if len(f_new) > 0:
                processor.MeshtoSTL(v_new, f_new)
            else:
                print(f"警告: {stl_file} Alpha Shape 生成失敗 (面數為0)")

        except Exception as e:
            print(f"Alpha Shape 失敗: {stl_file}, 錯誤: {e}")
def batch_transform_Stl_smoothing(input_dir, output_dir, iterations=5, lambda_filter=0.5, mode=".stl"):
    """
    批次拉普拉斯平滑
    :param iterations: 平滑迭代次數
    :param lambda_filter: 平滑強度 (0~1)
    """
    if not os.path.exists(input_dir): return

    stl_files = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith(".stl"):
                stl_files.append(os.path.join(root, file))

    for stl_file in tqdm(stl_files, desc=f"Smoothing (Iter={iterations})", unit="file"):
        relative_path = os.path.relpath(os.path.dirname(stl_file), input_dir)
        target_folder = os.path.join(output_dir, relative_path)
        os.makedirs(target_folder, exist_ok=True)

        out_file = os.path.join(target_folder, os.path.basename(stl_file).replace(".stl", mode))

        try:
            processor = STL_Simplified(in_path=stl_file, out_path=out_file)
            v, f = processor.LoadMesh()
            # 處理 (平滑)
            v_new, f_new = processor.smooth_mesh(v, f, iterations=iterations, lambda_filter=lambda_filter)
            processor.MeshtoSTL(v_new, f_new)
        except Exception as e:
            print(f"平滑失敗: {stl_file}, 錯誤: {e}")
def batch_transform_Stl_vhacd(input_dir, output_dir, use_simple_hull=False, mode=".stl"):
    """
    批次 V-HACD (或凸包) 分解
    :param use_simple_hull: True=僅計算單一凸包(快), False=V-HACD分解(慢,精確)
    """
    if not os.path.exists(input_dir): return

    stl_files = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith(".stl"):
                stl_files.append(os.path.join(root, file))

    desc_text = "Convex Hull" if use_simple_hull else "V-HACD Decomposition"
    
    for stl_file in tqdm(stl_files, desc=desc_text, unit="file"):
        relative_path = os.path.relpath(os.path.dirname(stl_file), input_dir)
        target_folder = os.path.join(output_dir, relative_path)
        os.makedirs(target_folder, exist_ok=True)

        out_file = os.path.join(target_folder, os.path.basename(stl_file).replace(".stl", mode))

        try:
            processor = STL_Simplified(in_path=stl_file, out_path=out_file)
            v, f = processor.LoadMesh()
            # 處理 (V-HACD)
            v_new, f_new = processor.compute_vhacd(v, f, use_simple_hull=use_simple_hull)
            processor.MeshtoSTL(v_new, f_new)
        except Exception as e:
            print(f"結構塊分解失敗: {stl_file}, 錯誤: {e}")
#transform_Step_OCC("49544357.step", "49544357 test.step")
#transform_Step_OCC("10717751.step", "10717751 test.step")
#transform_Step_OCC("103-200159 assembly.step", "103-200159 assembly test.step")
#transform_Step_OCC("KT MB03_pinion_FS assembly.STEP", "KT MB03_pinion_FS assembly test.step")
#transform_Step_OCC("KT MB03_pinion_FS assembly test.step", "KT MB03_pinion_FS assembly test 2.step")
#transform_Step_OCC("20819101H assembly.step", "20819101H assembly test.step")
#transform_Step_OCC("2990001G assembly.step", "2990001G assembly test.step")
#transform_Step_OCC("10715386 assembly.step", "10715386 assembly test.step")
#transform_Step_OCC("10717751 assembly.step", "10717751 assembly test.step")
#transform_Step_OCC("10732524.step", "10732524 test.step")
#transform_Step_OCC("10732965 assembly.step", "10732965 assembly test.step")
#transform_moving_step("49544357.step", "49544357 test.step", "49544357 m.step", "49544357 test m.step", )
#a = Parameter_DATA("10732965 assembly test.step").to_hdf5("10732965 assembly test.h5")

#print( Parameter_DATA("3999夾塊-左_merge.step").to_hdf5("3999夾塊-左_merge.h5"))

