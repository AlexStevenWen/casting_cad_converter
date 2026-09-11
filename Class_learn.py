
import os
from tqdm import tqdm
from collections import defaultdict
import numpy as np
from transform_3D import transform_3D,Parameter_DATA , STL_DATA ,STL_Simplified, transform_Step_OCC,transform_moving_step , transform_Step_OCCseg,transform_stlmerge,transform_OCCstl, transform_step_cloud,transform_Step_OCCsegre,transform_Cloud_2D,STEPto2D,transform_Cloud_STL_2D
from pc_surface_detection import process_assembly_data_gen ,visualize_dataset
import shutil
import pandas as pd
import glob
import pc_surface_detection


#圖檔合併
transform_Step_OCC(step_file, cad_file)

#重心定位
transform_moving_step(
                        asm_path, mer_path,
                        out_asm, out_mer,
                        mode=mode, Fvector=Fvector, Frotation=Frotation
                    )
#重心旋轉
transform_moving_step(
                        asm_path, mer_path,
                        out_asm, out_mer,
                        mode=mode, Fvector=Fvector, Frotation=Frotation
                    )
transform_3D_batch.batch_transform_Step_to_3D_moving_double(
    input_dir_assembly= processed_CAD_root + "\step_raw_component",
    input_dir_merged=processed_CAD_root + "\step_raw_merge",
    output_dir_assembly=processed_CAD_root + "\step_raw_center_component",
    output_dir_merged=processed_CAD_root + "\step_raw_center_merge", # 這裡指定輸出資料夾
    mode=".step",
    Fvector=(0, 0, 0),
    Frotation=0
    )
#圖檔轉STL
transform_3D(
                in_path=step_file,
                out_put=cad_file,
                Fvector=Fvector,
                Frotation=Frotation,
                tolerance=tolerance,
                tessellate_value=tessellate
            )


transform_3D_batch.batch_transform_Step_to_3D(
                                      input_dir=processed_CAD_root + "\step_raw_component",
                                      output_dir=processed_CAD_root +  "\stl_raw_componet",
                                      mode=".stl")
#CAD分割圖檔
transform_Step_OCCseg(step_file, cad_file)


#圖檔轉
transform_3D_batch.batch_transform_Step_to_3D_OCCsegre(processed_CAD_root + r"\step_upright_z_component\blank",processed_CAD_root + r"\step_upright_z_parts\tree",processed_CAD_root + r"\csv_identify_parts",)

