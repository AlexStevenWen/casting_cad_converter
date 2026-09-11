import os
import pandas as pd
from pathlib import Path

# 1. 設定來源資料夾路徑與輸出的檔名
folder_path = r'./D:/202604生產單'
output_filename = '檔案清單結果.xlsx'

# 2. 取得所有 .xlsx 檔案的名稱，並去掉副檔名 (.stem 屬性會直接去掉副檔名)
# 我們會排除掉輸出的那個檔案本身，避免重複讀取
file_names = [
    f.stem for f in Path(folder_path).glob('*.xlsx') 
    if f.name != output_filename
]

# 3. 轉成 DataFrame (表格格式)
df = pd.DataFrame(file_names, columns=['檔案名稱'])

# 4. 儲存成新的 xlsx 檔案
df.to_excel(output_filename, index=False)

print(f"完成！已將 {len(file_names)} 個檔名儲存至 {output_filename}")