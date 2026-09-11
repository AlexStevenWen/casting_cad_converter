import sys
import os
import FreeCAD
import Mesh
import Import
import Part
import io
import gc

class transform_moving:
    def __init__(self, in_path_assembly, in_path_merged, out_path_assembly="out_assembly", out_path_merged="out_merged", mode='step',
                 Fvector=(0, 0, 0), Frotation=0, do_align=True, align_target=(0, 0, 0)):
        """
        初始化變換類別。

        :param in_path_assembly: 組合件的輸入路徑
        :param in_path_merged: 已合併成單一件的組合件的輸入路徑
        :param out_path_assembly: 變換後的組合件的輸出路徑，預設為 "out_assembly"
        :param out_path_merged: 變換後的合併件的輸出路徑，預設為 "out_merged"
        :param mode: 輸入文件的格式，預設為 'step'
        :param Fvector: 旋轉軸向量，預設為 (0, 0, 1)
        :param Frotation: 旋轉角度，預設為 0
        :param do_align: 是否進行對正，預設為 True
        :param align_target: 對正的目標位置，預設為 (0, 0, 0)
        """
        self.in_path_assembly = in_path_assembly  # 組合件
        self.in_path_merged = in_path_merged      # 已合併成單一件的組合件
        self.out_path_assembly = out_path_assembly  # 變換後的組合件
        self.out_path_merged = out_path_merged      # 合併件輸出
        self.mode = '.' + mode

        # Assign transformation parameters
        self.Fvector = Fvector  # Store the rotation axis
        self.Frotation = Frotation  # Store the rotation angle
        
        self.do_align = do_align
        self.align_target = align_target

        # Set default rotation axis and angle (could be updated later if needed)
        self.rotation_axis = (0, 0, 1)  # 預設旋轉軸（Z 軸）
        self.rotation_angle = 0         # 預設旋轉角度

    def STEPtoSTEP(self):
        """
        處理兩個輸入檔案，計算平移和旋轉 (先對正後旋轉)，並輸出變換後的結果。
        """
        # --- 處理合併單一件 ---
        Import.open(self.in_path_merged)
        doc_merged = FreeCAD.ActiveDocument
        if doc_merged is None:
            raise RuntimeError(f"Failed to open merged file: {self.in_path_merged}")

        # 過濾出有 Shape 的物件
        merged_objs = [obj for obj in doc_merged.Objects if hasattr(obj, 'Shape')]
        if len(merged_objs) != 1:
            if len(merged_objs) == 0:
                FreeCAD.closeDocument(doc_merged.Name)
                raise ValueError(f"No shape object found in merged file: {self.in_path_merged}")
            else:
                # 如果超過 1，選第一個並告警
                merged_obj = merged_objs[0]
        else:
            merged_obj = merged_objs[0]

        # *** 修改後的邏輯：先對正，後旋轉 ***

        # 1. 計算平移 (Alignment)
        translation_placement = FreeCAD.Placement()
        if self.do_align:
            doc_merged.recompute()
            # 獲取物件在 *本地* 座標系中的形心
            centroid_local = merged_obj.Shape.CenterOfMass
            
            # (假設物件初始 Placement 為 Identity 或我們只關心 Shape 的形心)
            # 我們要將 centroid_local 移動到 align_target
            target_vector = FreeCAD.Vector(self.align_target)
            
            # 計算從當前形心到目標位置所需的平移向量
            translation_vector = target_vector - centroid_local
            translation_placement.Base = translation_vector
            
            # (此時尚未真正應用平移，只計算了 Placement)

        # 2. 設置旋轉變換 (Rotation)
        rotation_placement = FreeCAD.Placement()
        rotation_placement.Rotation = FreeCAD.Rotation(FreeCAD.Vector(self.Fvector), self.Frotation)

        # 3. 組合變換
        # FreeCAD 中， P_total = P2 * P1 的意思是 "先應用 P1，再應用 P2"
        # 我們要先平移 (translation_placement)，再旋轉 (rotation_placement)
        total_placement = rotation_placement.multiply(translation_placement)

        # 4. 應用總變換
        merged_obj.Placement = total_placement
        doc_merged.recompute()

        # 儲存最終的變換
        # total_placement 已經是我們需要的最終變換

        # 匯出變換後的合併單一件
        Part.export([merged_obj], self.out_path_merged)
        # 關閉合併件文檔
        FreeCAD.closeDocument(doc_merged.Name)

        # --- 處理組合件 -----
        Import.open(self.in_path_assembly)
        doc_assembly = FreeCAD.ActiveDocument
        if doc_assembly is None:
            raise RuntimeError(f"Failed to open assembly file: {self.in_path_assembly}")

        # 第一步：先找出所有「有形狀」的候選物件
        valid_objects = []
        for obj in doc_assembly.Objects:
            # 必須有 Shape 且有面 (排除只有座標點的空物件)
            if hasattr(obj, 'Shape') and obj.Shape is not None and len(obj.Shape.Faces) > 0:
                valid_objects.append(obj)

        # 第二步：過濾掉「容器/組件」
        # 原理：如果 A 物件的依賴列表 (OutList) 裡面包含了 B 物件，
        # 且 B 物件也在我們的 valid_objects 裡，代表 A 是 B 的「父容器」。
        # 我們只想要 B (底層零件)，不想要 A (重複的殼)。
        
        shapes = []
        for obj in valid_objects:
            is_container = False
            
            # 檢查這個物件是否連結到其他有效物件
            for child in obj.OutList:
                if child in valid_objects:
                    is_container = True
                    break
            
            # 只有當它「不是」別人的容器時 (或是最底層物件時)，才加入
            if not is_container:
                shapes.append(obj.Shape.copy())

        if not shapes:
            FreeCAD.closeDocument(doc_assembly.Name)
            # 如果過濾太嚴格導致全空 (極少見)，則退回到抓取所有 valid_objects
            # 但通常上面的邏輯能正確處理 Step 結構
            raise ValueError("Assembly not found: No valid leaf shapes found.")

        # 建立 compound
        compound = Part.makeCompound(shapes)

        # 建立臨時文件來放置 compound
        tmp_doc = FreeCAD.newDocument("tmp_compound_doc")
        compound_obj = tmp_doc.addObject("Part::Feature", "Compound")
        compound_obj.Shape = compound
        
        # 應用變換
        compound_obj.Placement = total_placement
        tmp_doc.recompute()

        # 匯出
        Part.export([compound_obj], self.out_path_assembly)

        # 清理
        FreeCAD.closeDocument(tmp_doc.Name)
        FreeCAD.closeDocument(doc_assembly.Name)

        gc.collect()


def main(in_path_assembly, in_path_merged, out_path_assembly="out_assembly", out_path_merged="out_merged",
         mode='step', Fvector=(0, 0, 1), Frotation=0, do_align=True, align_target=(0,0,0)):
    
    Frotation = float(Frotation)

    # 確保 Fvector 是 tuple 並且內部是 float
    if isinstance(Fvector, str):
        Fvector = tuple(map(float, Fvector.split(",")))  
    
    # 確保 align_target 是 tuple 並且內部是 float
    if isinstance(align_target, str):
        align_target = tuple(map(float, align_target.split(",")))
    elif isinstance(align_target, (list, tuple)):
         align_target = tuple(map(float, align_target))


    a = transform_moving(in_path_assembly, in_path_merged, out_path_assembly=out_path_assembly,  
                         out_path_merged=out_path_merged, mode=mode, Fvector=Fvector,  
                         Frotation=Frotation, do_align=do_align, align_target=align_target)
    a.STEPtoSTEP()
    return a

if __name__ == "__main__":
    if len(sys.argv) < 6:
        print("Usage: python transform_FreeCAD.py <in_path_assembly> <in_path_merged> <out_path_assembly> <out_path_merged> <mode> [Fvector] [Frotation] [align_target]")
    else:
        in_path_assembly = sys.argv[1]
        in_path_merged = sys.argv[2]
        out_path_assembly = sys.argv[3] if len(sys.argv) > 3 else "out_assembly"
        out_path_merged = sys.argv[4] if len(sys.argv) > 4 else "out_merged"
        mode = sys.argv[5] if len(sys.argv) > 5 else "step"
        Fvector = sys.argv[6] if len(sys.argv) > 6 else "0,0,1"
        Frotation = sys.argv[7] if len(sys.argv) > 7 else 0
        align_target_str = sys.argv[8] if len(sys.argv) > 8 else "0,0,0" # 新增對正目標參數

        # 轉換 Fvector
        if isinstance(Fvector, str):
            Fvector = tuple(map(float, Fvector.split(",")))  
            
        # 轉換 align_target
        try:
            align_target = tuple(map(float, align_target_str.split(",")))
        except:
            print(f"Invalid align_target format: {align_target_str}. Using (0,0,0).")
            align_target = (0.0, 0.0, 0.0)

        main(in_path_assembly, in_path_merged, out_path_assembly, out_path_merged, mode,  
             Fvector, Frotation, True, align_target)