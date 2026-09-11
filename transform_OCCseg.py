import sys
import os
import csv
import traceback
from pathlib import Path

# 匯入 OCC 相關模組
from OCC.Core.STEPControl import STEPControl_Reader, STEPControl_Writer, STEPControl_AsIs
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import (
    TopAbs_SOLID, TopAbs_SHELL,
    TopAbs_COMPOUND, TopAbs_REVERSED
)
from OCC.Core.TopoDS import topods_Solid, topods_Shell
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeSolid
from OCC.Core.BRepCheck import BRepCheck_Analyzer
from OCC.Core.BRepGProp import brepgprop
from OCC.Core.GProp import GProp_GProps

# --- 輔助函數 (從您的腳本中保留) ---

def is_valid_solid(solid):
    """檢查實體是否有效。"""
    analyzer = BRepCheck_Analyzer(solid)
    return analyzer.IsValid()

def get_shape_volume(shape):
    """計算形狀的體積。"""
    props = GProp_GProps()
    brepgprop.VolumeProperties(shape, props)
    return props.Mass()

def log_message(log_path, message):
    """寫入日誌檔案。"""
    with open(log_path, "a", encoding="utf-8") as log_file:
        log_file.write(message + "\n")

def explore_solids(shape):
    """
    (修正版)
    遞歸探索固體，優先獲取已有的 Solid。
    僅在找不到 Solid 時，才嘗試從 Shell 建立 Solid。
    """
    solids = []

    def add_unique_solid(new_solid):
        # 排除體積小於等於 0 或不合法的實體
        if get_shape_volume(new_solid) <= 1e-6: # 使用一個小的閾值
            return
        if not is_valid_solid(new_solid):
            return
            
        for s in solids:
            # IsSame() 檢查它們是否指向同一個底層 TShape
            if s.IsSame(new_solid):
                return
        solids.append(new_solid)

    # 直接處理已有的 Solid
    if shape.ShapeType() == TopAbs_SOLID:
        solid = topods_Solid(shape)
        add_unique_solid(solid)
        return solids # 找到 Solid，直接返回

    # 處理單個 Shell 轉為 Solid
    if shape.ShapeType() == TopAbs_SHELL:
        shell = topods_Shell(shape)
        if shell.Orientation() != TopAbs_REVERSED:
            builder = BRepBuilderAPI_MakeSolid(shell)
            if builder.IsDone():
                candidate = builder.Solid()
                add_unique_solid(candidate)
        return solids # 處理完 Shell，直接返回

    # 處理 Compound
    if shape.ShapeType() == TopAbs_COMPOUND:
        
        # --- 邏輯修正：順序對調 ---

        # (1) 優先尋找並添加所有已存在的 SOLID
        exp_solid = TopExp_Explorer(shape, TopAbs_SOLID)
        while exp_solid.More():
            solid = topods_Solid(exp_solid.Current())
            add_unique_solid(solid)
            exp_solid.Next()
            
        # (2) 遞歸處理嵌套 Compound
        exp_comp = TopExp_Explorer(shape, TopAbs_COMPOUND)
        while exp_comp.More():
            sub = exp_comp.Current()
            if not sub.IsEqual(shape):
                # 遞歸調用
                for s in explore_solids(sub):
                    add_unique_solid(s)
            exp_comp.Next()

        # (3) 【重要】僅在上述步驟 *完全沒有* 找到任何 Solid 的情況下，
        #     才嘗試從 Shell 構建 Solid。
        #     這避免了從已有 Solid 的 Shell 中重複構建。
        if not solids:
            exp_shell = TopExp_Explorer(shape, TopAbs_SHELL)
            while exp_shell.More():
                shell = topods_Shell(exp_shell.Current())
                if shell.Orientation() != TopAbs_REVERSED:
                    builder = BRepBuilderAPI_MakeSolid(shell)
                    if builder.IsDone():
                        cand = builder.Solid()
                        add_unique_solid(cand)
                exp_shell.Next()

    return solids

# --- 新的輔助函數 ---

def get_shape_centroid(shape):
    """
    計算形狀的質心 (Centroid/Center of Mass)。
    返回 (x, y, z) 元組。
    """
    props = GProp_GProps()
    # 計算體積、質心等屬性
    brepgprop.VolumeProperties(shape, props)
    
    # 檢查體積是否大於零，避免除以零
    if props.Mass() > 1e-9:
        center_of_mass = props.CentreOfMass()
        return (center_of_mass.X(), center_of_mass.Y(), center_of_mass.Z())
    else:
        # 如果沒有體積，返回原點
        return (0.0, 0.0, 0.0)

# --- 主要執行邏輯 ---

def extract_parts_and_coords(in_path, out_dir):
    """
    讀取 STEP 檔案，將每個獨立的 Solid 拆分出來，
    計算其質心座標，並分別儲存。
    """
    
    # 1. 設定輸出路徑
    output_directory = Path(out_dir)
    parts_directory = output_directory / "parts"
    csv_path = output_directory / "coordinates.csv"
    log_path = output_directory / "extraction_log.txt"

    # 建立輸出目錄
    try:
        output_directory.mkdir(parents=True, exist_ok=True)
        parts_directory.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"ERROR: 無法建立目錄 {output_directory}: {e}")
        return

    # (可選) 每次執行時清空日誌
    with open(log_path, "w", encoding="utf-8") as log_file:
        log_file.write(f"--- 開始處理 {in_path} ---\n")

    try:
        log_message(log_path, f"正在處理: {in_path}")
        reader = STEPControl_Reader()
        status = reader.ReadFile(in_path)
        if status != 1:
            log_message(log_path, f"ERROR: 讀取 STEP 檔案失敗: {in_path}")
            return

        reader.TransferRoots()
        shape = reader.OneShape()

        # 2. 尋找所有獨立的 Solid
        solids = explore_solids(shape)
        if not solids:
            log_message(log_path, f"ERROR: 在 {in_path} 中未找到任何有效的實體 (Solid)")
            return
        
        log_message(log_path, f"偵測到 {len(solids)} 個獨立實體")

        coordinate_data = [] # 用於儲存 CSV 數據
        
        # -----------------------------------------------------------------
        # ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼ 錯誤修正 ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
        # 
        # 將 writer = STEPControl_Writer() 從迴圈外移到迴圈內
        # 並刪除 writer.Clear()
        #
        # -----------------------------------------------------------------

        # 3. 遍歷所有 Solid
        for i, solid in enumerate(solids):
            part_id = i + 1
            part_name = f"part_{part_id:03d}" # 格式化為 "part_001"

            try:
                # 4. 計算座標 (質心)
                centroid = get_shape_centroid(solid)
                vol = get_shape_volume(solid)
                
                # 5. 儲存座標數據 (零件編號, 座標xyz, 體積)
                coordinate_data.append([
                    part_name, 
                    f"{centroid[0]:.6f}", 
                    f"{centroid[1]:.6f}", 
                    f"{centroid[2]:.6f}", 
                    f"{vol:.6f}"
                ])

                # 6. 儲存獨立的 STEP 檔案到 'parts' 資料夾
                part_out_path = str(parts_directory / f"{part_name}.step")
                
                # 【修正】在此處建立新的 writer
                writer = STEPControl_Writer() 
                
                # 【修正】刪除了 writer.Clear()
                
                writer.Transfer(solid, STEPControl_AsIs)
                
                if writer.Write(part_out_path) != 1:
                    log_message(log_path, f"ERROR: 寫入零件檔案失敗: {part_out_path}")
                else:
                    log_message(log_path, f"已儲存零件: {part_out_path} (質心: {centroid[0]:.2f}, {centroid[1]:.2f}, {centroid[2]:.2f})")

            except Exception as e_part:
                log_message(log_path, f"ERROR: 處理 {part_name} 時發生錯誤: {e_part}")
                log_message(log_path, traceback.format_exc())

        # 7. 寫入 CSV 檔案
        log_message(log_path, f"正在寫入座標檔案: {csv_path}")
        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                csv_writer = csv.writer(f)
                # 寫入標頭
                csv_writer.writerow(["PartID", "Centroid_X", "Centroid_Y", "Centroid_Z", "Volume"])
                # 寫入數據
                csv_writer.writerows(coordinate_data)
        except IOError as e_csv:
             log_message(log_path, f"ERROR: 寫入 CSV 檔案失敗: {e_csv}")
            
        log_message(log_path, f"--- {in_path} 處理完成 ---")

    except Exception as e:
        log_message(log_path, f"FATAL EXCEPTION on {in_path}: {e}")
        log_message(log_path, traceback.format_exc())

# --- 主程式入口 ---
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用途: python extract_parts.py <input_step_file> <output_directory>")
        print("範例: python extract_parts.py my_assembly.step ./extracted_parts_output")
    else:
        in_file = sys.argv[1]
        out_folder = sys.argv[2]
        extract_parts_and_coords(in_file, out_folder)