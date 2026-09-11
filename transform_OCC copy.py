import sys
import os
import traceback
import gc

# PythonOCC Core Imports
from OCC.Core.STEPControl import STEPControl_Reader, STEPControl_Writer, STEPControl_AsIs
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Fuse
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeSolid
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_SOLID, TopAbs_SHELL, TopAbs_COMPOUND, TopAbs_REVERSED, TopAbs_FACE
from OCC.Core.TopoDS import topods_Solid, topods_Shell, TopoDS_Compound, TopoDS_Iterator, TopoDS_Face, TopoDS_Shell
from OCC.Core.BRep import BRep_Builder
from OCC.Core.TopTools import TopTools_ListOfShape, TopTools_ListIteratorOfListOfShape
from OCC.Core.BRepGProp import brepgprop
from OCC.Core.GProp import GProp_GProps
from OCC.Core.BRepBndLib import brepbndlib_Add
from OCC.Core.Bnd import Bnd_Box
from OCC.Core.BRepCheck import BRepCheck_Analyzer
# ShapeFix Imports
from OCC.Core.ShapeFix import ShapeFix_Shape, ShapeFix_Solid, ShapeFix_Shell, ShapeFix_Face
from OCC.Core.BRepExtrema import BRepExtrema_DistShapeShape
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Check

# 設定 Windows 下的輸出編碼
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

def log_message(log_path, message):
    try:
        print(message)
        sys.stdout.flush()
        with open(log_path, "a", encoding="utf-8") as log_file:
            log_file.write(message + "\n")
    except Exception:
        pass

# --- 幾何屬性工具 ---

def get_shape_volume(shape):
    if shape.IsNull(): return 0.0
    try:
        v_props = GProp_GProps()
        brepgprop.VolumeProperties(shape, v_props)
        return v_props.Mass()
    except:
        return 0.0

def is_valid_solid(shape):
    if shape.IsNull(): return False
    try:
        analyzer = BRepCheck_Analyzer(shape)
        return analyzer.IsValid()
    except:
        return False

def get_bounding_box(shape, tol=0.0):
    bbox = Bnd_Box()
    try:
        brepbndlib_Add(shape, bbox, False) 
        bbox.SetGap(tol)
    except:
        pass
    return bbox

def boxes_intersect(b1, b2):
    if b1.IsVoid() or b2.IsVoid(): return False
    return not b1.IsOut(b2)

# --- 核心工具 ---

def unpack_compound(shape):
    """ 遞迴拆解 Compound """
    shapes = []
    if shape.IsNull(): return shapes
    if shape.ShapeType() != TopAbs_COMPOUND:
        shapes.append(shape)
        return shapes
    it = TopoDS_Iterator(shape)
    while it.More():
        sub_shape = it.Value()
        if sub_shape.ShapeType() == TopAbs_COMPOUND:
            shapes.extend(unpack_compound(sub_shape))
        else:
            shapes.append(sub_shape)
        it.Next()
    return shapes
def is_safe_to_fuse(base_shape, tool_shape, tolerance):
    """
    幾何前置安檢：確認兩個形狀是否真的有接觸，且適合進行布林運算。
    回傳: (True/False, 判斷原因字串)
    """
    # 1. 精確距離檢查 (取代粗糙的 Bounding Box)
    try:
        extrema = BRepExtrema_DistShapeShape(base_shape, tool_shape)
        extrema.Perform()
        if extrema.IsDone():
            min_dist = extrema.Value()
            # 如果最短距離大於容差，代表根本沒碰到。丟進 Fuse 容易引發邊界誤判或無謂的運算。
            if min_dist > tolerance:
                return False, f"未接觸 (精確最短距離 {min_dist:.4f} > 容差 {tolerance})"
    except Exception as e:
        return False, f"距離計算失敗: {e}"

    # 2. 布林運算專用拓樸檢查
    try:
        # BRepAlgoAPI_Check 會深度掃描兩個形狀，確認是否有破面或自交
        checker = BRepAlgoAPI_Check(base_shape, tool_shape)
        checker.SetFuzzyValue(tolerance) # 同步你的容差設定
        if not checker.IsValid():
            return False, "BRepAlgoAPI_Check 判定為無效幾何或存在自交 (Self-Intersection)"
    except Exception as e:
        return False, f"拓樸檢查失敗: {e}"

    # 如果都通過，代表這是一個健康的交集條件
    return True, "Safe"
# --- Deep Heal (治本修復 - Clean Version) ---

def deep_heal_shape(shape, log_path=None):
    if shape.IsNull(): return shape
    
    # 0. 基礎檢查
    if is_valid_solid(shape):
        vol = get_shape_volume(shape)
        if vol > 0: return shape
        elif vol < 0: shape.Reverse(); return shape

    if log_path: log_message(log_path, "      [Deep Heal] Starting aggressive repair...")
    target_shape = shape
    vol = get_shape_volume(target_shape)
    if vol < 0: target_shape.Reverse()

    # 1. ShapeFix (使用預設配置，避免 API 錯誤)
    try:
        sfs = ShapeFix_Shape(target_shape)
        sfs.SetPrecision(0.1)
        sfs.SetMinTolerance(0.1)
        sfs.SetMaxTolerance(1.0)
        
        sf_solid = sfs.FixSolidTool()
        try: sf_solid.SetCreateOpenSolidMode(True) 
        except: pass
        
        sfs.Perform()
        fixed_sfs = sfs.Shape()
        if is_valid_solid(fixed_sfs) and get_shape_volume(fixed_sfs) > 1e-6:
            if log_path: log_message(log_path, "      [Deep Heal] ShapeFix success.")
            return fixed_sfs
        else:
            target_shape = fixed_sfs
    except Exception as e:
        if log_path: log_message(log_path, f"      [Deep Heal] ShapeFix error: {e}")

    # 2. 拓樸重建 (Topology Rebuild)
    try:
        if log_path: log_message(log_path, "      [Deep Heal] Attempting Topology Rebuild (Explode->Solid)...")
        faces = []
        exp = TopExp_Explorer(target_shape, TopAbs_FACE)
        while exp.More():
            faces.append(exp.Current())
            exp.Next()
        
        if not faces: return shape
        
        builder = BRep_Builder()
        new_shell = TopoDS_Shell() 
        builder.MakeShell(new_shell)
        for f in faces: builder.Add(new_shell, f)
            
        solid_maker = BRepBuilderAPI_MakeSolid()
        solid_maker.Add(new_shell)
        solid_maker.Build()
        
        if solid_maker.IsDone():
            rebuilt_solid = solid_maker.Solid()
            sfs_simple = ShapeFix_Shape(rebuilt_solid)
            sfs_simple.Perform()
            final_shape = sfs_simple.Shape()
            
            if get_shape_volume(final_shape) > 1e-6:
                if log_path: log_message(log_path, "      [Deep Heal] Rebuild success.")
                return final_shape
    except Exception as e:
        if log_path: log_message(log_path, f"      [Deep Heal] Rebuild error: {e}")

    if log_path: log_message(log_path, "      [Deep Heal] All methods failed. Returning best effort.")
    return target_shape

# --- Explore Solids (全收錄 + 詳細 Log) ---

def explore_solids(shape, log_path):
    solids = []
    stats = {"found": 0, "valid": 0, "zombie": 0}

    def process_candidate(new_solid, context=""):
        vol = get_shape_volume(new_solid)
        if vol <= 1e-6 and vol >= -1e-6: return

        final_solid = new_solid
        
        # 嘗試修復
        if not is_valid_solid(new_solid):
            log_message(log_path, f"    [WARNING] Invalid Geometry in {context}. Starting Deep Heal...")
            final_solid = deep_heal_shape(new_solid, log_path)

        if get_shape_volume(final_solid) < 0:
            final_solid.Reverse()

        for s in solids:
            if s.IsSame(final_solid): return
        
        stats["found"] += 1
        current_id = stats["found"]
        
        if is_valid_solid(final_solid):
            stats["valid"] += 1
        else:
            stats["zombie"] += 1
            log_message(log_path, f"      [ZOMBIE DETECTED] Part #{current_id} (from {context}) is INVALID but kept.")

        solids.append(final_solid)

    if shape.IsNull(): return []
    log_message(log_path, "  Starting geometry exploration (Keep All Strategy)...")

    if shape.ShapeType() == TopAbs_SOLID:
        process_candidate(topods_Solid(shape), "TopLevel Solid")

    if shape.ShapeType() == TopAbs_SHELL:
        shell = topods_Shell(shape)
        if shell.Orientation() != TopAbs_REVERSED:
            builder = BRepBuilderAPI_MakeSolid(shell)
            builder.Build()
            if builder.IsDone():
                process_candidate(builder.Solid(), "TopLevel Shell->Solid")

    if shape.ShapeType() == TopAbs_COMPOUND:
        exp_shell = TopExp_Explorer(shape, TopAbs_SHELL)
        while exp_shell.More():
            shell = topods_Shell(exp_shell.Current())
            if shell.Orientation() != TopAbs_REVERSED:
                builder = BRepBuilderAPI_MakeSolid(shell)
                builder.Build()
                if builder.IsDone():
                    process_candidate(builder.Solid(), "Compound Shell->Solid")
            exp_shell.Next()

        exp_all = TopExp_Explorer(shape, TopAbs_SOLID)
        while exp_all.More():
            process_candidate(topods_Solid(exp_all.Current()), "Compound Solid")
            exp_all.Next()
            
        exp_comp = TopExp_Explorer(shape, TopAbs_COMPOUND)
        while exp_comp.More():
            sub = exp_comp.Current()
            if not sub.IsEqual(shape):
                sub_exp = TopExp_Explorer(sub, TopAbs_SOLID)
                while sub_exp.More():
                    process_candidate(topods_Solid(sub_exp.Current()), "Recursive Compound Solid")
                    sub_exp.Next()
            exp_comp.Next()

    log_message(log_path, f"  [Explore Summary] Total: {len(solids)} (Valid: {stats['valid']}, Zombies: {stats['zombie']})")
    return solids

# --- Smart Fuse (Pure Fuse, No Cut, No Move) ---

def smart_fuse(base_shape, tools_list, tolerance, log_path):
    """
    純粹的智慧合併 (包含防坍縮機制)
    """
    # 1. 【關鍵修復】在最頂端初始化變數，確保絕對不會出現 UnboundLocalError
    leftovers = [] 
    current_base = base_shape
    
    # 提前計算初始體積，供後續防護機制使用
    initial_base_vol = get_shape_volume(current_base)

    # --- 第一階段：全梭 (All-in) ---
    if len(tools_list) < 5:
        try:
            fuse_algo = BRepAlgoAPI_Fuse()
            base_args = TopTools_ListOfShape(); base_args.Append(current_base)
            fuse_algo.SetArguments(base_args)
            
            occ_tools = TopTools_ListOfShape()
            for t in tools_list: occ_tools.Append(t)
            fuse_algo.SetTools(occ_tools)
            
            fuse_algo.SetFuzzyValue(tolerance)
            fuse_algo.SetRunParallel(True)
            fuse_algo.SetUseOBB(True)
            fuse_algo.Build()
            
            if fuse_algo.IsDone():
                res = fuse_algo.Shape()
                new_vol = get_shape_volume(res)
                # 全梭防坍縮機制：體積不能小於原本的 80%
                if new_vol > 1e-6 and new_vol >= initial_base_vol * 0.8:
                    return res, [] # 成功全梭，無殘留
        except Exception as e:
            pass # 全梭失敗或報錯，默默進入第二階段

    # --- 第二階段：分級合併 (Incremental) ---
    log_message(log_path, "       [Smart Fuse] Switching to Incremental Mode (Pure Fuse)...")
    
    valid_tools = []
    zombie_tools = []
    for t in tools_list:
        if is_valid_solid(t): valid_tools.append(t)
        else: zombie_tools.append(t)
        
    log_message(log_path, f"       [Smart Fuse] Valid Tools: {len(valid_tools)}, Zombie Tools: {len(zombie_tools)}")

    # 處理 Valid Tools
    for i, tool in enumerate(valid_tools):
        # 🟢 新增：進度提示，讓你知道程式沒死，而且卡在哪一個
        log_message(log_path, f"       [Incremental] Fusing valid tool {i+1}/{len(valid_tools)}...") 
        try:
            fuse_algo = BRepAlgoAPI_Fuse()
            base_args = TopTools_ListOfShape(); base_args.Append(current_base)
            tool_args = TopTools_ListOfShape(); tool_args.Append(tool)
            fuse_algo.SetArguments(base_args)
            fuse_algo.SetTools(tool_args)
            fuse_algo.SetFuzzyValue(tolerance)
            fuse_algo.SetRunParallel(True) # 🟢 新增：開啟多執行緒加速
            fuse_algo.Build()
            # ... 下面的邏輯保持不變 ...
            
            if fuse_algo.IsDone():
                res = fuse_algo.Shape()
                new_vol = get_shape_volume(res)
                current_base_vol = get_shape_volume(current_base)
                
                # 增量防坍縮機制
                if new_vol > 1e-6 and new_vol >= current_base_vol * 0.8:
                    current_base = res
                else:
                    # 拓樸損毀，退回不合併
                    leftovers.append(tool) 
            else:
                leftovers.append(tool)
        except:
            leftovers.append(tool)

    # 處理 Zombie Tools
    for i, zombie in enumerate(zombie_tools):
        try:
            fuse_algo = BRepAlgoAPI_Fuse()
            base_args = TopTools_ListOfShape(); base_args.Append(current_base)
            tool_args = TopTools_ListOfShape(); tool_args.Append(zombie)
            fuse_algo.SetArguments(base_args)
            fuse_algo.SetTools(tool_args)
            fuse_algo.SetFuzzyValue(tolerance)
            fuse_algo.Build()
            
            if fuse_algo.IsDone():
                res = fuse_algo.Shape()
                new_vol = get_shape_volume(res)
                current_base_vol = get_shape_volume(current_base)
                
                if new_vol > 1e-6 and new_vol >= current_base_vol * 0.8:
                    current_base = res
                else:
                    leftovers.append(zombie)
            else:
                leftovers.append(zombie)
        except:
            leftovers.append(zombie)

    # 確保迴圈全部跑完後，統一回傳最終的 Base 與剩下的殘骸
    return current_base, leftovers

def batch_fuse_solids(shapes_list, tolerance, log_path):
    if not shapes_list: return [], False
    if len(shapes_list) == 1: return shapes_list, False

    shapes_list.sort(key=lambda s: get_shape_volume(s), reverse=True)
    
    remaining_shapes = shapes_list[:]
    output_list = []
    merge_happened = False

    while len(remaining_shapes) > 0:
        base_shape = remaining_shapes.pop(0)
        base_vol = get_shape_volume(base_shape)
        base_bbox = get_bounding_box(base_shape, tolerance)
        
        tools_to_fuse = []
        next_round_shapes = []
        
        for other in remaining_shapes:
            other_bbox = get_bounding_box(other, tolerance)
            if boxes_intersect(base_bbox, other_bbox):
                tools_to_fuse.append(other)
                base_bbox.Add(other_bbox)
            else:
                next_round_shapes.append(other)
        
        if tools_to_fuse:
            merge_happened = True
            vol = get_shape_volume(base_shape)
            log_message(log_path, f"    Fusing Group: Base(Vol={vol:.2f}) + {len(tools_to_fuse)} parts... (Tol={tolerance})")
            
            # 呼叫純粹的 Smart Fuse (回傳 Base 和 沒合成功的 Leftovers)
            result, leftovers = smart_fuse(base_shape, tools_to_fuse, tolerance, log_path)
            
            output_list.append(result)
            
            # 將失敗的零件保留下來
            if leftovers:
                log_message(log_path, f"      [Info] {len(leftovers)} parts failed to merge and are kept separate.")
                output_list.extend(leftovers)
        else:
            output_list.append(base_shape)
            
        remaining_shapes = next_round_shapes
    
    return output_list, merge_happened

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
        status = reader.ReadFile(in_path)
        if status != 1:
            log_message(log_path, "ERROR: Read STEP failed")
            return
        
        reader.TransferRoots()
        root_shape = reader.OneShape()
        
        current_shapes = explore_solids(root_shape, log_path)
        
        del reader, root_shape
        gc.collect()

        log_message(log_path, f"Initial Valid Parts: {len(current_shapes)}")
        
        if len(current_shapes) == 0:
            log_message(log_path, "ERROR: No valid geometry found.")
            return

        tolerances = [0.1, 0.5, 1.0, 2.0]
        
        for tol in tolerances:
            # 假合併檢查 (Before Pass)
            if len(current_shapes) == 1:
                unpacked_check = unpack_compound(current_shapes[0])
                if len(unpacked_check) <= 1:
                    log_message(log_path, "Already fully merged into single object. Stopping loop.")
                    break
                else:
                    log_message(log_path, f"  [Check] Input is a Compound containing {len(unpacked_check)} items. (Continuing to merge...)")
                    current_shapes = unpacked_check

            log_message(log_path, f"--- Starting Pass (Tol={tol}) with {len(current_shapes)} parts ---")
            new_shapes, changed = batch_fuse_solids(current_shapes, tol, log_path)
            
            # 假合併檢查 (After Pass)
            if len(new_shapes) == 1:
                unpacked_result = unpack_compound(new_shapes[0])
                if len(unpacked_result) > 1:
                    log_message(log_path, f"  [Result Check] Still disjoint (Compound of {len(unpacked_result)} items). Need higher tolerance.")
                    current_shapes = new_shapes
                else:
                    log_message(log_path, "  SUCCESS: Real merge achieved (Single Object).")
                    current_shapes = new_shapes
                    break 
            else:
                current_shapes = new_shapes
            
            gc.collect()

        final_shape = None
        if len(current_shapes) == 1:
            unpacked_final = unpack_compound(current_shapes[0])
            if len(unpacked_final) > 1:
                log_message(log_path, f"WARNING: Final result is a Compound of {len(unpacked_final)} separate items.")
                final_shape = current_shapes[0]
            else:
                final_shape = current_shapes[0]
        else:
            log_message(log_path, f"Result contains {len(current_shapes)} disjoint groups. Packing into Compound.")
            final_shape = pack_into_compound(current_shapes)

        if is_valid_solid(final_shape):
            log_message(log_path, "[FINAL STATUS] The output geometry is VALID (Healthy).")
        else:
            log_message(log_path, "[FINAL STATUS] The output geometry is INVALID (Zombie/Partial).")

        log_message(log_path, "Writing STEP file...")
        writer = STEPControl_Writer()
        writer.Transfer(final_shape, STEPControl_AsIs)
        
        out_dir = os.path.dirname(out_path)
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir)

        if writer.Write(out_path) != 1:
            log_message(log_path, f"ERROR: Write failed: {out_path}")
        else:
            log_message(log_path, f"Saved to: {out_path}")

    except Exception as e:
        log_message(log_path, f"EXCEPTION: {e}")
        sys.stderr.write(traceback.format_exc())

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python step_merge_tool.py <input.step> <output.step>")
    else:
        step_to_step(sys.argv[1], sys.argv[2])