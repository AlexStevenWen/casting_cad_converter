from OCC.Core.STEPControl import STEPControl_Reader, STEPControl_Writer, STEPControl_AsIs
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Fuse
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeSolid
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import (
    TopAbs_SOLID, TopAbs_SHELL, TopAbs_FACE,
    TopAbs_COMPOUND, TopAbs_COMPSOLID, TopAbs_REVERSED
)
from OCC.Core.TopoDS import topods_Solid, topods_Shell, TopoDS_Solid, TopoDS_Compound
from OCC.Core.BRepCheck import BRepCheck_Analyzer
from OCC.Core.BRepGProp import brepgprop_VolumeProperties, brepgprop 
from OCC.Core.GProp import GProp_GProps
from OCC.Core.BRep import BRep_Builder
import sys
import traceback
import gc 

# 1. 強制設定編碼
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# 體積比率閾值
VOLUME_RATIO_THRESHOLD_D = 0.85
VOLUME_RATIO_THRESHOLD_U = 1.15

def is_valid_solid(solid):
    if solid.IsNull(): return False
    analyzer = BRepCheck_Analyzer(solid)
    return analyzer.IsValid()

def get_shape_volume(shape):
    if shape.IsNull(): return 0.0
    props = GProp_GProps()
    brepgprop.VolumeProperties(shape, props)
    return props.Mass()

def log_message(log_path, message):
    try:
        with open(log_path, "a", encoding="utf-8") as log_file:
            print(message) 
            sys.stdout.flush() 
            log_file.write(message + "\n")
    except: pass

def explore_solids(shape):
    solids = []
    if shape.IsNull(): return solids

    def add_unique_solid(new_solid):
        if new_solid.IsNull(): return
        if get_shape_volume(new_solid) <= 1e-6: return
        for s in solids:
            if s.IsSame(new_solid): return
        solids.append(new_solid)

    if shape.ShapeType() == TopAbs_SOLID:
        add_unique_solid(topods_Solid(shape))
    elif shape.ShapeType() == TopAbs_SHELL:
        shell = topods_Shell(shape)
        if shell.Orientation() != TopAbs_REVERSED:
            builder = BRepBuilderAPI_MakeSolid(shell)
            if builder.IsDone():
                add_unique_solid(builder.Solid())
    elif shape.ShapeType() == TopAbs_COMPOUND:
        exp = TopExp_Explorer(shape, TopAbs_SHELL)
        while exp.More():
            shell = topods_Shell(exp.Current())
            if shell.Orientation() != TopAbs_REVERSED:
                builder = BRepBuilderAPI_MakeSolid(shell)
                if builder.IsDone():
                    add_unique_solid(builder.Solid())
            exp.Next()
        exp_comp = TopExp_Explorer(shape, TopAbs_COMPOUND)
        while exp_comp.More():
            sub = exp_comp.Current()
            if not sub.IsEqual(shape):
                for s in explore_solids(sub):
                    add_unique_solid(s)
            exp_comp.Next()
            
    return solids

def pack_solids_into_one(solids_list, log_path):
    """
    【多殼實體封裝】
    """
    log_message(log_path, f"Packing parts into a SINGLE SOLID container (Multi-Shell)...")
    
    builder = BRep_Builder()
    new_solid = TopoDS_Solid()
    builder.MakeSolid(new_solid)
    
    count = 0
    for shape in solids_list:
        if shape.ShapeType() == TopAbs_SHELL:
            builder.Add(new_solid, shape)
            count += 1
        else:
            exp = TopExp_Explorer(shape, TopAbs_SHELL)
            while exp.More():
                sh = topods_Shell(exp.Current())
                builder.Add(new_solid, sh)
                count += 1
                exp.Next()
                
    log_message(log_path, f"Packed {count} shells into one Solid.")
    return new_solid

def run_greedy_merge_loop(current_solids, tolerance, log_path, pass_name=""):
    """
    【穩定版貪婪合併】
    移除了內部的強制 GC 和 del，恢復到您原始最穩定的狀態。
    """
    solids_rem = current_solids[:]
    merge_count = 0
    
    log_message(log_path, f"--- Starting {pass_name} (Tolerance: {tolerance} mm) with {len(solids_rem)} solids ---")

    while True:
        merged = False
        solids_rem.sort(key=lambda s: get_shape_volume(s), reverse=True)
        
        for i in range(len(solids_rem)):
            for j in range(i + 1, len(solids_rem)):
                s1 = solids_rem[i]
                s2 = solids_rem[j]
                
                vol_i = get_shape_volume(s1)
                vol_j = get_shape_volume(s2)
                
                fuse_op = BRepAlgoAPI_Fuse(s1, s2)
                fuse_op.SetFuzzyValue(tolerance) 
                fuse_op.Build()
                
                if fuse_op.IsDone():
                    fused_candidate = fuse_op.Shape()
                    if is_valid_solid(fused_candidate):
                        vol_fused = get_shape_volume(fused_candidate)
                        if vol_fused > 0:
                            log_message(log_path,
                                f"Merge: Solid {i + 1} ({vol_i:.2f}) + Solid {j + 1} ({vol_j:.2f}) => {vol_fused:.2f}"
                            )
                            # 構建新列表 (Python 自動管理記憶體)
                            new_list = []
                            for k, s in enumerate(solids_rem):
                                if k != i and k != j:
                                    new_list.append(s)
                            new_list.append(fused_candidate)
                            solids_rem = new_list
                            
                            merged = True
                            merge_count += 1
                            break 
            
            if merged:
                break 
        
        if not merged:
            break 

    log_message(log_path, f"--- {pass_name} finished. Merged {merge_count} times. Remaining: {len(solids_rem)} ---")
    
    # 只在「整輪」結束後清理一次，避免干擾內部 C++ 指針
    gc.collect() 
    return solids_rem

def step_to_step(in_path, out_path, log_path="unmerged_files.txt"):
    final_result_shape = None 
    solids = []
    
    try:
        log_message(log_path, "\n" + "="*60)
        log_message(log_path, f"Processing: {in_path}")
        
        reader = STEPControl_Reader()
        status = reader.ReadFile(in_path)
        if status != 1:
            log_message(log_path, f"ERROR: Failed to read STEP file: {in_path}")
            return

        reader.TransferRoots()
        shape = reader.OneShape()
        solids = explore_solids(shape)
        
        # 讀取完清理
        del reader
        del shape
        gc.collect()
        
        if not solids:
            log_message(log_path, "ERROR: No solids found.")
            return

        init_volumes = [get_shape_volume(s) for s in solids]
        total_init_vol = sum(init_volumes)
        
        for idx, vol in enumerate(init_volumes, 1):
            log_message(log_path, f"Volume solid {idx}: {vol:.6f}")
        log_message(log_path, f"Total initial volume: {total_init_vol:.6f}")

        if len(solids) == 1:
            final_result_shape = solids[0]
            log_message(log_path, "Single solid, skipping fusion")
            # 檢查初始是否為 Compound
            if final_result_shape.ShapeType() != TopAbs_SOLID:
                 unpacked = explore_solids(final_result_shape)
                 if len(unpacked) > 1:
                      log_message(log_path, f"!!! [MERGE FAILURE] Final Count: {len(unpacked)} (Initial Compound) !!!")
                      final_result_shape = pack_solids_into_one(unpacked, log_path)
        else:
            current_solids = solids[:]
            
            # 定義公差序列
            tolerances = [0.1, 0.12, 0.15, 0.18, 0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0, 1.25, 1.5, 2.0, 3.0, 5.0]
            
            for tol in tolerances:
                current_solids = run_greedy_merge_loop(
                    current_solids, 
                    tolerance=tol, 
                    log_path=log_path, 
                    pass_name=f"Fuse Pass (Tol {tol})"
                )
                
                if len(current_solids) == 1:
                    single_shape = current_solids[0]
                    if single_shape.ShapeType() == TopAbs_SOLID:
                        log_message(log_path, "SUCCESS: Merged into single SOLID during loop.")
                        break 
                    else:
                        # 拆解 Compound
                        unpacked = explore_solids(single_shape)
                        if len(unpacked) > 1:
                            log_message(log_path, f"Result is Compound of {len(unpacked)} parts. Exploding for next pass...")
                            current_solids = unpacked
                            gc.collect() # 拆解後清理一次
                        else:
                            break
            
            # =========================================================
            # 最終檢查與封裝
            # =========================================================
            final_count = len(current_solids)
            
            if final_count == 1:
                final_result_shape = current_solids[0]
                if final_result_shape.ShapeType() != TopAbs_SOLID:
                     real_parts = explore_solids(final_result_shape)
                     if len(real_parts) > 1:
                         log_message(log_path, f"!!! [MERGE FAILURE] Final Count: {len(real_parts)} (Compound remains) !!!")
                         final_result_shape = pack_solids_into_one(real_parts, log_path)
                     else:
                         log_message(log_path, f"*** [MERGE SUCCESS] Final Count: 1 ***")
                else:
                    log_message(log_path, f"*** [MERGE SUCCESS] Final Count: 1 ***")
            else:
                log_message(log_path, f"!!! [MERGE FAILURE] Final Count: {final_count} !!!")
                
                log_message(log_path, "Detailed unmerged parts:")
                current_solids.sort(key=lambda s: get_shape_volume(s), reverse=True)
                for idx, s in enumerate(current_solids):
                    vol_rem = get_shape_volume(s)
                    log_message(log_path, f"  - Part {idx+1}: Volume {vol_rem:.6f}")
                
                final_result_shape = pack_solids_into_one(current_solids, log_path)

        if final_result_shape is None:
            return

        vol_final = get_shape_volume(final_result_shape)
        log_message(log_path, f"Final Volume: {vol_final:.6f}")
        
        if total_init_vol > 0:
            ratio = vol_final / total_init_vol
            log_message(log_path, f"Volume Ratio: {ratio:.6f}")

        writer = STEPControl_Writer()
        writer.Transfer(final_result_shape, STEPControl_AsIs)
        if writer.Write(out_path) != 1:
            log_message(log_path, f"ERROR: Write failed: {out_path}")
        else:
            log_message(log_path, f"Saved to: {out_path}")

    except Exception as e:
        log_message(log_path, f"EXCEPTION: {e}")
        sys.stderr.write(traceback.format_exc())
    finally:
        # 最後再做一次完整清理
        gc.collect()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python transform_merge_fix.py <in> <out>")
    else:
        step_to_step(sys.argv[1], sys.argv[2])