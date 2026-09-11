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
csv_identify_dir = os.path.join(processed_CAD_root, "csv_identify_parts")

samplings = ['random','fps','surface_uniform']
#"binary"
contacts = ["local_linear","gaussian", "flat_core_gaussian", "global_linear", "global_gaussian","global_flat_core_gaussian"]
for exp in range(12, 13):
    for contact in contacts:
        for s in samplings:

            size_str = str(2**exp)
            print(size_str)
            # 1. 定義輸入與輸出的路徑
            input_cloud_dir = os.path.join(processed_CAD_root,"normalcloud_upright_z", f"normalcloud_upright_z_parts_{s}_{size_str}", "tree")
            
            # 2. 定義 Contact Binary 的路徑
            contact_binary_dir= os.path.join(processed_CAD_root,"normalcloud_upright_z", f"normalcloud_upright_z_parts_{s}_{contact}_binary_{size_str}", "tree")
            print(f"--- 正在處理 2^{exp} (Size: {size_str}) ---")

            # 執行 Contact Generation
            transform_3D_batch.batch_process_contact_gen(
                input_cloud_dir,
                contact_binary_dir,
                label_mode=contact
            )

            transform_3D_batch.batch_rename_and_copy_by_mode(
                csv_identify_dir,
                os.path.join(contact_binary_dir),
                os.path.join(processed_CAD_root,"normalcloud_upright_z_identify", f"normalcloud_upright_z_parts_{s}_{contact}_identify_{size_str}", "tree")
            )

        print("所有批次任務已完成！")