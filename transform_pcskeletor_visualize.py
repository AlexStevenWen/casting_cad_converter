import sys
import os
import open3d as o3d
import numpy as np
import h5py

def is_skip_token(path_str):
    """判斷字串是否為跳過指令"""
    return not path_str or path_str.lower() in ['none', 'null', '0', '-', 'nan']

def load_point_cloud(in_path):
    """
    讀取點雲 (.ply, .pcd, .xyz, .npz, .h5)
    """
    if is_skip_token(in_path):
        return None

    if not os.path.exists(in_path):
        print(f"[Warning] File not found: {in_path}")
        return None

    ext = os.path.splitext(in_path)[1].lower()
    pcd = o3d.geometry.PointCloud()

    try:
        if ext in ['.ply', '.pcd', '.xyz']:
            pcd = o3d.io.read_point_cloud(in_path)
        
        elif ext == '.npz':
            data = np.load(in_path)
            if 'point_cloud' in data:
                pcd.points = o3d.utility.Vector3dVector(data['point_cloud'])
            else:
                return None
            
        elif ext == '.h5':
            with h5py.File(in_path, 'r') as hf:
                if 'point_cloud' in hf:
                    pcd.points = o3d.utility.Vector3dVector(np.array(hf['point_cloud']))
                else:
                    return None
        else:
            print(f"[Error] Unsupported format: {ext}")
            return None
        
        return pcd
    except Exception as e:
        print(f"[Error] Loading failed for {in_path}: {e}")
        return None

def load_topology(in_path):
    """
    讀取拓譜線 (.ply LineSet)
    """
    if is_skip_token(in_path):
        return None
    
    if not os.path.exists(in_path):
        print(f"[Warning] File not found: {in_path}")
        return None
    
    try:
        lines = o3d.io.read_line_set(in_path)
        if lines.has_lines():
            return lines
        else:
            # 若讀不到線，嘗試讀成點雲當作 fallback
            return load_point_cloud(in_path)
    except:
        return None

def main():
    # 取得參數，若無則預設為 None
    # sys.argv[0] 是程式本身
    arg1_orig = sys.argv[1] if len(sys.argv) > 1 else None
    arg2_skel = sys.argv[2] if len(sys.argv) > 2 else None
    arg3_topo = sys.argv[3] if len(sys.argv) > 3 else None

    # 如果完全沒參數，顯示用法
    if len(sys.argv) < 2:
        print("\nUsage: python visualize.py <Original_Path> <Skeleton_Path> <Topology_Path>")
        print("Note:  Use 'None' or '0' to skip a position.")
        print("\nExample (Skip Original, show Skeleton & Topology):")
        print("  python visualize.py None result/skeleton.pcd result/topology.ply")
        sys.exit(0)

    geometries = []
    print("="*40)

    # 1. 載入原點雲 (位置1) -> 淺灰色
    if not is_skip_token(arg1_orig):
        print(f"1. [Original]: {arg1_orig}")
        pcd = load_point_cloud(arg1_orig)
        if pcd:
            pcd.paint_uniform_color([0.8, 0.8, 0.8])
            geometries.append(pcd)
    else:
        print("1. [Original]: Skipped")

    # 2. 載入骨架 (位置2) -> 紅色
    if not is_skip_token(arg2_skel):
        print(f"2. [Skeleton]: {arg2_skel}")
        pcd = load_point_cloud(arg2_skel)
        if pcd:
            pcd.paint_uniform_color([1.0, 0.0, 0.0])
            geometries.append(pcd)
    else:
        print("2. [Skeleton]: Skipped")

    # 3. 載入拓譜 (位置3) -> 綠色
    if not is_skip_token(arg3_topo):
        print(f"3. [Topology]: {arg3_topo}")
        mesh = load_topology(arg3_topo)
        if mesh:
            mesh.paint_uniform_color([0.0, 1.0, 0.0])
            geometries.append(mesh)
    else:
        print("3. [Topology]: Skipped")

    print("="*40)

    if not geometries:
        print("[Error] Nothing loaded. Please check your paths.")
        sys.exit(1)

    print("\nVisualizing...")
    print("  [+/-] Change Point Size")
    print("  [N]   Toggle Normals")
    print("  [Q]   Quit")

    o3d.visualization.draw_geometries(geometries, width=1024, height=768)

if __name__ == "__main__":
    main()