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

    def Parameter(self):
        if self.mode == ".step" or self.mode == '.stp' :
            Import.open(self.in_path)  # 打開 STEP 文件
            doc = FreeCAD.ActiveDocument  # 獲取當前文檔
            
            # 找到第一個具有 Shape 屬性的物件
            part_obj = next((obj for obj in doc.Objects if hasattr(obj, 'Shape')), None)
            
            if not part_obj:
                raise ValueError("No Part::Feature objects found in the document")

            # 設置旋轉角度（以度為單位）
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
                rotation_vector = FreeCAD.Vector(*self.Fvector)

            rotation_placement = FreeCAD.Placement()
            rotation_placement.Rotation = FreeCAD.Rotation(rotation_vector, float(self.Frotation))

            # 應用旋轉變換
            part_obj.Placement = rotation_placement

            # 獲取形狀
            shape = part_obj.Shape
            
            # 计算体积、面积、质心等
            volume = shape.Volume
            area = shape.Area  
            centerofmass = {"x":shape.CenterOfMass.x,
                            "y":shape.CenterOfMass.y,
                            "z":shape.CenterOfMass.z} 
            boundbox = {
                "XMin": shape.BoundBox.XMin,
                "XMax": shape.BoundBox.XMax,
                "YMin": shape.BoundBox.YMin,
                "YMax": shape.BoundBox.YMax,
                "ZMin": shape.BoundBox.ZMin,
                "ZMax": shape.BoundBox.ZMax
            }
            edges_number = len(shape.Edges) 
            face_number = len(shape.Faces)
            vertexes_number = len(shape.Vertexes)
            euler_characteristic =  vertexes_number - edges_number + face_number
            
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

            # 关闭文档
            FreeCAD.closeDocument(doc.Name)
            gc.collect()
            
            # --- 修正: 加入 EulerCharacteristic 和 PrincipalMoments ---
            return [
                {"Volume": volume},
                {"Area": area},
                {"CenterOfMass": centerofmass},
                {"BoundBox": boundbox},
                {"EdgesNumber": edges_number},
                {"FaceNumber": face_number},
                {"VertexesNumber": vertexes_number},
                {"MatrixOfInertia": matrixofinertia},
                {"MaxArea": max_area},
                {"EulerCharacteristic": euler_characteristic},
                {"PrincipalMoments": principal_moments}
            ]
        else:
            print("file type not supported")
            # --- 修正: 預設失敗狀態也要補上格式長度 ---
            return [
                {"Volume": 0}, {"Area": 0}, {"CenterOfMass": 0}, {"BoundBox": 0},
                {"EdgesNumber": 0}, {"FaceNumber": 0}, {"VertexesNumber": 0},
                {"MatrixOfInertia": 0}, {"MaxArea": 0},
                {"EulerCharacteristic": 0}, {"PrincipalMoments": 0}
            ]

    def __str__(self):
        return json.dumps(self.res)


def get_max_cross_section_area(shape, direction):
    # (保留你原本的程式碼即可，此處未更動)
    max_area = 0
    bounding_box = shape.BoundBox

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

    step = (max_bound - min_bound)

    for i in range(int(step) + 1):
        position = min_bound + i

        if direction == 'XY':
            plane = Part.makePlane(bounding_box.XMax - bounding_box.XMin ,bounding_box.YMax - bounding_box.YMin, FreeCAD.Vector(bounding_box.XMin ,bounding_box.YMin, position), normal)
        elif direction == 'XZ':
            plane = Part.makePlane(bounding_box.ZMax - bounding_box.ZMin, bounding_box.XMax - bounding_box.XMin, FreeCAD.Vector(bounding_box.XMin, position, bounding_box.ZMin), normal)
        elif direction == 'YZ':
            plane = Part.makePlane(bounding_box.ZMax - bounding_box.ZMin, bounding_box.YMax - bounding_box.YMin, FreeCAD.Vector(position ,bounding_box.YMax, bounding_box.ZMin), normal)

        section = shape.common(plane)
        area = sum([face.Area for face in section.Faces])

        if area > max_area:
            max_area = area
    return max_area

def main(in_path,mode = ".step",Fvector = (0, 0, 0) , Frotation = 0):
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
        result = main(in_path,mode,Fvector,Frotation)