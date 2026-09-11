import sys
import os
import open3d as o3d
import numpy as np
import h5py 
import traceback
import copy

# Load the pc_skeletor library
try:
    from pc_skeletor import LBC
except Exception as e:
    print("\n" + "="*30)
    print("!!! DETAILED ERROR !!!")
    print(f"Error message: {e}")
    print("-" * 20)
    traceback.print_exc()  
    print("="*30 + "\n")
    print("Error: 'pc_skeletor' library not found.")
    sys.exit(1)

def load_point_cloud(in_path):
    """
    Loads a point cloud file based on its extension (.ply, .pcd, .npz, .h5).
    Returns an open3d.geometry.PointCloud object.
    """
    if not os.path.exists(in_path):
        print(f"Error: Input file not found {in_path}")
        return None

    ext = os.path.splitext(in_path)[1].lower()
    pcd = o3d.geometry.PointCloud() 

    try:
        if ext in ['.ply', '.pcd', '.xyz']:
            pcd = o3d.io.read_point_cloud(in_path)
            if not pcd.has_points():
                print(f"Error: File {in_path} failed to load or contains no points.")
                return None
                
        elif ext == '.npz':
            data = np.load(in_path)
            if 'point_cloud' not in data:
                print(f"Error: 'point_cloud' key not found in .npz file.")
                return None
            points = data['point_cloud']
            pcd.points = o3d.utility.Vector3dVector(points)

        elif ext == '.h5':
            with h5py.File(in_path, 'r') as hf:
                if 'point_cloud' not in hf:
                    print(f"Error: 'point_cloud' dataset not found in .h5 file.")
                    return None
                points = np.array(hf['point_cloud'])
                pcd.points = o3d.utility.Vector3dVector(points)
        
        else:
            print(f"Error: Unsupported file format {ext}")
            return None
            
        return pcd

    except Exception as e:
        print(f"An error occurred while loading point cloud {in_path}: {e}")
        return None


def skeletonize(in_path, out_folder, down_sample=0.01):
    """
    Loads a point cloud file, corrects normals, performs LBC skeleton extraction, and saves results.
    Includes Coordinate Normalization to prevent boundary issues.
    """
    print(f"--- Starting to process point cloud: {in_path} ---")

    # --- 1. Load Point Cloud ---
    print(f"Loading point cloud...")
    pcd = load_point_cloud(in_path)

    if pcd is None:
        return 

    print(f"Load successful, {len(pcd.points)} points found.")

    # ============================================================
    # ★★★ 修正重點 1：歸一化 (Normalization) ★★★
    # 將點雲移動到 (0,0,0) 並縮放到單位球內 (Unit Sphere)
    # 這能解決「超出邊界」和數值爆炸的問題
    # ============================================================
    print("Performing coordinate normalization...")
    original_center = pcd.get_center()
    pcd.translate(-original_center) # 移到原點

    # 計算最大距離，用於縮放
    points_np = np.asarray(pcd.points)
    max_dist = np.max(np.linalg.norm(points_np, axis=1))
    if max_dist == 0: max_dist = 1.0 # 防止除以零
    
    pcd.scale(1.0 / max_dist, center=(0,0,0)) # 縮放到 [-1, 1] 之間
    print(f"Normalization done. Scale factor: {1.0/max_dist:.4f}")


    # ============================================================
    # 前處理 (Preprocessing)
    # ============================================================
    
    # A. 去除雜訊 (Remove Outliers)
    print("Removing statistical outliers (reducing noise)...")
    # 先存原始數量以便比較
    original_count = len(pcd.points)
    pcd, ind = pcd.remove_statistical_outlier(nb_neighbors=20, std_ratio=2.0)
    print(f"Points after denoising: {len(pcd.points)} (Removed {original_count - len(pcd.points)})")

    # B. 估計法向量 (Estimate Normals)
    print("Estimating normals...")
    # 因為已經歸一化了，這裡的 search_radius 不需要太大，down_sample 也不需要太大
    # 注意：這裡的 down_sample 參數也應該是針對歸一化後的尺度
    search_radius = down_sample * 5 
    if search_radius < 0.02: search_radius = 0.02 # 歸一化後的最小保護值

    pcd.estimate_normals(
        search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=search_radius, max_nn=30)
    )

    # C. 統一法向量方向 (Orient Normals)
    print("Orienting normals consistent tangent plane...")
    pcd.orient_normals_consistent_tangent_plane(k=15)


    # --- 2. Initialize LBC ---
    print(f"Initializing LBC with down_sample={down_sample}...")
    
    try:
        # 這裡傳入歸一化後的 pcd
        lbc = LBC(point_cloud=pcd, down_sample=down_sample)
    except Exception as e:
        print(f"LBC Initialization failed: {e}")
        return

    # --- 3. Perform Skeleton Extraction ---
    print("Extracting skeleton (extract_skeleton)...")
    try:
        lbc.extract_skeleton()
        print("Extracting topology (extract_topology)...")
        lbc.extract_topology()
    except Exception as e:
        print(f"Error during extraction process: {e}")
        traceback.print_exc()
        return

    # ============================================================
    # ★★★ 修正重點 2：還原座標 (Denormalization) ★★★
    # 將算出來的骨架和拓撲還原回原始的大小和位置
    # ============================================================
    print("Restoring coordinates to original scale...")
    
    # 1. 還原骨架點 (Skeleton)
    if hasattr(lbc, 'skeleton') and lbc.skeleton is not None:
        lbc.skeleton.scale(max_dist, center=(0,0,0)) # 放大回去
        lbc.skeleton.translate(original_center)      # 移回原位

    # 2. 還原拓撲線段 (Topology)
    if hasattr(lbc, 'topology') and lbc.topology is not None:
        lbc.topology.scale(max_dist, center=(0,0,0)) # 放大回去
        lbc.topology.translate(original_center)      # 移回原位


    # --- 4. Export Results ---
    os.makedirs(out_folder, exist_ok=True)
    print(f"Exporting results to {out_folder}...")
    
    try:
        skel_file = os.path.join(out_folder, 'skeleton.pcd')
        topo_file = os.path.join(out_folder, 'topology.ply')

        # Save the Skeleton (PointCloud)
        if hasattr(lbc, 'skeleton') and lbc.skeleton is not None:
            o3d.io.write_point_cloud(skel_file, lbc.skeleton)
            print(f"Skeleton file saved: {skel_file}")
        else:
            print("Error: lbc.skeleton is empty or does not exist.")

        # Save the Topology (LineSet)
        if hasattr(lbc, 'topology') and lbc.topology is not None:
            lines = np.asarray(lbc.topology.lines)
            if lines.shape[0] > 0:
                o3d.io.write_line_set(topo_file, lbc.topology)
                print(f"Topology file saved: {topo_file} (Lines count: {lines.shape[0]})")
            else:
                print(f"Warning: Topology generated but has 0 lines. (Try increasing down_sample slightly)")
        else:
            print("Warning: lbc.topology is empty.")

        print("--- Processing complete ---")

    except Exception as e:
        print(f"An error occurred while exporting results manually: {e}")
        traceback.print_exc()

def main():
    """
    Usage: python skeletonize_fixed.py <in_path> <out_folder> [down_sample]
    """
    if len(sys.argv) < 3:
        print("Usage: python skeletonize_fixed.py <in_path> <out_folder> [down_sample]")
        print("\n  <in_path>:      Input point cloud file")
        print("  <out_folder>:   Folder to save the results")
        print("  [down_sample]:  (Optional) Default is 0.005 (in normalized unit space)")
        sys.exit(1)

    in_path = sys.argv[1]
    out_folder = sys.argv[2]
    
    # 由於我們做了歸一化，0.005 代表是整個物體尺寸的 0.5%，這是一個很安全的數值
    down_sample = 0.005 

    if len(sys.argv) > 3:
        try:
            down_sample = float(sys.argv[3])
            if down_sample <= 0:
                raise ValueError("down_sample must be greater than 0")
        except ValueError as e:
            print(f"Error: down_sample parameter error. {e}")
            sys.exit(1)

    skeletonize(in_path, out_folder, down_sample)

if __name__ == "__main__":
    main()