import sys
import os
sys.path.append('C:/Program Files/FreeCAD 0.21/bin')
import FreeCAD
import Mesh
import Import
import Part
import io
import gc
class transform_FreeCAD:
    def __init__(self, in_path, out_path="out_path", mode='stl', 
                 Fvector=(0, 0, 0), Frotation=0,Fmoving =(0,0,0), tolerance=0.1, tessellate_value=0.1,
                 ):
        self.in_path = in_path
        self.out_path = out_path
        self.ex_in = os.path.splitext(in_path)[1].lower()
        self.mode = '.' + mode
        self.Fvector = Fvector
        self.Frotation = Frotation
        self.Fmoving = Fmoving
        self.tolerance = tolerance
        self.tessellate_value = tessellate_value
        # 新增對正參數
        self.do_align = False
        self.align_target = (0,0,0)
    def STEPtoSTEP(self):
        # 讀取 STEP 文件
        Import.open(self.in_path)
        doc = FreeCAD.ActiveDocument

        # 過濾出所有 Part::Feature 物件
        part_features = [obj for obj in doc.Objects if hasattr(obj, 'Shape')]
        if not part_features:
            raise ValueError("No Part::Feature objects found in the document")

        # 取得所有零件的形狀，建立組合件
        shapes = [obj.Shape for obj in part_features]
        compound = Part.makeCompound(shapes)

        # 將 Compound 加入文檔中
        compound_obj = doc.addObject("Part::Feature", "Compound")
        compound_obj.Shape = compound

        # 設置旋轉角度（以度為單位）
        rotation_vector = FreeCAD.Vector(self.Fvector)  # 設置旋轉軸，例如 Z 軸
        rotation_placement = FreeCAD.Placement()
        rotation_placement.Rotation = FreeCAD.Rotation(rotation_vector, self.Frotation)

        # 對組合件應用旋轉變換
        compound_obj.Placement = rotation_placement

        # 若啟用對正功能，計算形心平移到指定位置
        if self.do_align:
            # 計算全局座標系中的形心（考慮旋轉後的變換）
            centroid_local = compound_obj.Shape.CenterOfMass()  # 這裡要用 compound_obj.Shape
            centroid_global = compound_obj.Placement.multVec(centroid_local)
            target_vector = FreeCAD.Vector(self.align_target)

            # 計算平移向量（全局座標系）
            translation_vector = target_vector - centroid_global

            # 更新 Placement 的 Base
            new_placement = compound_obj.Placement
            new_placement.Base += translation_vector
            compound_obj.Placement = new_placement

        # 匯出旋轉（及對正）後的組合件
        Part.export([compound_obj], "{}{}".format(self.out_path, self.mode))

        # 關閉文檔並釋放記憶體
        FreeCAD.closeDocument(doc.Name)
        gc.collect()

    def STLtoSTEP(self):
        mesh = Mesh.Mesh(self.in_path)
        # 将 Mesh 转换为 Shape
        shape = Part.Shape()

        shape.makeShapeFromMesh(mesh.Topology, self.tolerance)  # 0.1 表示容差

        # 将 Shape 转换为 Solid
        solid = Part.makeSolid(shape)
        refined_shape = solid.removeSplitter()
        # 创建一个新的文档
        doc = FreeCAD.newDocument("STL_to_STEP_Conversion")

        # 将 Solid 添加到文档中
        part_obj = doc.addObject("Part::Feature", "ConvertedSolid")
        part_obj.Shape = refined_shape

        # 保存为 STEP 文件
        Part.export([part_obj], "{}{}".format(self.out_path, self.mode))

        # 完成后关闭文档
        FreeCAD.closeDocument(doc.Name)
        gc.collect()
        
    def STEPtoSTL(self): 
        # 讀取 STEP 文件
        Import.open(self.in_path)  # 使用 Import.open() 方法打開 STEP 文件
        doc = FreeCAD.ActiveDocument  # 獲取當前文檔

        # 獲取 STEP 文件中的所有具有 Shape 屬性的對象
        part_features = [obj for obj in doc.Objects if hasattr(obj, 'Shape')]

        # 如果沒有 Part::Feature 物件則退出
        if not part_features:
            raise ValueError("No Part::Feature objects found in the document")

        # 判斷是否為單一件物件
        if len(part_features) == 1:
            print("The document contains only one part feature.")
            # 如果只有一個物件，直接使用該物件的 Shape
            compound_shape = part_features[0].Shape
        else:
            # 創建 Compound（複合物件）當有多個物件時
            print("The document contains multiple part features. Combining them into a compound.")
            compound_shape = Part.makeCompound([obj.Shape for obj in part_features])

        # 創建新的物件來存放 Compound
        compound_obj = doc.addObject("Part::Feature", "CompoundObject")
        compound_obj.Shape = compound_shape

        placement = FreeCAD.Placement() 

        # 平移：使用 align_target 作為平移目標
        placement.Base = FreeCAD.Vector(*self.Fmoving)
        
        # 旋轉：以 Fvector 為旋轉軸，並以 Frotation 作為旋轉角度（角度制）
        placement.Rotation = FreeCAD.Rotation(FreeCAD.Vector(*self.Fvector), self.Frotation)
        
        # 更新物件的 Placement
        compound_obj.Placement = placement

        # 保存為 STL 文件
        Mesh.export([compound_obj], "{}{}".format(self.out_path, self.mode))

        # 關閉文檔
        FreeCAD.closeDocument(doc.Name)
        gc.collect()
    def STEPtoOFF(self):
        # 讀取 STEP 文件
        Import.open(self.in_path)  # 使用 Import.open() 方法打開 STEP 文件
        doc = FreeCAD.ActiveDocument  # 獲取當前文檔

        # 取得所有具有 Shape 屬性的對象
        part_features = [obj for obj in doc.Objects if hasattr(obj, 'Shape')]
        if not part_features:
            raise ValueError("No Part::Feature objects found in the document")

        # 創建 Compound（複合物件）
        merged_shape = Part.makeCompound([obj.Shape for obj in part_features])

        # 轉換為網格
        mesh = Mesh.Mesh(merged_shape.tessellate(self.tessellate_value))
        
        # 輸出為 OFF 格式
        off_path = "{}.off".format(self.out_path)
        mesh.write(off_path, "OFF")  # 輸出 OFF 格式

        # 關閉文檔並進行垃圾回收
        FreeCAD.closeDocument(doc.Name)
        gc.collect()
    def STEPtoPLY(self):
        # 讀取 STEP 文件
        Import.open(self.in_path)  # 使用 Import.open() 方法打開 STEP 文件
        doc = FreeCAD.ActiveDocument  # 獲取當前文檔

        # 取得所有具有 Shape 屬性的對象
        part_features = [obj for obj in doc.Objects if hasattr(obj, 'Shape')]
        if not part_features:
            raise ValueError("No Part::Feature objects found in the document")

        # 創建 Compound（複合物件）
        merged_shape = Part.makeCompound([obj.Shape for obj in part_features])

        # 轉換為網格
        mesh = Mesh.Mesh(merged_shape.tessellate(self.tessellate_value))
        
        # 輸出為 PLY 格式 (二進制格式)
        ply_path = "{}.ply".format(self.out_path)
        mesh.write(ply_path, "PLY2")  # "PLY2" 表示二進制格式

        # 關閉文檔並進行垃圾回收
        FreeCAD.closeDocument(doc.Name)
        gc.collect()
    def STEPtoOBJ(self):
        # 讀取 STEP 文件
        Import.open(self.in_path)  # 使用 Import.open() 方法打開 STEP 文件
        doc = FreeCAD.ActiveDocument  # 獲取當前文檔

        # 取得所有具有 Shape 屬性的對象
        part_features = [obj for obj in doc.Objects if hasattr(obj, 'Shape')]
        if not part_features:
            raise ValueError("No Part::Feature objects found in the document")

        # 創建 Compound（複合物件）
        merged_shape = Part.makeCompound([obj.Shape for obj in part_features])

        # 轉換為網格
        mesh = Mesh.Mesh(merged_shape.tessellate(self.tessellate_value))
        
        # 輸出為 OBJ 格式
        obj_path = "{}.obj".format(self.out_path)
        mesh.write(obj_path, "OBJ")  # 輸出 OBJ 格式

        # 關閉文檔並進行垃圾回收
        FreeCAD.closeDocument(doc.Name)
        gc.collect()
    def transfromFreeCAD(self):
        #print(self.mode)
        #print(self.ex_in)
        
        if self.mode == '.stl':
            if self.ex_in == '.step' or self.ex_in == '.stp' or self.ex_in == '.igs':
                self.STEPtoSTL()
        elif self.mode == ".step" or self.mode == '.stp' or self.mode == '.igs':
            if self.ex_in == '.stl':
                self.STLtoSTEP()
            if self.ex_in == '.step' or self.ex_in == '.stp' or self.ex_in == '.igs':
                self.STEPtoSTEP()
        elif self.mode == '.step':
            if self.ex_in == '.step' or self.ex_in == '.stp' or self.ex_in == '.igs':
                self.STEPtoSTL()
        elif self.mode == '.obj':
            if self.ex_in == '.step' or self.ex_in == '.stp' or self.ex_in == '.igs':
                self.STEPtoOBJ()
        elif self.mode == '.ply':
            if self.ex_in == '.step' or self.ex_in == '.stp' or self.ex_in == '.igs':
                self.STEPtoPLY()
        elif self.mode == '.off':
            if self.ex_in == '.step' or self.ex_in == '.stp' or self.ex_in == '.igs':
                self.STEPtoOFF()
                
        else:
            print("file type not supported")

def main(in_path, out_path="out_path", mode="stl", Fvector=(0, 0, 0), Frotation=0, Fmoving = (0,0,0), tolerance=0.1, tessellate_value=0.1):
    tolerance = float(tolerance)
    tessellate_value = float(tessellate_value)
    Frotation = float(Frotation)

    # 確保 Fvector 是 tuple 並且內部是 float
    if isinstance(Fvector, str):
        Fvector = tuple(map(float, Fvector.split(",")))  
    if isinstance(Fmoving, str):
        Fmoving = tuple(map(float, Fmoving.split(","))) 

    a = transform_FreeCAD(in_path, out_path, mode=mode, Fvector=Fvector, Frotation=Frotation,Fmoving=Fmoving, tolerance=tolerance, tessellate_value=tessellate_value)
    a.transfromFreeCAD()
    return a

if __name__ == "__main__":
    if len(sys.argv) < 7:
        print("Usage: python transform_FreeCAD.py <in_path> <out_path> <mode> <Fvector> <Frotation> <tolerance> <tessellate_value>")
    else:
        in_path = sys.argv[1]
        out_path = sys.argv[2] if len(sys.argv) > 2 else "out_path"
        mode = sys.argv[3] if len(sys.argv) > 3 else "stl"
        Fvector = sys.argv[4] if len(sys.argv) > 4 else (0,0,0)
        Frotation = sys.argv[5] if len(sys.argv) > 5 else 90
        Fmoving = sys.argv[6] if len(sys.argv) > 6 else (0,0,0)
        tolerance = sys.argv[7] if len(sys.argv) > 7 else 0.1
        tessellate_value = sys.argv[8] if len(sys.argv) > 8 else 0.1
        tolerance = sys.argv[7] if len(sys.argv) > 7 else 0.1
        tessellate_value = sys.argv[8] if len(sys.argv) > 8 else 0.1

        # 轉換 Fvector
        if isinstance(Fvector, str):
            Fvector = tuple(map(float, Fvector.split(",")))  

        main(in_path, out_path, mode, Fvector, Frotation,Fmoving ,tolerance, tessellate_value)



