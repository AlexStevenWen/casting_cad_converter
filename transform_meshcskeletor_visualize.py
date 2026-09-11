import sys
import os
import open3d as o3d
import numpy as np
import collections

print("--- 獨立 3D 可視化工具 (Mesh + SWC) ---")

def load_mesh_file(mesh_path):
    """
    使用 Open3D 載入網格檔案 (ply, obj, stl 等)
    """
    if not os.path.exists(mesh_path):
        print(f"❌ 錯誤: 找不到網格檔案 {mesh_path}")
        return None
    
    try:
        print(f"📂 正在載入網格: {mesh_path}")
        mesh = o3d.io.read_triangle_mesh(mesh_path)
        if not mesh.has_vertices():
            print(f"❌ 錯誤: 網格檔案 {mesh_path} 為空或無法讀取。")
            return None
        
        # 賦予灰色並計算法線，使其看起來更清晰
        mesh.paint_uniform_color([0.7, 0.7, 0.7])
        mesh.compute_vertex_normals()
        print(f"    -> 網格: {len(mesh.vertices)} 頂點, {len(mesh.triangles)} 面")
        return mesh
    except Exception as e:
        print(f"❌ 載入網格時發生錯誤: {e}")
        return None

def load_swc_file(swc_path):
    """
    載入 SWC 檔案並將其轉換為 Open3D 的 LineSet
    """
    if not os.path.exists(swc_path):
        print(f"❌ 錯誤: 找不到 SWC 檔案 {swc_path}")
        return None
        
    print(f"💀 正在載入 SWC: {swc_path}")
    nodes = {}
    lines = []
    
    try:
        with open(swc_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('#') or not line:
                    continue
                
                parts = line.split()
                if len(parts) < 7:
                    continue
                
                node_id = int(parts[0])
                x, y, z = float(parts[2]), float(parts[3]), float(parts[4])
                parent_id = int(parts[6])
                
                # 儲存節點位置
                nodes[node_id] = [x, y, z]
                
                # 如果有父節點，建立一條線
                if parent_id != -1 and parent_id in nodes:
                    # lines 儲存的是 [node_index_a, node_index_b]
                    # 這裡我們直接用 node_id-1 (假設 id 從 1 開始且連續)
                    # 為了更穩健，我們建立一個 id 到 index 的映射
                    lines.append((node_id, parent_id))

        if not nodes:
            print("❌ 錯誤: SWC 檔案中未找到任何節點。")
            return None

        # 重新建立索引，因為 SWC ID 可能不連續
        node_id_to_index = {node_id: i for i, node_id in enumerate(nodes.keys())}
        node_points = [nodes[node_id] for node_id in nodes.keys()]
        
        line_indices = []
        for (id_a, id_b) in lines:
            if id_a in node_id_to_index and id_b in node_id_to_index:
                idx_a = node_id_to_index[id_a]
                idx_b = node_id_to_index[id_b]
                line_indices.append([idx_a, idx_b])

        # 建立 Open3D LineSet
        line_set = o3d.geometry.LineSet()
        line_set.points = o3d.utility.Vector3dVector(node_points)
        line_set.lines = o3d.utility.Vector2iVector(line_indices)
        
        # 賦予紅色
        line_set.paint_uniform_color([1.0, 0, 0])
        print(f"    -> 骨架: {len(node_points)} 節點, {len(line_indices)} 條連線")
        return line_set

    except Exception as e:
        print(f"❌ 讀取 SWC 時發生錯誤: {e}")
        return None
def visualize_files(mesh_path, swc_path):
    """
    載入網格和 SWC 檔案並使用 Open3D 進行可視化。
    (這是可被 import 的主邏輯)
    """
    # 載入幾何體
    mesh = load_mesh_file(mesh_path)
    skeleton = load_swc_file(swc_path)
    
    geometries = []
    if mesh:
        geometries.append(mesh)
    if skeleton:
        geometries.append(skeleton)
        
    if not geometries:
        print("❌ 沒有可顯示的物件。請檢查您的檔案路徑。")
        return # <-- 改為 return 而非 sys.exit()
        
    # 顯示
    print("\n✅ 載入成功！正在啟動 Open3D 視窗...")
    print("    -> 按 'q' 關閉視窗。")
    o3d.visualization.draw_geometries(geometries,
                                      window_name=f"可視化: {os.path.basename(mesh_path)}",
                                      width=1024,
                                      height=768)
    print("...可視化結束。")
def main():
    if len(sys.argv) != 3:
        print("\n--- 獨立 3D 可視化工具 (Mesh + SWC) ---")
        print("用途: 將一個網格檔案和一個 SWC 骨架檔案疊加顯示。")
        print("用法: python visualize.py <mesh_file_path> <swc_file_path>")
        print("範例: python visualize.py ./my_mesh.obj ./skeleton.swc")
        sys.exit(1)
        
    mesh_path = sys.argv[1]
    swc_path = sys.argv[2]
    
    # 從 main() 呼叫新的邏輯函數
    visualize_files(mesh_path, swc_path)

if __name__ == "__main__":
    main()