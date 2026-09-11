import sys
import os
sys.path.append('C:/Program Files/FreeCAD 0.21/bin')
import FreeCAD
import Mesh
import Import
import Part
import io
import json
from concurrent.futures import ThreadPoolExecutor
import numpy as np
class PonintCloud_FreeCAD:
    def __init__(self, in_path, out_path="out_path"):
        self.in_path = in_path
        self.out_path = out_path
        self.ex_in = os.path.splitext(in_path)[1].lower()
    def PonintCloud_FreeCAD(self):
        if self.ex_in in ['.step', '.stp', '.igs']:
            # 读取 STEP 文件
            Import.open(self.in_path)
            doc = FreeCAD.ActiveDocument  # 获取当前文档
            shape = doc.Objects[0].Shape  # 假设 STEP 文件中只有一个对象，获取第一个对象

            # 设置点云的分辨率
            resolution = 1

            # 获取实体模型的边界框
            bbox = shape.BoundBox
            xmin, xmax = bbox.XMin, bbox.XMax
            ymin, ymax = bbox.YMin, bbox.YMax
            zmin, zmax = bbox.ZMin, bbox.ZMax

            # 创建均匀的点网格
            x = np.linspace(xmin, xmax, int((xmax - xmin) / resolution))
            y = np.linspace(ymin, ymax, int((ymax - ymin) / resolution))
            z = np.linspace(zmin, zmax, int((zmax - zmin) / resolution))
            xx, yy, zz = np.meshgrid(x, y, z)

            # 将点网格转换为点列表
            points = np.c_[xx.ravel(), yy.ravel(), zz.ravel()]

            # 检查每个点是否在实体模型内部
            def check_point(point):
                vec = FreeCAD.Vector(point[0], point[1], point[2])
                return point if shape.isInside(vec, 1e-6, True) else None

            with ThreadPoolExecutor() as executor:
                results = list(executor.map(check_point, points))

            # 过滤掉 None 值
            point_cloud = np.array([point for point in results if point is not None])

            return point_cloud

    def delete_edges_from_to(shape, start_edge, end_edge):
        # 获取模型的边界边
        edges = shape.Edges
        # 选择需要删除的边
        edges_to_delete = [edge for edge in edges if start_edge in edge.Vertices and end_edge in edge.Vertices]

        # 删除选中的边
        for edge in edges_to_delete:
            shape.Edges.remove(edge)

        # 返回修改后的形状
        return shape

    def __str__(self):
        point_cloud = self.PonintCloud_FreeCAD()
        return json.dumps(point_cloud.tolist()) if point_cloud is not None else "No point cloud generated"

def main(in_path,out_path = "out_path"):
    # 这里是你的主要逻辑
    #mesh = FreeCAD.Mesh.Mesh('3Dtest.stl')
    #polt_3D_mesh(mesh)
    a = PonintCloud_FreeCAD(in_path,out_path)
    a.PonintCloud_FreeCAD()
    return print(a)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python transform_FreeCAD.py <in_path> [mode]")
    else:
        in_path = sys.argv[1]
        out_path = sys.argv[2] if len(sys.argv) > 2 else "out_path"
        #print(in_path,out_path,mode)
        main(in_path,out_path)



