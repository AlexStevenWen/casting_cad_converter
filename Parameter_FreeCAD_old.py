import sys
import os
sys.path.append('C:/Program Files/FreeCAD 0.21/bin')
import FreeCAD
import Mesh
import Import
import Part
import io
import json
import math
import gc
class Parameter_FreeCAD:
    def __init__(self, in_path, mode ='step',Fvector = (0, 0, 0) , Frotation = 0):
        self.in_path = in_path
        self.mode = '.' + mode
        self.Fvector = Fvector
        self.Frotation = Frotation
        self.res = self.Parameter()
        #print(self.Parameter())

    def Parameter(self):
        if self.mode == ".step" or self.mode == '.stp' :
            Import.open(self.in_path)  # 打開 STEP 文件
            doc = FreeCAD.ActiveDocument  # 獲取當前文檔
            
            # 找到第一個具有 Shape 屬性的物件
            part_obj = next((obj for obj in doc.Objects if hasattr(obj, 'Shape')), None)
            
            if not part_obj:
                raise ValueError("No Part::Feature objects found in the document")

            # 設置旋轉角度（以度為單位）
            # new code: coerce "x,y,z" → (x, y, z) floats
            if isinstance(self.Fvector, str):
                parts = self.Fvector.split(',')
                if len(parts) != 3:
                    raise ValueError(f"Expected 3 components in rotation axis, got: {self.Fvector!r}")
                try:
                    x, y, z = map(float, parts)
                except ValueError:
                    raise ValueError(f"Could not parse rotation axis floats from: {self.Fvector!r}")
                rotation_vector = FreeCAD.Vector(x, y, z)
            else:
                # assume it's already a 3‑tuple/list of numbers
                rotation_vector = FreeCAD.Vector(*self.Fvector)
            #print("rotation_vector is",rotation_vector)
            #print("self.Frotation is",self.Frotation)
            rotation_placement = FreeCAD.Placement()
            rotation_placement.Rotation = FreeCAD.Rotation(rotation_vector, float(self.Frotation))

            # 應用旋轉變換
            part_obj.Placement = rotation_placement

            # 獲取形狀
            shape = part_obj.Shape
            

            # 计算体积
            volume = shape.Volume
            area = shape.Area  #：获取形状的表面积。
            centerofmass = {"x":shape.CenterOfMass.x,
                            "y":shape.CenterOfMass.y,
                            "z":shape.CenterOfMass.z,
                            } #获取形状的质心位置。
            boundbox = {
                "XMin": shape.BoundBox.XMin,
                "XMax": shape.BoundBox.XMax,
                "YMin": shape.BoundBox.YMin,
                "YMax": shape.BoundBox.YMax,
                "ZMin": shape.BoundBox.ZMin,
                "ZMax": shape.BoundBox.ZMax
            }
            edges_number = len(shape.Edges) #获取形状的边数。
            face_number = len(shape.Faces)#获取形状的面的数量。
            vertexes_number = len(shape.Vertexes)#获取形状的顶点数量。
            euler_characteristic =  vertexes_number  -edges_number +face_number
            principal_moments = {
            "I1": shape.PrincipalProperties['Moments'].x,
            "I2": shape.PrincipalProperties['Moments'].y,
            "I3": shape.PrincipalProperties['Moments'].z
        }
            matrixofinertia = {
                "Ixx" : shape.MatrixOfInertia.A11,
                "Ixy" : shape.MatrixOfInertia.A12,
                "Ixz" : shape.MatrixOfInertia.A13,
                "Iyx" : shape.MatrixOfInertia.A21,
                "Iyy" : shape.MatrixOfInertia.A22,
                "Iyz" : shape.MatrixOfInertia.A23,
                "Izx" : shape.MatrixOfInertia.A31,
                "Izy" : shape.MatrixOfInertia.A32,
                "Izz" : shape.MatrixOfInertia.A33,
            }
            from concurrent.futures import ThreadPoolExecutor
            """
            XY_max_area = get_max_cross_section_area(shape,'XY')
            XZ_max_area = get_max_cross_section_area(shape, 'XZ')
            YZ_max_area = get_max_cross_section_area(shape, 'YZ')
            """

            def calculate_max_area(shape, plane):
                return get_max_cross_section_area(shape, plane)

            with ThreadPoolExecutor() as executor:
                # 提交任務到執行緒池
                future_xy = executor.submit(calculate_max_area, shape, 'XY')
                future_xz = executor.submit(calculate_max_area, shape, 'XZ')
                future_yz = executor.submit(calculate_max_area, shape, 'YZ')

                # 獲取結果
                XY_max_area = future_xy.result()
                XZ_max_area = future_xz.result()
                YZ_max_area = future_yz.result()
            max_area = {
                "XYMaxArea" : XY_max_area,
                "XZMaxArea": XZ_max_area,
                "YZMaxArea": YZ_max_area,
            }
            #print(matrixofinertia)

            # 关闭文档
            FreeCAD.closeDocument(doc.Name)
            gc.collect()
            return [{"Volume": volume},{"Area":area},{"CenterOfMass":centerofmass},{"BoundBox":boundbox},{"EdgesNumber":edges_number},{"FaceNumber":face_number},{"VertexesNumber":vertexes_number},{"MatrixOfInertia":matrixofinertia},{"MaxArea":max_area}]
       #{"EdgesNumber":edges_number},{"FaceNumber":face_number},{"Vertexes_number":vertexes_number},
        else:
            print("file type not supported")
            return [{"Volume": 0},{"Area":0},{"CenterOfMass":0},{"BoundBox":0},{"EdgesNumber":0},{"FaceNumber":0},{"VertexesNumber":0},{"MatrixOfInertia":0},{"MaxArea":0}]
    def __str__(self):
        return json.dumps(self.res)


def get_max_cross_section_area(shape, direction):
    # 初始化最大面积
    max_area = 0
    # 获取形状的边界框
    bounding_box = shape.BoundBox

    # 根据切片方向选择切片的位置范围
    if direction == 'XY':
        min_bound = bounding_box.ZMin
        max_bound = bounding_box.ZMax
        normal = FreeCAD.Vector(0, 0, 1)
    elif direction == 'XZ':
        min_bound = bounding_box.YMin
        max_bound = bounding_box.YMax
        normal = FreeCAD.Vector(0, 1, 0)
    elif direction == 'YZ':
        min_bound = bounding_box.XMin
        max_bound = bounding_box.XMax
        normal = FreeCAD.Vector(1, 0, 0)
    else:
        raise ValueError("方向必须是 'XY', 'XZ' 或 'YZ'")

    # 步进值，根据需要调整
    step = (max_bound - min_bound)

    def divide_and_conquer(slice_indices, shape, bounding_box, direction, normal):
        if len(slice_indices) == 1:
            i = slice_indices[0]
            # 计算当前切片位置
            position = min_bound + i

            # 生成平面
            if direction == 'XY':
                plane = Part.makePlane(bounding_box.XMax - bounding_box.XMin ,bounding_box.YMax - bounding_box.YMin, FreeCAD.Vector(bounding_box.XMin ,bounding_box.YMin, position), normal)
            elif direction == 'XZ':
                plane = Part.makePlane(bounding_box.ZMax - bounding_box.ZMin, bounding_box.XMax - bounding_box.XMin, FreeCAD.Vector(bounding_box.XMin, position, bounding_box.ZMin), normal)
            elif direction == 'YZ':
                plane = Part.makePlane(bounding_box.ZMax - bounding_box.ZMin, bounding_box.YMax - bounding_box.YMin, FreeCAD.Vector(position ,bounding_box.YMax, bounding_box.ZMin), normal)
            
            # 切割形状
            section = shape.common(plane)

            # 计算截面积
            area = sum([face.Area for face in section.Faces])
            return area
        # 分解
        mid = len(slice_indices) // 2
        left_indices = slice_indices[:mid]
        right_indices = slice_indices[mid:]

        # 递归地处理两个子问题
        left_max_area = divide_and_conquer(left_indices, shape, bounding_box, direction, normal)
        right_max_area = divide_and_conquer(right_indices, shape, bounding_box, direction, normal)

        # 合并结果
        return max(left_max_area, right_max_area)
    # 遍历指定方向上的位置

    for i in range(int(step) + 1):

        # 计算当前切片位置
        position = min_bound + i

        # 生成平面
        if direction == 'XY':
            plane = Part.makePlane(bounding_box.XMax - bounding_box.XMin ,bounding_box.YMax - bounding_box.YMin, FreeCAD.Vector(bounding_box.XMin ,bounding_box.YMin, position), normal)
        elif direction == 'XZ':
            plane = Part.makePlane(bounding_box.ZMax - bounding_box.ZMin, bounding_box.XMax - bounding_box.XMin, FreeCAD.Vector(bounding_box.XMin, position, bounding_box.ZMin), normal)
        elif direction == 'YZ':
            plane = Part.makePlane(bounding_box.ZMax - bounding_box.ZMin, bounding_box.YMax - bounding_box.YMin, FreeCAD.Vector(position ,bounding_box.YMax, bounding_box.ZMin), normal)

        # 切割形状
        section = shape.common(plane)

        # 计算截面积
        area = sum([face.Area for face in section.Faces])

        # 更新最大面积
        if area > max_area:
            max_area = area
    return max_area
    """
    min_bound = bounding_box.XMin  # 假设 min_bound 对应于 bounding_box 的最小值
    slice_indices = list(range(int(step) + 1))
    max_area = divide_and_conquer(slice_indices, shape, bounding_box, direction, normal)
    return max_area
    """
def main(in_path,mode = ".step",Fvector = (0, 0, 0) , Frotation = 0):
    # 这里是你的主要逻辑
    #mesh = FreeCAD.Mesh.Mesh('3Dtest.stl')
    #polt_3D_mesh(mesh)
    a = Parameter_FreeCAD(in_path,mode=mode ,Fvector = Fvector , Frotation =  Frotation)
    
    return print(a)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python transform_FreeCAD.py <in_path> [mode]")
    else:
        in_path = sys.argv[1]
        mode = sys.argv[2] if len(sys.argv) > 2 else ".step"
        Fvector = sys.argv[3] if len(sys.argv) > 3 else (0,0,0)
        Frotation = sys.argv[4] if len(sys.argv) > 4 else 90
        #print(in_path)
        #print(mode)
        #print(Fvector)
        #print(Frotation)

        #print(in_path,out_path,mode)
        result = main(in_path,mode,Fvector,Frotation )




