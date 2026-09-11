import sys
import os
import FreeCAD
import Mesh
import Import
import Part
import io
import gc
import traceback
import logging  # 引入內建日誌模組
log_filename = "transform_process.log"

# 建立 Logger
logger = logging.getLogger("FreeCAD_Transform")
logger.setLevel(logging.DEBUG)  # 捕捉所有層級的日誌

# 避免重複添加 Handler (在某些環境下重複 import 會導致重複印 Log)
if not logger.handlers:
    # 1. 檔案 Handler (記錄詳細時間與訊息，編碼指定為 utf-8 避免中文亂碼)
    file_handler = logging.FileHandler(log_filename, encoding='utf-8', mode='a')
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # 2. 螢幕 Handler (讓你在終端機也能即時看到)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_formatter = logging.Formatter('[%(levelname)s] %(message)s')
    stream_handler.setFormatter(stream_formatter)
    logger.addHandler(stream_handler)
class transform_moving:
    def __init__(self, in_path_assembly, in_path_merged, out_path_assembly="out_assembly", out_path_merged="out_merged", mode='step',
                 Fvector=(0, 0, 1), Frotation=0, do_align=True, align_target=(0, 0, 0)):
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
self.in_path_assembly = in_path_assembly  
        self.in_path_merged = in_path_merged      
        self.out_path_assembly = out_path_assembly  
        self.out_path_merged = out_path_merged      
        self.mode = '.' + mode
        self.Fvector = Fvector  
        self.Frotation = Frotation  
        self.do_align = do_align
        self.align_target = align_target

    def STEPtoSTEP(self):
        doc_merged = None
        doc_assembly = None
        tmp_doc = None

        # --- 1. 處理合併單一件 ---
        logger.info(f"開始處理合併單一件: {self.in_path_merged}")
        try:
            if not os.path.exists(self.in_path_merged):
                raise FileNotFoundError(f"找不到合併件檔案: {self.in_path_merged}")

            Import.open(self.in_path_merged)
            doc_merged = FreeCAD.ActiveDocument
            if doc_merged is None:
                raise RuntimeError(f"FreeCAD 無法開啟合併件: {self.in_path_merged}")

            merged_objs = [obj for obj in doc_merged.Objects if hasattr(obj, 'Shape')]
            if len(merged_objs) == 0:
                raise ValueError(f"合併件中找不到任何含有 Shape 的物件: {self.in_path_merged}")
            
            if len(merged_objs) > 1:
                logger.warning(f"合併件中發現多個 Shape 物件，預設選取第一個: {merged_objs[0].Name}")
            
            merged_obj = merged_objs[0]

            # 幾何變換計算
            translation_placement = FreeCAD.Placement()
            if self.do_align:
                doc_merged.recompute()
                centroid_local = merged_obj.Shape.CenterOfMass
                target_vector = FreeCAD.Vector(self.align_target)
                translation_vector = target_vector - centroid_local
                translation_placement.Base = translation_vector

            rotation_placement = FreeCAD.Placement()
            rotation_placement.Rotation = FreeCAD.Rotation(FreeCAD.Vector(self.Fvector), self.Frotation)

            total_placement = rotation_placement.multiply(translation_placement)

            merged_obj.Placement = total_placement
            doc_merged.recompute()

            # 確保輸出目錄存在
            out_merged_dir = os.path.dirname(self.out_path_merged)
            if out_merged_dir and not os.path.exists(out_merged_dir):
                os.makedirs(out_merged_dir, exist_ok=True)

            Part.export([merged_obj], self.out_path_merged)
            logger.info(f"成功導出變換後的合併件: {self.out_path_merged}")

        except Exception as e:
            logger.error(f"處理合併件時發生錯誤！錯誤原因: {str(e)}")
            # 將詳細的報錯行數 (Traceback) 轉成字串寫入 Log 檔案
            logger.error(traceback.format_exc())
            raise e
        finally:
            if doc_merged is not None:
                FreeCAD.closeDocument(doc_merged.Name)
                logger.info(f"已關閉合併件文檔: {doc_merged.Name}")

        # --- 2. 處理組合件 -----
        logger.info(f"開始處理組合件: {self.in_path_assembly}")
        try:
            if not os.path.exists(self.in_path_assembly):
                raise FileNotFoundError(f"找不到組合件檔案: {self.in_path_assembly}")

            Import.open(self.in_path_assembly)
            doc_assembly = FreeCAD.ActiveDocument
            if doc_assembly is None:
                raise RuntimeError(f"FreeCAD 無法開啟組合件: {self.in_path_assembly}")

            valid_objects = []
            for obj in doc_assembly.Objects:
                if hasattr(obj, 'Shape') and obj.Shape is not None:
                    if len(obj.Shape.Faces) > 0 or len(obj.Shape.Edges) > 0:
                        valid_objects.append(obj)

            shapes = []
            for obj in valid_objects:
                is_container = False
                for child in obj.OutList:
                    if child in valid_objects:
                        is_container = True
                        break
                if not is_container:
                    shapes.append(obj.Shape.copy())

            if not shapes:
                raise ValueError("組合件過濾後未發現任何有效的底層零件形狀 (Leaf Shapes)。")

            compound = Part.makeCompound(shapes)

            tmp_doc = FreeCAD.newDocument("tmp_compound_doc")
            compound_obj = tmp_doc.addObject("Part::Feature", "Compound")
            compound_obj.Shape = compound
            
            compound_obj.Placement = total_placement
            tmp_doc.recompute()

            out_assembly_dir = os.path.dirname(self.out_path_assembly)
            if out_assembly_dir and not os.path.exists(out_assembly_dir):
                os.makedirs(out_assembly_dir, exist_ok=True)

            Part.export([compound_obj], self.out_path_assembly)
            logger.info(f"成功導出變換後的組合件: {self.out_path_assembly}")

        except Exception as e:
            logger.error(f"處理組合件時發生錯誤！錯誤原因: {str(e)}")
            logger.error(traceback.format_exc())
            raise e
        finally:
            if tmp_doc is not None:
                FreeCAD.closeDocument(tmp_doc.Name)
            if doc_assembly is not None:
                FreeCAD.closeDocument(doc_assembly.Name)
                logger.info(f"已關閉組合件與臨時文檔")
            
            gc.collect()


def main(in_path_assembly, in_path_merged, out_path_assembly="out_assembly", out_path_merged="out_merged",
         mode='step', Fvector=(0, 0, 1), Frotation=0, do_align=True, align_target=(0,0,0)):
    
    try:
        Frotation = float(Frotation)
    except ValueError:
        logger.error(f"旋轉角度 Frotation 必須為數值，收到: {Frotation}")
        return None

    if isinstance(Fvector, str):
        try:
            Fvector = tuple(map(float, Fvector.split(",")))  
        except ValueError:
            logger.error(f"Fvector 格式錯誤，應為 'x,y,z'，收到: {Fvector}")
            return None
    
    if isinstance(align_target, str):
        try:
            align_target = tuple(map(float, align_target.split(",")))
        except ValueError:
            logger.warning(f"align_target 格式錯誤，改用預設值 (0,0,0)。收到: {align_target}")
            align_target = (0.0, 0.0, 0.0)
    elif isinstance(align_target, (list, tuple)):
         align_target = tuple(map(float, align_target))

    try:
        a = transform_moving(in_path_assembly, in_path_merged, out_path_assembly=out_path_assembly,  
                             out_path_merged=out_path_merged, mode=mode, Fvector=Fvector,  
                             Frotation=Frotation, do_align=do_align, align_target=align_target)
        a.STEPtoSTEP()
        return a
    except Exception as main_err:
        logger.critical(f"轉換任務最終失敗，詳情請查看上方 Error Log。")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("\n[ERROR] 參數不足！")
        print("Usage: python transform_FreeCAD.py <in_path_assembly> <in_path_merged> [out_path_assembly] [out_path_merged] [mode] [Fvector] [Frotation] [align_target]")
        sys.exit(1)
        
    in_path_assembly = sys.argv[1]
    in_path_merged = sys.argv[2]
    
    out_path_assembly = sys.argv[3] if len(sys.argv) > 3 else "out_assembly.step"
    out_path_merged = sys.argv[4] if len(sys.argv) > 4 else "out_merged.step"
    mode = sys.argv[5] if len(sys.argv) > 5 else "step"
    Fvector = sys.argv[6] if len(sys.argv) > 6 else "0,0,1"
    Frotation = sys.argv[7] if len(sys.argv) > 7 else 0
    align_target_str = sys.argv[8] if len(sys.argv) > 8 else "0,0,0"

    if isinstance(Fvector, str):
        try:
            Fvector = tuple(map(float, Fvector.split(",")))  
        except ValueError:
            logger.warning(f"終端機傳入的 Fvector 格式有誤 '{Fvector}'，改用預設 Z 軸 (0,0,1)")
            Fvector = (0.0, 0.0, 1.0)
            
    try:
        align_target = tuple(map(float, align_target_str.split(",")))
    except ValueError:
        logger.warning(f"終端機傳入的 align_target 格式有誤 '{align_target_str}'，改用預設值 (0,0,0).")
        align_target = (0.0, 0.0, 0.0)

    main(in_path_assembly, in_path_merged, out_path_assembly, out_path_merged, mode,  
         Fvector, Frotation, True, align_target)