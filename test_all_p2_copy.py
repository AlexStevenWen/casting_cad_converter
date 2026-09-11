from cad_converter import process_3d_file_unified_batch
import transform_3D_batch 
import pandas as pd
import os
import shutil
from ShapeCastDATA import PdReadShape
from SySPath import ChynWangDatapy , ChynWangPojectpy
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.subplots as sp
from tqdm import tqdm
import numpy as np
import csv
import transform_3D_batch
CW_root = ChynWangDatapy()
CP_root = ChynWangPojectpy()

CAD_source_root = os.path.join(CP_root,"data", "access_raw_CAD")
CAD_input_root = os.path.join(CP_root, "data", "step_file_raw")

processed_table_root = os.path.join(CP_root, "data", "processed_table")
processed_CAD_root = os.path.join(CP_root, "data", "processed_CAD")

# transform_3D_batch.copy_cad_files_based_on_csv_v2(CAD_source_root,
#                                                processed_CAD_root +  "\step_raw_component",
#                                                processed_table_root + "\cast_table_dataset.csv")



# transform_3D_batch.batch_transform_Step_to_3D_OCC(input_dir=processed_CAD_root + "\step_raw_component",
#                                                  output_dir=processed_CAD_root +  "\step_raw_merge",
#                                       mode=".step")



# transform_3D_batch.batch_transform_Step_to_3D_moving_double(
#     input_dir_assembly= processed_CAD_root + "\step_raw_component",
#     input_dir_merged=processed_CAD_root + "\step_raw_merge",
#     output_dir_assembly=processed_CAD_root + "\step_raw_center_component",
#     output_dir_merged=processed_CAD_root + "\step_raw_center_merge", # 這裡指定輸出資料夾
#     mode=".step",
#     Fvector=(0, 0, 0),
#     Frotation=0
#     )

# transform_3D_batch.batch_transform_Step_to_3D_moving_double(
#     input_dir_assembly= processed_CAD_root + "\step_raw_center_component",
#     input_dir_merged=processed_CAD_root + "\step_raw_center_merge",
#     output_dir_assembly=processed_CAD_root + "\step_upright_z_component",
#     output_dir_merged=processed_CAD_root + "\step_upright_z_merge", # 這裡指定輸出資料夾
#     mode=".step",
#     Fvector=(1, 0, 0),
#     Frotation=-90
#     )

#transform_3D_batch.batch_transform_Step_to_3D_OCCseg(processed_CAD_root + r"\step_upright_z_component",processed_CAD_root + r"\step_upright_z_parts")

transform_3D_batch.batch_transform_Step_to_3D_OCCsegre(processed_CAD_root + r"\step_upright_z_component\blank",processed_CAD_root + r"\step_upright_z_parts\tree",processed_CAD_root + r"\csv_identify_parts",)

