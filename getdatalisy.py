import os
import pandas as pd
import locale

# 1. 設定區域語言為繁體中文（台灣），這會影響字串排序邏輯
try:
    locale.setlocale(locale.LC_COLLATE, 'zh_TW.UTF-8')
except:
    # 某些 Windows 環境可能需要寫成 'Chinese_Taiwan.950'
    locale.setlocale(locale.LC_COLLATE, 'Chinese_Taiwan.950')

# 設定路徑
root_dir = r'D:\202603組樹\組樹'
output_path = r'D:\202603組樹\output.xlsx'

data = []

if not os.path.exists(root_dir):
    print(f"錯誤：找不到路徑 {root_dir}")
else:
    # 第一層：遍歷所有客戶
    for customer in os.listdir(root_dir):
        customer_path = os.path.join(root_dir, customer)
        
        if os.path.isdir(customer_path):
            # 取得該客戶資料夾內所有的子資料夾
            sub_items = [item for item in os.listdir(customer_path) 
                         if os.path.isdir(os.path.join(customer_path, item))]
            
            if sub_items:
                for product in sub_items:
                    data.append([customer, product])
            else:
                # 即使沒有子資料夾，也要出現該客戶
                data.append([customer, ""])

    # 建立 DataFrame
    df = pd.DataFrame(data, columns=['客戶', '品名'])

    # 2. 【核心修正】使用 locale 進行筆畫排序
    # 我們利用 sorted 函數配合 locale.strxfrm 處理排序關鍵字
    df['sort_key'] = df['客戶'].apply(locale.strxfrm)
    df = df.sort_values(by='sort_key').drop('sort_key', axis=1)

    # 3. 儲存 Excel
    try:
        df.to_excel(output_path, index=False)
        print("--- 執行成功 ---")
        print(f"已完成「繁體中文筆畫排序」，共計 {len(df)} 筆資料。")
    except Exception as e:
        print(f"發生錯誤：{e}")