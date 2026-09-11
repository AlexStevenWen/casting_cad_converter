import sys
import os
import open3d as o3d
import numpy as np

# 載入 pc_skeletor 函式庫
try:
    from pc_skeletor import LBC
except ImportError:
    print("錯誤：找不到 'pc_skeletor' 函式庫。")
    print("請確認已在您的獨立環境中使用 'pip install pc-skeletor' 安裝。")
    sys.exit(1)

def skeletonize(in_path, out_folder, down_sample=0.01):
    """
    載入點雲檔案，執行 LBC 骨架提取，並儲存結果。

    :param in_path: 輸入的點雲檔案路徑 (例如 .ply, .pcd)
    :param out_folder: 儲存骨架 (skeleton.pcd) 和拓撲 (topology.ply) 檔案的資料夾
    :param down_sample: LBC 下採樣的體素大小 (Voxel size for down-sampling)
    """
    print(f"--- 開始處理點雲： {in_path} ---")

    # --- 1. 載入點雲 ---
    if not os.path.exists(in_path):
        print(f"錯誤：找不到輸入檔案 {in_path}")
        return

    print(f"正在載入點雲...")
    try:
        # 使用 open3d 讀取您先前產生的點雲檔案
        pcd = o3d.io.read_point_cloud(in_path)
        if not pcd.has_points():
            print(f"錯誤：檔案 {in_path} 載入失敗或不包含任何點。")
            return
        print(f"載入成功，包含 {len(pcd.points)} 個點。")
    except Exception as e:
        print(f"載入點雲時發生錯誤: {e}")
        return

    # --- 2. 初始化 LBC ---
    print(f"使用 down_sample={down_sample} 初始化 LBC...")
    # 您可以在這裡傳入更多 LBC 的超參數，例如：
    # lbc = LBC(point_cloud=pcd, 
    #           down_sample=down_sample, 
    #           MAX_LAPLACE_CONTRACTION_WEIGHT=1024, 
    #           MAX_POSITIONAL_WEIGHT=1024)
    lbc = LBC(point_cloud=pcd, down_sample=down_sample)

    # --- 3. 執行骨架提取 ---
    print("正在提取骨架 (extract_skeleton)...")
    lbc.extract_skeleton()

    print("正在提取拓撲 (extract_topology)...")
    lbc.extract_topology()

    # --- 4. 匯出結果 ---
    os.makedirs(out_folder, exist_ok=True)
    print(f"正在將結果匯出至 {out_folder}...")
    
    try:
        lbc.export_results(output_folder=out_folder)
        
        # 檢查是否真的產生了檔案
        skel_file = os.path.join(out_folder, 'skeleton.pcd')
        topo_file = os.path.join(out_folder, 'topology.ply')

        if os.path.exists(skel_file) and os.path.exists(topo_file):
            print(f"骨架檔案已儲存: {skel_file}")
            print(f"拓撲檔案已儲存: {topo_file}")
            print("--- 處理完成 ---")
        else:
            print("警告：結果檔案未成功產生。")
            if len(lbc.skeleton.points) == 0:
                print("警告：產生的骨架沒有任何點。請嘗試調整 'down_sample' 參數。")
            
    except Exception as e:
        print(f"匯出結果時發生錯誤: {e}")
        print("請檢查 LBC 參數是否正確，以及 'down_sample' 值是否過大或過小。")


def main():
    """
    主函式，用於解析命令列參數。
    用法: python skeletonize_pcd.py <in_path> <out_folder> [down_sample]
    """
    if len(sys.argv) < 3:
        print("用法: python skeletonize_pcd.py <in_path> <out_folder> [down_sample]")
        print("\n  <in_path>:     輸入的點雲檔案 (例如 'my_cloud.ply')")
        print("  <out_folder>:  儲存結果的資料夾 (例如 'output_skeleton')")
        print("  [down_sample]: (可選) LBC 下採樣體素大小, 預設 0.01")
        print("                 (這對結果影響很大，請務必嘗試調整此數值)")
        sys.exit(1)

    in_path = sys.argv[1]
    out_folder = sys.argv[2]
    down_sample = 0.01 # 預設值

    if len(sys.argv) > 3:
        try:
            down_sample = float(sys.argv[3])
            if down_sample <= 0:
                raise ValueError("down_sample 必須大於 0")
        except ValueError as e:
            print(f"錯誤：down_sample 參數 '{sys.argv[3]}' 必須是正數。 {e}")
            sys.exit(1)

    skeletonize(in_path, out_folder, down_sample)

if __name__ == "__main__":
    main()