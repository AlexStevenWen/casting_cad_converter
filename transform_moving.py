import sys
import os
import FreeCAD
import Mesh
import Import
import Part
import io
import gc
import traceback
import logging

# ==========================================
# 🛠️ 100% Forced real-time flush, zero-loss Logger settings
# ==========================================
log_filename = "transform_process.log"
logger = logging.getLogger("FreeCAD_Transform")
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    # Custom handler to forcefully flush logs to the disk immediately upon receipt, preventing log loss if FreeCAD crashes
    class FlushFileHandler(logging.FileHandler):
        def emit(self, record):
            super().emit(record)
            self.flush()

    try:
        # Use mode='a' to append records
        file_handler = FlushFileHandler(log_filename, encoding='utf-8', mode='a')
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter('%(asctime)s [%(levelname)s] (Line: %(lineno)d) %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    except Exception as log_err:
        print(f"Failed to create Log File Handler: {log_err}")

    # Screen Stream Handler
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_formatter = logging.Formatter('[%(levelname)s] %(message)s')
    stream_handler.setFormatter(stream_formatter)
    logger.addHandler(stream_handler)


class transform_moving:
    def __init__(self, in_path_assembly, in_path_merged, out_path_assembly="out_assembly", out_path_merged="out_merged", mode='step',
                 Fvector=(0, 0, 1), Frotation=0, do_align=True, align_target=(0, 0, 0)):
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
        """
        Process two input files, calculate translation and rotation, and output them with built-in log recording.
        """
        doc_merged = None
        doc_assembly = None
        tmp_doc = None

        # --- 1. Process the merged single part ---
        logger.info(f"============ New Task Started ============")
        logger.info(f"[Merged Part] Start processing input file: {self.in_path_merged}")
        
        try:
            if not os.path.exists(self.in_path_merged):
                raise FileNotFoundError(f"Physical file does not exist: {self.in_path_merged}")

            Import.open(self.in_path_merged)
            doc_merged = FreeCAD.ActiveDocument
            if doc_merged is None:
                raise RuntimeError(f"FreeCAD cannot open this merged part, the file may be corrupted.")

            # Filter objects that have a Shape
            merged_objs = [obj for obj in doc_merged.Objects if hasattr(obj, 'Shape')]
            if len(merged_objs) == 0:
                raise ValueError(f"No objects containing a Shape found in the merged part.")
            
            if len(merged_objs) > 1:
                logger.warning(f"Multiple Shape objects found in the merged part, selecting the first one by default: {merged_objs[0].Name}")
            
            merged_obj = merged_objs[0]

            # Geometric alignment and rotation calculations
            translation_placement = FreeCAD.Placement()
            if self.do_align:
                doc_merged.recompute()
                centroid_local = merged_obj.Shape.CenterOfMass
                target_vector = FreeCAD.Vector(self.align_target)
                translation_vector = target_vector - centroid_local
                translation_placement.Base = translation_vector
                logger.info(f"[Alignment] Calculated centroid successfully: {centroid_local} -> Target: {target_vector}")

            rotation_placement = FreeCAD.Placement()
            rotation_placement.Rotation = FreeCAD.Rotation(FreeCAD.Vector(self.Fvector), self.Frotation)

            total_placement = rotation_placement.multiply(translation_placement)
            merged_obj.Placement = total_placement
            doc_merged.recompute()

            # Automatically create output directory
            out_merged_dir = os.path.dirname(self.out_path_merged)
            if out_merged_dir and not os.path.exists(out_merged_dir):
                os.makedirs(out_merged_dir, exist_ok=True)

            Part.export([merged_obj], self.out_path_merged)
            logger.info(f"[Success] The transformed merged part has been exported to: {self.out_path_merged}")

        except Exception as e:
            logger.error(f"[Failure] A fatal error occurred while processing the merged part: {str(e)}")
            logger.error(traceback.format_exc())  # Forcefully write detailed traceback lines to the file
            raise e
        finally:
            if doc_merged is not None:
                FreeCAD.closeDocument(doc_merged.Name)
                logger.info(f"Closed merged part document memory cache.")

        # --- 2. Process the assembly -----
        logger.info(f"[Assembly] Start processing input file: {self.in_path_assembly}")
        try:
            if not os.path.exists(self.in_path_assembly):
                raise FileNotFoundError(f"Physical file does not exist: {self.in_path_assembly}")

            Import.open(self.in_path_assembly)
            doc_assembly = FreeCAD.ActiveDocument
            if doc_assembly is None:
                raise RuntimeError(f"FreeCAD cannot open this assembly.")

            # Find all non-empty candidate objects
            valid_objects = []
            for obj in doc_assembly.Objects:
                if hasattr(obj, 'Shape') and obj.Shape is not None and len(obj.Shape.Faces) > 0:
                    valid_objects.append(obj)

            # Filter out assembly containers
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
                raise ValueError("After filtering the assembly structure, no valid leaf shapes were found.")

            logger.info(f"[Assembly] Successfully filtered leaf shape count: {len(shapes)} parts")

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
            logger.info(f"[Success] The transformed assembly has been exported to: {self.out_path_assembly}")

        except Exception as e:
            logger.error(f"[Failure] A fatal error occurred while processing the assembly: {str(e)}")
            logger.error(traceback.format_exc())
            raise e
        finally:
            if tmp_doc is not None:
                FreeCAD.closeDocument(tmp_doc.Name)
            if doc_assembly is not None:
                FreeCAD.closeDocument(doc_assembly.Name)
                logger.info(f"Cleared assembly and temporary document memory.")
            gc.collect()


def main(in_path_assembly, in_path_merged, out_path_assembly="out_assembly", out_path_merged="out_merged",
         mode='step', Fvector=(0, 0, 1), Frotation=0, do_align=True, align_target=(0,0,0)):
    
    try:
        Frotation = float(Frotation)
    except ValueError:
        logger.error(f"Input parameter error: Frotation must be a numeric value, received '{Frotation}'")
        return None

    if isinstance(Fvector, str):
        try:
            Fvector = tuple(map(float, Fvector.split(",")))  
        except ValueError:
            logger.error(f"Input parameter error: Fvector format should be x,y,z, received '{Fvector}'")
            return None
    
    if isinstance(align_target, str):
        try:
            align_target = tuple(map(float, align_target.split(",")))
        except ValueError:
            logger.warning(f"Failed to parse align_target, using default (0,0,0). Received '{align_target}'")
            align_target = (0.0, 0.0, 0.0)
    elif isinstance(align_target, (list, tuple)):
         align_target = tuple(map(float, align_target))

    try:
        a = transform_moving(in_path_assembly, in_path_merged, out_path_assembly=out_path_assembly,  
                             out_path_merged=out_path_merged, mode=mode, Fvector=Fvector,  
                             Frotation=Frotation, do_align=do_align, align_target=align_target)
        a.STEPtoSTEP()
        return a
    except Exception:
        logger.critical("❌ The transformation task has been completely aborted due to the above exceptions.")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("\n[ERROR] Insufficient parameters!")
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
            Fvector = (0.0, 0.0, 1.0)
            
    try:
        align_target = tuple(map(float, align_target_str.split(",")))
    except ValueError:
        align_target = (0.0, 0.0, 0.0)

    main(in_path_assembly, in_path_merged, out_path_assembly, out_path_merged, mode,  
         Fvector, Frotation, True, align_target)