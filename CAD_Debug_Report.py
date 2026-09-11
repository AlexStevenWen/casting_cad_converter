import os
import csv

def generate_corrected_cad_csv(root_path, output_csv):
    header = ['Folder_Name', 'Expected_FileName', 'Full_Path', 'Status', 'Search_Prefix']
    data_rows = []

    if not os.path.exists(root_path):
        print(f"錯誤：找不到路徑 {root_path}")
        return

    subfolders = [f for f in os.listdir(root_path) if os.path.isdir(os.path.join(root_path, f))]

    for folder in subfolders:
        # --- 修正邏輯處 ---
        # 如果資料夾是 103-200159-M210416，我們需要 103-200159
        # 使用 rsplit('-', 1) 從右邊切開第一個遇到的槓，取左邊的部分
        if '-' in folder:
            prefix = folder.rsplit('-', 1)[0]
        else:
            prefix = folder
            
        expected_name = f"{prefix} assembly.step"
        # ----------------
        
        folder_path = os.path.join(root_path, folder)
        full_path = os.path.join(folder_path, expected_name)
        
        # 檢查檔案是否存在
        if os.path.exists(full_path):
            status = "OK"
        else:
            # 除錯：如果找不到，列出資料夾內所有的 .step 檔案，幫你比對差在哪
            actual_files = os.listdir(folder_path)
            step_files = [f for f in actual_files if f.lower().endswith('.step')]
            if step_files:
                status = f"找不到，但資料夾內有: {', '.join(step_files)}"
            else:
                status = "錯誤：資料夾內無 .step 檔案"

        data_rows.append([folder, expected_name, full_path if status == "OK" else "N/A", status, prefix])

    with open(output_csv, mode='w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(data_rows)

    print(f"修正後的檢查完成！報告：{output_csv}")

# 執行
target_dir = r'D:\ChynWangProject\data\processed_CAD\step_upright_z_component\tree'
generate_corrected_cad_csv(target_dir, 'CAD_Debug_Fixed.csv')