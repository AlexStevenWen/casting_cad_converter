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
        self.mode = '.' + mode.replace('.', '')
        self.Fvector = Fvector
        self.Frotation = Frotation
        self.res = self.Parameter()

    def Parameter(self):
        if self.mode in [".step", '.stp']:
            try:
                Import.open(self.in_path)  # 打開 STEP 文件
                doc = FreeCAD.ActiveDocument 
                
                # 找到第一個具有 Shape 屬性的物件
                part_obj = next((obj for obj in doc.Objects if hasattr(obj, 'Shape')), None)
                if not part_obj:
                    raise ValueError("No Part::Feature objects found in the document")

                # 設置旋轉角度
                if isinstance(self.Fvector, str):
                    parts = self.Fvector.split(',')
                    x, y, z = map(float, parts)
                    rotation_vector = FreeCAD.Vector(x, y, z)
                else:
                    rotation_vector = FreeCAD.Vector(*self.Fvector)

                rotation_placement = FreeCAD.Placement()
                rotation_placement.Rotation = FreeCAD.Rotation(rotation_vector, float(self.Frotation))
                part_obj.Placement = rotation_placement

                shape = part_obj.Shape
                
                # 安全獲取基本屬性
                volume = getattr(shape, 'Volume', 0.0)
                area = getattr(shape, 'Area', 0.0)  
                cm = getattr(shape, 'CenterOfMass', None)
                centerofmass = {"x": cm.x, "y": cm.y, "z": cm.z} if cm else {"x":0, "y":0, "z":0}
                
                bb = getattr(shape, 'BoundBox', None)
                if bb:
                    boundbox = {"XMin": bb.XMin, "XMax": bb.XMax, "YMin": bb.YMin, "YMax": bb.YMax, "ZMin": bb.ZMin, "ZMax": bb.ZMax}
                else:
                    boundbox = {"XMin": 0, "XMax": 0, "YMin": 0, "YMax": 0, "ZMin": 0, "ZMax": 0}
                    
                edges_number = len(shape.Edges) if hasattr(shape, 'Edges') else 0
                face_number = len(shape.Faces) if hasattr(shape, 'Faces') else 0
                vertexes_number = len(shape.Vertexes) if hasattr(shape, 'Vertexes') else 0
                euler_characteristic = vertexes_number - edges_number + face_number
                
                try:
                    mi = shape.MatrixOfInertia
                    matrixofinertia = {
                        "Ixx": mi.A11, "Ixy": mi.A12, "Ixz": mi.A13,
                        "Iyx": mi.A21, "Iyy": mi.A22, "Iyz": mi.A23,
                        "Izx": mi.A31, "Izy": mi.A32, "Izz": mi.A33,
                    }
                except Exception:
                    matrixofinertia = {"Ixx":0, "Ixy":0, "Ixz":0, "Iyx":0, "Iyy":0, "Iyz":0, "Izx":0, "Izy":0, "Izz":0}

                # --- 2. 利用 NumPy 從慣性矩陣精確計算 PrincipalMoments (主慣性矩) ---
                try:
                    import numpy as np
                    # 將剛剛取得的慣性特徵轉換為 3x3 矩陣
                    I_matrix = np.array([
                        [matrixofinertia["Ixx"], matrixofinertia["Ixy"], matrixofinertia["Ixz"]],
                        [matrixofinertia["Iyx"], matrixofinertia["Iyy"], matrixofinertia["Iyz"]],
                        [matrixofinertia["Izx"], matrixofinertia["Izy"], matrixofinertia["Izz"]]
                    ])
                    # 計算特徵值 (即為主慣性矩)，eigvalsh 專門處理這種實對稱矩陣，極度穩定
                    eigenvalues = np.linalg.eigvalsh(I_matrix)
                    principal_moments = {
                        "I1": float(eigenvalues[0]),
                        "I2": float(eigenvalues[1]),
                        "I3": float(eigenvalues[2])
                    }
                except Exception:
                    # 萬一 NumPy 沒裝或是遇到極端幾何導致奇異矩陣，退回 FreeCAD 原生算法
                    try:
                        props = shape.PrincipalProperties
                        if 'Moments' in props:
                            principal_moments = {
                                "I1": props['Moments'].x,
                                "I2": props['Moments'].y,
                                "I3": props['Moments'].z
                            }
                        else:
                            principal_moments = {"I1": 0, "I2": 0, "I3": 0}
                    except Exception:
                        principal_moments = {"I1": 0, "I2": 0, "I3": 0}

                # --- 恢復你的多執行緒，確保切片速度 ---
                from concurrent.futures import ThreadPoolExecutor

                def calculate_max_area(s, plane):
                    # 避免單個切面崩潰影響整體
                    try:
                        return get_max_cross_section_area(s, plane)
                    except Exception:
                        return 0.0

                with ThreadPoolExecutor() as executor:
                    future_xy = executor.submit(calculate_max_area, shape, 'XY')
                    future_xz = executor.submit(calculate_max_area, shape, 'XZ')
                    future_yz = executor.submit(calculate_max_area, shape, 'YZ')

                    XY_max_area = future_xy.result()
                    XZ_max_area = future_xz.result()
                    YZ_max_area = future_yz.result()
                    
                max_area = {
                    "XYMaxArea": XY_max_area,
                    "XZMaxArea": XZ_max_area,
                    "YZMaxArea": YZ_max_area,
                }

                # 关闭文档
                FreeCAD.closeDocument(doc.Name)
                gc.collect()
                
                return [
                    {"Volume": volume}, {"Area": area}, {"CenterOfMass": centerofmass},
                    {"BoundBox": boundbox}, {"EdgesNumber": edges_number}, {"FaceNumber": face_number},
                    {"VertexesNumber": vertexes_number}, {"MatrixOfInertia": matrixofinertia},
                    {"MaxArea": max_area}, {"EulerCharacteristic": euler_characteristic},
                    {"PrincipalMoments": principal_moments}
                ]
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr)
                return self._get_default_return()
        else:
            return self._get_default_return()

    def _get_default_return(self):
        # 保持格式與長度一致 (11個元素)
        return [
            {"Volume": 0}, {"Area": 0}, {"CenterOfMass": {"x":0,"y":0,"z":0}}, 
            {"BoundBox": {"XMin":0,"XMax":0,"YMin":0,"YMax":0,"ZMin":0,"ZMax":0}},
            {"EdgesNumber": 0}, {"FaceNumber": 0}, {"VertexesNumber": 0},
            {"MatrixOfInertia": {"Ixx":0,"Ixy":0,"Ixz":0,"Iyx":0,"Iyy":0,"Iyz":0,"Izx":0,"Izy":0,"Izz":0}}, 
            {"MaxArea": {"XYMaxArea":0,"XZMaxArea":0,"YZMaxArea":0}},
            {"EulerCharacteristic": 0}, {"PrincipalMoments": {"I1":0,"I2":0,"I3":0}}
        ]

    def __str__(self):
        return json.dumps(self.res)

def get_max_cross_section_area(shape, direction):
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
        pass
    else:
        in_path = sys.argv[1]
        mode = sys.argv[2] if len(sys.argv) > 2 else ".step"
        Fvector = sys.argv[3] if len(sys.argv) > 3 else (0,0,0)
        Frotation = sys.argv[4] if len(sys.argv) > 4 else 0
        result = main(in_path,mode,Fvector,Frotation)