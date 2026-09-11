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
#'random, 'surface_uniform''
samplings = ['fps']
# for sampling in samplings:
#     for i in range(10, 17):
#         # 計算當前的點數 (2^10 到 2^16)
#         pts = 2 ** i 
        
#         # 組合路徑
#         input_path = processed_CAD_root + r"\stl_upright_z_merge"
#         output_path = processed_CAD_root + fr"\normalcloud_upright_z\normalcloud_upright_z_merge_{sampling}_{pts}"
        
#         # 執行轉換
#         transform_3D_batch.batch_transform_Stl_to_normalcloud(
#             input_path, 
#             output_path, 
#             point_num=pts,sampling=sampling
#         )
#fps,random,surface_uniform

samplings = ["surface_uniform"]
for sampling in samplings:
    for i in range(12, 13):
        
        # 計算當前的點數 (2^10 到 2^16)
        pts = 2 ** i 
        print(pts)
        # 組合路徑
        input_path = processed_CAD_root + r"\stl_upright_z_parts"
        output_path = processed_CAD_root + fr"\normalcloud_upright_z\normalcloud_upright_z_parts_{sampling}_{pts}"
        
        # 執行轉換
        transform_3D_batch.batch_transform_Stl_to_normalcloud(
            input_path, 
            output_path, 
            point_num=pts,sampling=sampling
        )


