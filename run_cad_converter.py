import json
import argparse
import sys
# 假設您的 3D 處理函數都放在一個名為 'cad_converter.py' 的檔案中
# 請根據您的實際檔名修改下面這行
from cad_converter import process_3d_file_unified, process_3d_file_unified_batch

def main():
    """
    主執行函式：
    1. 從命令列讀取 --config 參數來取得 JSON 設定檔路徑。
    2. 載入並解析 JSON 檔案。
    3. 遍歷設定檔中的每一個任務，並動態呼叫對應的處理函數。
    4. 回傳一個包含整體執行結果的字典。
    """
    # 1. 設定參數解析器
    parser = argparse.ArgumentParser(description="3D 檔案批次轉換與處理工具")
    parser.add_argument("--config", required=True, help="指向 JSON 設定檔的路徑")
    args = parser.parse_args()

    # 2. 讀取並驗證 JSON 設定檔
    try:
        with open(args.config, "r", encoding="utf-8") as f:
            config = json.load(f)
    except FileNotFoundError:
        error_msg = f"錯誤：設定檔 '{args.config}' 不存在。"
        print(error_msg)
        return {"status": "error", "message": error_msg}
    except json.JSONDecodeError:
        error_msg = f"錯誤：設定檔 '{args.config}' 格式不正確，請檢查 JSON 語法。"
        print(error_msg)
        return {"status": "error", "message": error_msg}
    except Exception as e:
        error_msg = f"讀取設定檔時發生未知錯誤: {e}"
        print(error_msg)
        return {"status": "error", "message": error_msg}

    # 3. 執行處理流程 (Pipeline)
    tasks = config.get("processing_pipeline", [])

    if not tasks:
        warn_msg = "警告：在設定檔中未找到 'processing_pipeline' 鍵，或任務列表為空。"
        print(warn_msg)
        # 雖然不是錯誤，但沒有任務執行，回傳成功但附上警告訊息
        return {"status": "success", "message": warn_msg, "data": {"total": 0, "success": 0, "failed": 0, "skipped": 0}}

    print(f"--- 成功載入設定檔 '{args.config}'，發現 {len(tasks)} 個任務 ---")

    # 初始化計數器
    successful_tasks = 0
    failed_tasks = 0
    skipped_tasks = 0
    
    # 遍歷並執行每一個任務
    for i, task in enumerate(tasks):
        task_name = task.get("task_name", f"任務 #{i+1}")

        if not task.get("enabled", True):
            print(f"\n--> [已跳過] 任務 '{task_name}' (已禁用)")
            skipped_tasks += 1
            continue

        print(f"\n===> [開始執行] 任務: '{task_name}' <===")
        
        task_type = task.get("type")
        params = task.get("parameters", {})

        if not task_type or not params or 'operation' not in params:
            print(f"   [錯誤] 任務 '{task_name}' 缺少 'type', 'parameters' 或 'operation' 鍵，無法執行。")
            failed_tasks += 1
            continue

        try:
            if task_type == "single":
                process_3d_file_unified(**params)
            elif task_type == "batch":
                process_3d_file_unified_batch(**params)
            else:
                print(f"   [錯誤] 未知的任務類型 '{task_type}'。")
                failed_tasks += 1
                continue # 確保未知類型也算失敗
            
            # 如果沒有異常，則任務成功
            successful_tasks += 1
            print(f"   [成功] 任務 '{task_name}' 執行完畢。")

        except TypeError as e:
            print(f"   [參數錯誤] 任務 '{task_name}' 執行失敗: {e}")
            failed_tasks += 1
        except Exception as e:
            print(f"   [執行時錯誤] 任務 '{task_name}' 發生未預期錯誤: {e}")
            failed_tasks += 1

    # 4. 產生最終報告
    final_message = f"所有已啟用的任務均已執行完畢。總計: {len(tasks)}，成功: {successful_tasks}，失敗: {failed_tasks}，跳過: {skipped_tasks}"
    print(f"\n--- {final_message} ---")
    
    # 如果有任何一個任務失敗，則整體狀態為 "error"
    final_status = "error" if failed_tasks > 0 else "success"

    return {
        "status": final_status,
        "message": final_message,
        "data": {
            "total": len(tasks),
            "success": successful_tasks,
            "failed": failed_tasks,
            "skipped": skipped_tasks
        }
    }

if __name__ == "__main__":
    result = main()

    # 美化輸出，讓結果一目了然
    print("\n--- 執行結果 ---")
    print(json.dumps(result, indent=4, ensure_ascii=False))
    
    # 根據結果狀態碼來結束程式
    # 成功時 exit code 為 0，失敗時為 1
    if result["status"] == "error":
        sys.exit(1)
    else:
        sys.exit(0)
