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
# 定義輸入路徑，避免在迴圈內重複拼接
input_dir = os.path.join(processed_CAD_root, "stl_upright_z_parts")
"""
for i in range(10, 15):
    num_points = 2**i
    # 動態生成輸出路徑
    output_dir = os.path.join(
        processed_CAD_root, 
        "normal_cloud", 
        f"normal_cloud_upright_z_parts_random_{num_points}"
    )
    
    # 執行轉換
    transform_3D_batch.batch_transform_Stl_to_normalcloud(
        input_dir,
        output_dir,
        point_num=num_points,
        sampling="random"
    )

for i in range(10, 15):
    num_points = 2**i
    # 動態生成輸出路徑
    output_dir = os.path.join(
        processed_CAD_root, 
        "normal_cloud", 
        f"normal_cloud_upright_z_parts_fps_{num_points}"
    )
    
    # 執行轉換
    transform_3D_batch.batch_transform_Stl_to_normalcloud(
        input_dir,
        output_dir,
        point_num=num_points,
        sampling="fps"
    )
"""
for i in range(10, 15):
    num_points = 2**i
    # 動態生成輸出路徑
    output_dir = os.path.join(
        processed_CAD_root, 
        "normal_cloud", 
        f"normal_cloud_upright_z_parts_surface_uniform_{num_points}"
    )
    
    # 執行轉換
    transform_3D_batch.batch_transform_Stl_to_normalcloud(
        input_dir,
        output_dir,
        point_num=num_points,
        sampling="surface_uniform"
    )