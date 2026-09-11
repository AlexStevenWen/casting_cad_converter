
import json
import argparse
# 假設您的 3D 處理函數都放在一個名為 'transform_engine.py' 的檔案中
# 請根據您的實際檔名修改下面這行
from cad_converter import process_3d_file_unified, process_3d_file_unified_batch

def main():
    """
    主執行函式：
    1. 從命令列讀取 --config 參數來取得 JSON 設定檔路徑。
    2. 載入並解析 JSON 檔案。
    3. 遍歷設定檔中的每一個任務，並動態呼叫對應的處理函數。
    """
    # 1. 設定參數解析器，接收 --config 參數
    parser = argparse.ArgumentParser(description="3D 檔案批次轉換與處理工具")
    parser.add_argument("--config", required=True, help="指向 JSON 設定檔的路徑")
    args = parser.parse_args()

    # 2. 讀取並驗證 JSON 設定檔
    try:
        with open(args.config, "r", encoding="utf-8") as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"錯誤：設定檔 '{args.config}' 不存在。")
        return
    except json.JSONDecodeError:
        print(f"錯誤：設定檔 '{args.config}' 格式不正確，請檢查 JSON 語法。")
        return
    except Exception as e:
        print(f"讀取設定檔時發生未知錯誤: {e}")
        return

    # 3. 執行處理流程 (Pipeline)
    # 從 JSON 根部取得名為 "processing_pipeline" 的任務列表
    tasks = config.get("processing_pipeline", [])

    if not tasks:
        print("警告：在設定檔中未找到 'processing_pipeline' 鍵，或任務列表為空。")
        return

    print(f"--- 成功載入設定檔 '{args.config}'，發現 {len(tasks)} 個任務 ---")

    # 遍歷並執行每一個任務
    for i, task in enumerate(tasks):
        task_name = task.get("task_name", f"任務 #{i+1}")

        # 如果任務被禁用 (enabled: false)，則跳過
        if not task.get("enabled", True):
            print(f"\n--> [已跳過] 任務 '{task_name}' (已禁用)")
            continue

        print(f"\n===> [開始執行] 任務: '{task_name}' <===")

        task_type = task.get("type")
        params = task.get("parameters", {})

        # 驗證任務基本結構
        if not task_type or not params or 'operation' not in params:
            print(f"   [錯誤] 任務 '{task_name}' 缺少 'type', 'parameters' 或 'operation' 鍵，無法執行。")
            continue

        # 根據 "type" 動態呼叫對應的函數
        try:
            if task_type == "single":
                # 使用 **params 將字典解包為關鍵字參數傳入
                process_3d_file_unified(**params)
            elif task_type == "batch":
                process_3d_file_unified_batch(**params)
            else:
                print(f"   [錯誤] 未知的任務類型 '{task_type}'。")

        except TypeError as e:
            # 這個錯誤通常表示缺少必要參數 (如 in_path) 或傳入了函數不認識的參數
            print(f"   [參數錯誤] 任務 '{task_name}' 執行失敗: {e}")
        except Exception as e:
            # 捕捉處理函數內部可能發生的其他所有錯誤
            print(f"   [執行時錯誤] 任務 '{task_name}' 執行時發生未預期錯誤: {e}")

    print("\n--- 所有已啟用的任務均已執行完畢 ---")


if __name__ == "__main__":
    main()