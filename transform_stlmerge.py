import sys
import numpy as np
import trimesh
import os
from datetime import datetime

# 設定環境變數，確保 PyVista 在背景執行時不會卡住
os.environ["PYVISTA_OFF_SCREEN"] = "true"
os.environ["PV_ALLOW_BATCHED_INTERACTION"] = "true"

# 嘗試匯入 PyVista
try:
    import pyvista as pv
    HAS_PYVISTA = True
    pv.OFF_SCREEN = True
except ImportError:
    HAS_PYVISTA = False

# =================設定區=================
LOG_FILE = "merge_report.txt"
# =======================================

def log_to_file(input_name, original_count, final_count, note, status):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {input_name} | Orig:{original_count} -> Final:{final_count} | Note:{note} | {status}\n")
    except:
        pass

def get_true_count(mesh):
    """
    使用 PyVista (VTK) 精確計算連通組件數量。
    """
    if HAS_PYVISTA:
        try:
            # 轉為 PyVista 物件
            pv_mesh = pv.wrap(mesh)
            
            # 確保是 PolyData
            if not isinstance(pv_mesh, pv.PolyData):
                pv_mesh = pv_mesh.extract_geometry()
            
            # 使用 connectivity 濾鏡計算連通區域
            bodies = pv_mesh.split_bodies()
            return len(bodies)
        except Exception:
            return len(mesh.split())
    else:
        return len(mesh.split())

def pyvista_stitch(mesh, tolerance=0.01):
    """
    使用 PyVista 進行縫合。
    """
    if not HAS_PYVISTA:
        return mesh

    try:
        print(f"   [VTK] Stitching (tol={tolerance}mm)...", end="", flush=True)
        pv_mesh = pv.wrap(mesh)
        
        # absolute=True 確保 tolerance 單位是 mm
        cleaned = pv_mesh.clean(point_merging=True, tolerance=tolerance, absolute=True)
        
        if not cleaned.is_all_triangles:
            cleaned = cleaned.triangulate()
            
        if cleaned.n_faces > 0:
            try:
                faces = cleaned.faces.reshape(-1, 4)[:, 1:]
                print(" Done.", flush=True)
                return trimesh.Trimesh(vertices=cleaned.points, faces=faces)
            except:
                cleaned = cleaned.triangulate()
                faces = cleaned.faces.reshape(-1, 4)[:, 1:]
                print(" Done (Retry).", flush=True)
                return trimesh.Trimesh(vertices=cleaned.points, faces=faces)
        else:
            return mesh
    except Exception as e:
        print(f" Error: {e}", flush=True)
        return mesh

def trimesh_aggressive_snap(mesh, grid_size):
    """
    Trimesh 暴力鎖點：
    直接對座標進行 grid_size 的量化，強制把附近的點吸到網格點上。
    這對於 VTK clean 無法處理的破爛網格很有效。
    """
    print(f"   [Trimesh] Aggressive Snap (Grid={grid_size}mm)...", end="", flush=True)
    temp = mesh.copy()
    
    # 使用整數化運算來鎖點： round(x / grid) * grid
    if grid_size > 0:
        temp.vertices = np.round(temp.vertices / grid_size) * grid_size
    
    # 合併頂點
    temp.merge_vertices()
    print(" Done.", flush=True)
    return temp

def pyvista_pipeline(input_path, output_path):
    print(f"Loading: {input_path}", flush=True)
    
    # 1. 載入檔案
    try:
        mesh = trimesh.load(input_path, force='mesh', process=False)
    except:
        try:
            scene = trimesh.load(input_path, force='scene', process=False)
            geoms = [g for g in scene.geometry.values() if hasattr(g, 'vertices')]
            mesh = trimesh.util.concatenate(geoms) if geoms else trimesh.Trimesh()
        except:
            return

    if isinstance(mesh, trimesh.Scene):
        mesh = trimesh.util.concatenate(tuple(mesh.geometry.values()))

    # 檢查空檔
    if len(mesh.vertices) == 0:
        log_to_file(os.path.basename(input_path), 0, 0, "Empty Input", "ERROR")
        return

    # 2. 初始狀態檢測
    print("Analyzing topology...", flush=True)
    # 基礎合併，消除轉檔造成的微小浮點數誤差
    mesh.merge_vertices()
    
    orig_count = get_true_count(mesh)
    if orig_count == 0 and len(mesh.vertices) > 0: orig_count = 1
    
    print(f"Original Connected Components: {orig_count}", flush=True)

    final_mesh = None
    operation_mode = "N/A"
    success_merged = False

    # =========================================================
    # 策略 1: PyVista (VTK) 高速縫合
    # =========================================================
    if HAS_PYVISTA:
        print("--- Mode: PyVista (VTK) Stitching ---", flush=True)
        
        # 如果原本就是 1 個，直接保留
        if orig_count == 1:
            print(" -> Single component detected. Preserving...", flush=True)
            final_mesh = mesh
            operation_mode = "Original Preserved"
            success_merged = True
        else:
            # 容差等級 (mm)
            tolerances = [0.01, 0.1, 0.5, 1.0, 5.0, 10.0, 20.0, 50.0]
            
            for tol in tolerances:
                temp_mesh = pyvista_stitch(mesh, tolerance=tol)
                
                current_count = get_true_count(temp_mesh)
                print(f" -> Result: {current_count} parts", flush=True)
                
                if current_count == 1:
                    final_mesh = temp_mesh
                    operation_mode = f"PV Stitched (Tol={tol}mm)"
                    print(" -> Success! Merged into one.", flush=True)
                    success_merged = True
                    break
                elif current_count < orig_count:
                    # 進步了但還沒完，暫存
                    final_mesh = temp_mesh
                    operation_mode = f"PV Partial (Tol={tol}mm)"
                elif final_mesh is None:
                    final_mesh = temp_mesh
                    operation_mode = f"PV BestEffort (Tol={tol}mm)"

    else:
        print("Warning: PyVista not found. Skipping VTK stage.", flush=True)

    # =========================================================
    # 策略 2: Trimesh 暴力鎖點 (Fallback)
    # 如果 PyVista 縫合失敗 (仍大於 1 件)，使用 Trimesh 嘗試暴力合併
    # =========================================================
    if not success_merged and orig_count > 1:
        print("--- Mode: Trimesh Aggressive Snap (Fallback) ---", flush=True)
        print(" -> VTK failed to merge completely. Switching to geometry snapping...", flush=True)
        
        # 使用目前的最佳結果作為起點，或者原始網格
        base_for_snap = final_mesh if final_mesh is not None else mesh
        
        # 網格尺寸等級 (mm)
        # 從 1mm 開始，如果不夠就加大到 5mm, 10mm
        # 注意：這會改變幾何精度，但能強行合併
        grid_sizes = [1.0, 2.0, 5.0, 10.0]
        
        for grid in grid_sizes:
            temp_mesh = trimesh_aggressive_snap(base_for_snap, grid_size=grid)
            
            current_count = get_true_count(temp_mesh)
            print(f" -> Result: {current_count} parts", flush=True)
            
            if current_count == 1:
                final_mesh = temp_mesh
                operation_mode = f"Trimesh Snap (Grid={grid}mm)"
                print(" -> Success! Forced merge.", flush=True)
                success_merged = True
                break
            elif final_mesh is None:
                 final_mesh = temp_mesh
                 operation_mode = f"Trimesh Partial (Grid={grid}mm)"

    # =========================================================
    # 存檔
    # =========================================================
    if final_mesh is None:
        final_mesh = mesh
        operation_mode = "Raw Backup"

    try:
        print("Finalizing mesh...", flush=True)
        final_mesh.fix_normals()
        
        final_c = get_true_count(final_mesh)
        if final_c == 0: final_c = 1
        
        print(f"Exporting to {output_path} (Final Count: {final_c})", flush=True)
        final_mesh.export(output_path)
        
        status = "SUCCESS" if final_c == 1 else "WARNING"
        if final_c > 1: status += " (Split)"
        
        log_to_file(os.path.basename(input_path), orig_count, final_c, operation_mode, status)
        
    except Exception as e:
        print(f"Save Failed: {e}", flush=True)
        try:
            mesh.export(output_path)
        except:
            pass

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python transform_stlmerge.py <input.stl> <output.stl>")
    else:
        pyvista_pipeline(sys.argv[1], sys.argv[2])