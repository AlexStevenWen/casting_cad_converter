import sys
import traceback
import gc

from OCC.Core.STEPControl import STEPControl_Reader, STEPControl_Writer, STEPControl_AsIs
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Fuse
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeSolid
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import (
    TopAbs_SOLID, TopAbs_SHELL, TopAbs_FACE,
    TopAbs_COMPOUND, TopAbs_REVERSED
)
from OCC.Core.TopoDS import topods_Solid, topods_Shell, TopoDS_Compound
from OCC.Core.BRep import BRep_Builder
# 引入列表工具，用於批次運算
from OCC.Core.TopTools import TopTools_ListOfShape
# 引入幾何簡化工具 (解決記憶體爆量與卡頓的關鍵)
from OCC.Core.ShapeUpgrade import ShapeUpgrade_UnifySameDomain
from OCC.Core.BRepCheck import BRepCheck_Analyzer
from OCC.Core.BRepGProp import brepgprop
from OCC.Core.GProp import GProp_GProps
from OCC.Core.BRepBndLib import brepbndlib_Add
from OCC.Core.Bnd import Bnd_Box

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError: pass

def log_message(log_path, message):
    try:
        with open(log_path, "a", encoding="utf-8") as log_file:
            print(message)
            sys.stdout.flush()
            log_file.write(message + "\n")
    except: pass

# --- 幾何工具 ---

def get_bounding_box(shape, tol=0.0):
    bbox = Bnd_Box()
    brepbndlib_Add(shape, bbox, False)
    bbox.SetGap(tol) 
    return bbox

def boxes_intersect(b1, b2):
    if b1.IsVoid() or b2.IsVoid(): return False
    return not b1.IsOut(b2)

def get_shape_volume(shape):
    if shape.IsNull(): return 0.0
    try:
        props = GProp_GProps()
        brepgprop.VolumeProperties(shape, props)
        return props.Mass()
    except: return 0.0

def explore_solids(shape):
    """ 遞迴提取所有 Solid """
    solids = []
    if shape.IsNull(): return solids

    def add_unique_solid(new_solid):
        if new_solid.IsNull(): return
        if get_shape_volume(new_solid) <= 1e-7: return
        for s in solids:
            if s.IsSame(new_solid): return
        solids.append(new_solid)

    if shape.ShapeType() == TopAbs_SOLID:
        add_unique_solid(topods_Solid(shape))
    elif shape.ShapeType() == TopAbs_COMPOUND:
        exp = TopExp_Explorer(shape, TopAbs_SOLID)
        while exp.More():
            add_unique_solid(topods_Solid(exp.Current()))
            exp.Next()
    # 簡化處理：如果只有 Shell，嘗試轉 Solid (可依需求加回完整邏輯)
    return solids

def simplify_shape(shape):
    """
    關鍵函數：移除多餘的內部邊界 (共面線、共面面)。
    這能大幅減少拓樸複雜度，防止記憶體溢出。
    """
    try:
        unif = ShapeUpgrade_UnifySameDomain(shape, True, True, True)
        unif.Build()
        return unif.Shape()
    except Exception:
        return shape

def batch_fuse_solids(solids_list, tolerance, log_path):
    """
    【批次合併策略】
    不使用兩兩迴圈，而是找出所有「與主體有交集」的物件，一次性 Fuse。
    """
    if not solids_list: return []
    
    # 按體積排序，最大的當主體 (Base)，運算較穩
    solids_list.sort(key=lambda s: get_shape_volume(s), reverse=True)
    
    remaining_solids = solids_list[:]
    final_disjoint_parts = []

    log_message(log_path, f"--- Starting Batch Fuse (Tol: {tolerance}) ---")

    while len(remaining_solids) > 0:
        # 取出最大的當基底
        base_solid = remaining_solids.pop(0)
        base_bbox = get_bounding_box(base_solid, tolerance)
        
        # 找出所有與 base_solid 接觸的零件 (Candidates)
        tools_to_fuse = TopTools_ListOfShape()
        next_round_solids = []
        
        candidates_count = 0
        for other_solid in remaining_solids:
            other_bbox = get_bounding_box(other_solid, tolerance)
            
            if boxes_intersect(base_bbox, other_bbox):
                tools_to_fuse.Append(other_solid)
                candidates_count += 1
                # 擴大 BBox 以便抓到連鎖接觸的零件 (Chain reaction)
                base_bbox.Add(other_bbox) 
            else:
                next_round_solids.append(other_solid)
        
        # 如果有找到可以合併的零件，執行批次合併
        if candidates_count > 0:
            log_message(log_path, f"  Group found: Base + {candidates_count} parts. Fusing...")
            
            # 使用 BRepAlgoAPI_Fuse 的參數化介面
            # SetArguments: 主體
            # SetTools: 工具列表 (C++ 層級迴圈，效率極高)
            fuse_algo = BRepAlgoAPI_Fuse()
            base_args = TopTools_ListOfShape()
            base_args.Append(base_solid)
            
            fuse_algo.SetArguments(base_args)
            fuse_algo.SetTools(tools_to_fuse)
            fuse_algo.SetFuzzyValue(tolerance) # 設定模糊公差
            fuse_algo.SetRunParallel(True)     # 開啟多核心
            fuse_algo.Build()
            
            if fuse_algo.IsDone():
                result = fuse_algo.Shape()
                # --- 關鍵步驟：合併後立刻簡化幾何 ---
                log_message(log_path, "  Fuse done. Simplifying geometry...")
                cleaned_result = simplify_shape(result)
                
                # 將結果放回 final 列表 (或者放回 remaining 繼續檢查，這裡選擇視為一個獨立區塊)
                final_disjoint_parts.append(cleaned_result)
                log_message(log_path, "  Block processing complete.")
            else:
                log_message(log_path, "  WARNING: Fuse failed. Keeping parts separate.")
                final_disjoint_parts.append(base_solid)
                # 失敗的話，工具列表裡的也要加回去 (這裡簡化處理，直接放回 disjoint)
                # 實際應用可能需要更細的 Error Handling
        else:
            # 沒有接觸任何東西，它是獨立的
            final_disjoint_parts.append(base_solid)
            
        remaining_solids = next_round_solids
        gc.collect()

    return final_disjoint_parts

def pack_into_compound(shapes):
    builder = BRep_Builder()
    comp = TopoDS_Compound()
    builder.MakeCompound(comp)
    for s in shapes:
        builder.Add(comp, s)
    return comp

def step_to_step(in_path, out_path, log_path="process_log.txt"):
    try:
        log_message(log_path, "\n" + "="*60)
        log_message(log_path, f"Processing: {in_path}")
        
        reader = STEPControl_Reader()
        if reader.ReadFile(in_path) != 1:
            log_message(log_path, "ERROR: Read failed")
            return
        reader.TransferRoots()
        shape = reader.OneShape()
        solids = explore_solids(