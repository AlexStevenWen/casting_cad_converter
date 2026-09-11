import os
import shutil
import re

# 1. 您的異常清單資料
raw_data = """
103-200213-O1(合併失敗，Log 狀態： Result contains 9 disjoint groups. -> VALID (Healthy) 比對結果： 吻合。程式嘗試合併 50 個零件，但最終仍然散落成 9 個獨立的群組（disjoint groups），並未形成單一實體)
10717980-WG1(疑似澆口件有問題需檢查)
10730888-O1(疑似澆口件有問題需檢查)
10731478-O1(疑似澆口件有問題需檢查)
10732524-O1(疑似澆口件有問題需檢查)
10732841-O1(疑似澆口件有問題需檢查)
10732965-O11疑似上部分澆口有問題Log 狀態： [FINAL STATUS] The output geometry is INVALID (Zombie/Partial).比對結果： 吻合。雖然宣稱 Real merge achieved，但幾何體被判定為無效或部分損壞。)
10743556-O1 (整個圖檔都有問題，疑似曲面與實體重疊 需要解決，毛胚未匹配到需檢查毛胚 與組樹內毛胚是否一樣且是實體(soild))
10744381-WG220714(澆口合併有問題，Log 狀態： Result contains 20 disjoint groups.比對結果： 吻合。高達 294 個零件，但合併後仍有 20 個未連結的群組，這通常就是澆口無法與主樹幹或鑄件完全接合所導致。)
10744516-WG210908(疑似下澆口件有問題，Log 狀態： [WARNING] Invalid Geometry in Compound Shell->Solid. Starting Deep Heal... ShapeFix success.比對結果： 吻合。該圖檔本身幾何就有破損，觸發了程式的深度修復（Deep Heal），這往往伴隨著澆口或其他曲面的異常。)
10744658-O1 (疑似上澆口件有問題)
10744667-O1(整個圖檔都有問題，疑似曲面與實體重疊 需要解決，毛胚未匹配到需檢查毛胚 與組樹內毛胚是否一樣且是實體(soild))
10732841-O1(毛胚未匹配到需檢查毛胚 與組樹內毛胚 是否一樣 )
10732965-O1(疑似上部分澆口有問題)
10744687-O1(部分澆口有問題)
10744681-YJ210319 (毛胚未匹配到需檢查毛胚 與組樹內毛胚 是否一樣 )
10745488-O1 (毛胚未匹配到需檢查毛胚 與組樹內毛胚 是否一樣 )
10745904-O1(毛胚未匹配到需檢查毛胚 與組樹內毛胚 是否一樣 )
1080901A-O1 (毛胚未匹配到需檢查毛胚 與組樹內毛胚 是否一樣 )
14049549111-O1  (疑似曲面與實體重疊 需要解決)
1690401D-O1(部分下澆口件有問題)
20478805B-O1(右側澆口件有問題)
20511601F-O1 (下澆口件有問題)
20722601J-O1 (方向未矯正 但是目前已經解決)
20835901F-O1 (疑似澆口件有問題) 
20869701G-O1(毛胚未匹配到需檢查毛胚 與組樹內毛胚 是否一樣 Log 狀態： [FINAL STATUS] The output geometry is INVALID (Zombie/Partial). 比對結果： 吻合。圖檔體積異常龐大，且被判定為無效實體。)
20906501J-O1(疑似澆口件有問題，Log 狀態： [FINAL STATUS] The output geometry is INVALID (Zombie/Partial).)
21015301K-O1(毛胚未匹配到需檢查毛胚 與組樹內毛胚 是否一樣 )
21162101B-O1(毛胚未匹配到需檢查毛胚 與組樹內毛胚 是否一樣 )
21222401A-O1(毛胚未匹配到需檢查毛胚 與組樹內毛胚 是否一樣 )
21440601G-O1(毛胚未匹配到需檢查毛胚 與組樹內毛胚 是否一樣 )
22010578-O149544357-O1(毛胚未匹配到需檢查毛胚 與組樹內毛胚 是否一樣 )
2990001G-O1(下部分澆口有問題)
49544357-O1(整個圖檔都有問題...)
68201D-O1(上部分澆口有問題)
ELBOW CELL HOUSING-RH-O1(毛胚未匹配到需檢查毛胚 與組樹內毛胚 是否一樣 )
FX750-24A-WG201211 (疑似澆口件有問題，Log 狀態： 瘋狂觸發 Deep Heal 達 16 次，且 16 parts failed to merge。)
FX750-38F-O1(合併失疑似是圖檔破損所導致...) 
KT YK04_DT_R_Pinion-O1 (方向相反 已解決)
KT YK04_ST_RL-O1(毛胚未匹配到需檢查毛胚 與組樹內毛胚是否一樣...)
NB0119-131-05B-O1
NB0119-131-05B-S230207 (毛胚未匹配到需檢查毛胚(毛胚未切割) 與組樹內毛胚)
放置盒-WG201214(中文問題 已解決)
放置蓋-WG201214(中文問題 已解決)
本體外殼-N210929(中文問題 已解決)
本體外殼-New1 (中文問題 已解決)
"""

# 2. 設定來源與目的資料夾路徑 
SOURCE_DIR = r"D:\ChynWangData\3D_CAD - 複製"  
DEST_DIR = r"D:\Problem_CAD_Files"  

os.makedirs(DEST_DIR, exist_ok=True)

# 3. 超強效文字清洗 (精準提取最上層基礎檔名)
problem_items = set() # 使用 set 防止重複抓取相同名稱
for line in raw_data.strip().split('\n'):
    line = line.strip()
    if not line:
        continue
    
    # 第一步：去除括號或「疑似」後面的說明文
    item_with_version = re.split(r'\(|（|疑似', line)[0].strip()
    
    # 第二步：移除版號後綴 (自動砍掉 -O1, -WG..., -S..., -N... 以及後面的所有字元)
    # 這樣 NB0119-131-05B-S230207 就會變成乾淨的 NB0119-131-05B
    # 22010578-O149544357-O1 就會變成 22010578
    base_name = re.sub(r'-(O|WG|YJ|N|New|S)\d*.*$', '', item_with_version, flags=re.IGNORECASE).strip()
    
    if base_name:
        problem_items.add(base_name)

# --- 印出清洗結果讓您確認 ---
print("🎯 【解析出的最上層資料夾名稱清單】:")
for name in sorted(problem_items):
    print(f" - {name}")
print("=" * 50 + "\n")

# 4. 開始掃描並做「完全吻合」比對
print(f"🔍 開始在 {SOURCE_DIR} 中尋找...\n")
found_count = 0

if not os.path.exists(SOURCE_DIR):
    print(f"❌ 找不到來源資料夾: {SOURCE_DIR}，請確認路徑。")
else:
    for root, dirs, files in os.walk(SOURCE_DIR):
        if DEST_DIR in root:
            continue
            
        for folder_name in dirs:
            # 💡 這次我們要求【完全命中】清洗過後的乾淨名稱
            if folder_name in problem_items:
                print(f"✅ 找到目標: [{folder_name}] (位於 {root})")
                
                source_path = os.path.join(root, folder_name)
                dest_path = os.path.join(DEST_DIR, folder_name)

                try:
                    if not os.path.exists(dest_path):
                        shutil.copytree(source_path, dest_path)
                        print(f"   -> 📁 成功複製到: {dest_path}\n")
                    else:
                        print(f"   -> ⚠️ 目的地已有相同資料夾，跳過。\n")
                except Exception as e:
                    print(f"   -> ❌ 複製失敗: {e}\n")

                found_count += 1

    print(f"🎉 處理完成！共成功挑出 {found_count} 個資料夾。")