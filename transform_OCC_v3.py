import sys
import os
import traceback
import gc
import math

# PythonOCC Core Imports
from OCC.Core.STEPControl import STEPControl_Reader, STEPControl_Writer, STEPControl_AsIs
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Fuse
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeSolid
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_SOLID, TopAbs_SHELL, TopAbs_COMPOUND, TopAbs_REVERSED, TopAbs_FACE
from OCC.Core.TopoDS import topods_Solid, topods_Shell, TopoDS_Compound, TopoDS_Iterator
from OCC.Core.BRep import BRep_Builder
from OCC.Core.TopTools import TopTools_ListOfShape, TopTools_ListIteratorOfListOfShape
from OCC.Core.BRepGProp import brepgprop
from OCC.Core.GProp import GProp_GProps
from OCC.Core.BRepBndLib import brepbndlib_Add
from OCC.Core.Bnd import Bnd_Box
from OCC.Core.BRepCheck import BRepCheck_Analyzer
# 引入治本需要的修復工具
from OCC.Core.ShapeFix import ShapeFix_Shape, ShapeFix_Solid, ShapeFix_Face
from OCC.Core.ShapeUpgrade import ShapeUpgrade_UnifySameDomain
from OCC.Core.Precision import precision
from OCC.Core.BRep import BRep_Builder
from OCC.Core.TopoDS import TopoDS_Shell, TopoDS_Face
from OCC.Core.ShapeFix import ShapeFix_Shape, ShapeFix_Solid, ShapeFix_Shell, ShapeFix_Face

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

# --- 核心：治本修復函數 (Deep Healing) ---

def deep_heal_shape(shape, log_path=None):
    """
    深度修復函數：最終 Clean 版。
    移除導致 Attribute Error 的特定參數設定，依賴 Perform 的預設行為。
    """
    if shape.IsNull(): return shape
    
    # 0. 基礎檢查
    if is_valid_solid(shape):
        vol = get_shape_volume(shape)
        if vol > 0:
            return shape
        elif vol < 0:
            shape.Reverse()
            return shape

    if log_path: log_message(log_path, "      [Deep Heal] Starting aggressive repair...")

    target_shape = shape
    
    # 1. 嘗試反轉負體積
    vol = get_shape_volume(target_shape)
    if vol < 0:
        target_shape.Reverse()

    # 2. 使用 ShapeFix_Shape
    try:
        sfs = ShapeFix_Shape(target_shape)
        sfs.SetPrecision(0.1)
        sfs.SetMinTolerance(0.1)
        sfs.SetMaxTolerance(1.0)
        
        # 針對 Solid 的修復
        # 移除 SetFixShell (因為 API 版本不一)，只設定 CreateOpenSolidMode
        sf_solid = sfs.FixSolidTool()
        try:
            sf_solid.SetCreateOpenSolidMode(True) 
        except:
            pass # 如果連這個都沒有，就跳過
        
        sfs.Perform()
        fixed_sfs = sfs.Shape()
        
        if is_valid_solid(fixed_sfs) and get_shape_volume(fixed_sfs) > 1e-6:
            if log_path: log_message(log_path, "      [Deep Heal] ShapeFix success.")
            return fixed_sfs
        else:
            target_shape = fixed_sfs
    except Exception as e:
        if log_path: log_message(log_path, f"      [Deep Heal] ShapeFix error: {e}")

    # 3. 拓樸重建 (Topology Rebuild)
    try:
        if log_path: log_message(log_path, "      [Deep Heal] Attempting Topology Rebuild (Explode->Solid)...")
        
        faces = []
        exp = TopExp_Explorer(target_shape, TopAbs_FACE)
        while exp.More():
            faces.append(exp.Current())
            exp.Next()
            
        if not faces: return shape
        
        # 使用 BRep_Builder 手動構建 Shell
        builder = BRep_Builder()
        new_shell = TopoDS_Shell() 
        builder.MakeShell(new_shell)
        
        for f in faces:
            builder.Add(new_shell, f)
            
        # 再做 Solid
        solid_maker = BRepBuilderAPI_MakeSolid()
        solid_maker.Add(new_shell)
        solid_maker.Build()
        
        if solid_maker.IsDone():
            rebuilt_solid = solid_maker.Solid()
            
            # 重建後做簡單修復
            sfs_simple = ShapeFix_Shape(rebuilt_solid)
            sfs_simple.Perform()
            final_shape = sfs_simple.Shape()
            
            # 只要有體積就算成功，不管 Valid 與否
            if get_shape_volume(final_shape) > 1e-6:
                if log_path: log_message(log_path, "      [Deep Heal] Rebuild success.")
                return final_shape
    except Exception as e:
        if log_path: log_message(log_path, f"      [Deep Heal] Rebuild error: {e}")

    if log_path: log_message(log_path, "      [Deep Heal] All methods failed. Returning best effort.")
    return target_shape

# --- 讀取與探索 ---

def explore_solids(shape, log_path):
    """
    使用 deep_heal_shape 進行治本修復
    """
    solids = []
    
    stats = {
        "solid_found": 0,
        "shell_converted": 0,
        "rejected_small": 0,
        "healed": 0,
        "failed_heal": 0,
        "rejected_duplicate": 0
    }

    def process_candidate(new_solid, context=""):
        # 1. 體積檢查 (極小雜訊直接丟)
        vol = get_shape_volume(new_solid)
        if vol <= 1e-6 and vol >= -1e-6: # 絕對值很小
            stats["rejected_small"] += 1
            return

        # 2. 深度修復 (治本關鍵)
        # 不管它現在是好是壞，只要它是無效的，就進去修
        final_solid = new_solid
        if not is_valid_solid(new_solid):
            log_message(log_path, f"    [WARNING] Invalid Geometry in {context}. Starting Deep Heal...")
            final_solid = deep_heal_shape(new_solid, log_path)
            
            if is_valid_solid(final_solid):
                stats["healed"] += 1
            else:
                stats["failed_heal"] += 1
                log_message(log_path, "      -> Deep Heal finished but shape still Invalid (kept as is).")
        
        # 3. 確保體積為正 (最後防線)
        if get_shape_volume(final_solid) < 0:
            final_solid.Reverse()

        # 4. 重複檢查
        for s in solids:
            if s.IsSame(final_solid):
                stats["rejected_duplicate"] += 1
                return
        
        solids.append(final_solid)

    if shape.IsNull(): return solids

    log_message(log_path, "  Starting geometry exploration with Deep Heal...")

    # 1. Solid
    if shape.ShapeType() == TopAbs_SOLID:
        stats["solid_found"] += 1
        process_candidate(topods_Solid(shape), "TopLevel Solid")

    # 2. Shell
    if shape.ShapeType() == TopAbs_SHELL:
        shell = topods_Shell(shape)
        if shell.Orientation() != TopAbs_REVERSED:
            builder = BRepBuilderAPI_MakeSolid(shell)
            builder.Build()
            if builder.IsDone():
                stats["shell_converted"] += 1
                process_candidate(builder.Solid(), "TopLevel Shell->Solid")

    # 3. Compound
    if shape.ShapeType() == TopAbs_COMPOUND:
        log_message(log_path, "  Entering Compound...")
        
        # Shells inside Compound
        exp_shell = TopExp_Explorer(shape, TopAbs_SHELL)
        while exp_shell.More():
            shell = topods_Shell(exp_shell.Current())
            if shell.Orientation() != TopAbs_REVERSED:
                builder = BRepBuilderAPI_MakeSolid(shell)
                builder.Build()
                if builder.IsDone():
                    stats["shell_converted"] += 1
                    process_candidate(builder.Solid(), "Compound Shell->Solid")
            exp_shell.Next()

        # Solids inside Compound
        exp_all = TopExp_Explorer(shape, TopAbs_SOLID)
        while exp_all.More():
            stats["solid_found"] += 1
            process_candidate(topods_Solid(exp_all.Current()), "Compound Solid")
            exp_all.Next()
            
        # Recursive Compounds
        exp_comp = TopExp_Explorer(shape, TopAbs_COMPOUND)
        while exp_comp.More():
            sub = exp_comp.Current()
            if not sub.IsEqual(shape):
                # 這裡簡單遞迴，不再重複 unpack_compound 的邏輯
                sub_exp = TopExp_Explorer(sub, TopAbs_SOLID)
                while sub_exp.More():
                    process_candidate(topods_Solid(sub_exp.Current()), "Recursive Compound Solid")
                    sub_exp.Next()
            exp_comp.Next()

    log_message(log_path, f"  [Explore Summary] Found: {len(solids)} Parts.")
    log_message(log_path, f"  [Explore Stats] Healed: {stats['healed']}, Still Invalid: {stats['failed_heal']}")
    
    # 孤注一擲：如果沒有任何 Valid 的，但有 Invalid 的，就全部回傳
    # 但因為我們上面已經把所有東西(無論好壞)都 append 進 solids 了，所以這裡不需要額外邏輯
    # 只要 solids 不為空，就不會報 Error: No valid geometry found
    
    return solids

# --- 寬鬆合併 (維持不變) ---

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
        
        tools_to_fuse = TopTools_ListOfShape()
        next_round_shapes = []
        
        for other in remaining_shapes:
            other_bbox = get_bounding_box(other, tolerance)
            if boxes_intersect(base_bbox, other_bbox):
                tools_to_fuse.Append(other)
                base_bbox.Add(other_bbox)
            else:
                next_round_shapes.append(other)
        
        if tools_to_fuse.Size() > 0:
            merge_happened = True
            vol = get_shape_volume(base_shape)
            log_message(log_path, f"    Fusing Group: Base(Vol={vol:.2f}) + {tools_to_fuse.Size()} parts... (Tol={tolerance})")
            
            try:
                fuse_algo = BRepAlgoAPI_Fuse()
                base_args = TopTools_ListOfShape()
                base_args.Append(base_shape)
                fuse_algo.SetArguments(base_args)
                fuse_algo.SetTools(tools_to_fuse)
                fuse_algo.SetFuzzyValue(tolerance)
                fuse_algo.SetRunParallel(True)
                fuse_algo.SetUseOBB(True)
                
                fuse_algo.Build()
                
                if fuse_algo.IsDone():
                    result = fuse_algo.Shape()
                    res_vol = get_shape_volume(result)
                    
                    if res_vol <= 1e-6:
                         log_message(log_path, "      [REJECT] Volume became Zero. Keeping separate.")
                         output_list.append(base_shape)
                         it = TopTools_ListIteratorOfListOfShape(tools_to_fuse)
                         while it.More():
                            output_list.append(it.Value())
                            it.Next()
                    else:
                        output_list.append(result)
                else:
                    log_message(log_path, "    WARNING: Fuse failed (Algo error). Keeping separate.")
                    output_list.append(base_shape)
                    it = TopTools_ListIteratorOfListOfShape(tools_to_fuse)
                    while it.More():
                        output_list.append(it.Value())
                        it.Next()
            except Exception as e:
                log_message(log_path, f"    ERROR inside Fuse: {e}")
                output_list.append(base_shape)
                it = TopTools_ListIteratorOfListOfShape(tools_to_fuse)
                while it.More():
                    next_round_shapes.append(it.Value())
                    it.Next()
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
            if len(current_shapes) <= 1:
                log_message(log_path, "Merged into single object. Stopping loop.")
                break

            log_message(log_path, f"--- Starting Pass (Tol={tol}) with {len(current_shapes)} parts ---")
            new_shapes, changed = batch_fuse_solids(current_shapes, tol, log_path)
            
            current_shapes = new_shapes
            gc.collect()

        final_shape = None
        if len(current_shapes) == 1:
            final_shape = current_shapes[0]
            log_message(log_path, "SUCCESS: Single object result.")
        else:
            log_message(log_path, f"Result contains {len(current_shapes)} disjoint groups. Packing into Compound.")
            final_shape = pack_into_compound(current_shapes)

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