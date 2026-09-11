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
for exp in range(13, 15):
    size_str = str(2**exp)
    
    # 1. 定義輸入與輸出的路徑
    input_cloud_dir = os.path.join(processed_CAD_root, "normal_cloud", f"normal_cloud_upright_z_parts_random_{size_str}")
    
    # 2. 定義 Contact auto_detect_plateau 的路徑
    contact_auto_detect_plateau_dir = os.path.join(processed_CAD_root, "normal_cloud", f"normal_cloud_upright_z_parts_random_contact_auto_detect_plateau_{size_str}")
    
    # 3. 定義 Identify 的路徑
    csv_identify_dir = os.path.join(processed_CAD_root, "csv_identify_parts")
    final_output_dir = os.path.join(processed_CAD_root, "normal_cloud", f"normal_cloud_upright_z_parts_random_contact_auto_detect_plateau_auto_detect_plateau_{size_str}")

    print(f"--- 正在處理 2^{exp} (Size: {size_str}) ---")

    # 執行 Contact Generation
    transform_3D_batch.batch_process_contact_gen(
        input_cloud_dir,
        contact_auto_detect_plateau_dir,
        label_mode="auto_detect_plateau"
    )

    # 執行 Rename 與 Copy
    transform_3D_batch.batch_rename_and_copy_by_mode(
        csv_identify_dir,
        os.path.join(contact_auto_detect_plateau_dir,"tree"),
        os.path.join(final_output_dir,"tree")
    )

# print("所有批次任務已完成！")

# for exp in range(13, 15):
#     size_str = str(2**exp)
    
#     # 1. 定義輸入與輸出的路徑
#     input_cloud_dir = os.path.join(processed_CAD_root, "normal_cloud", f"normal_cloud_upright_z_parts_fps_{size_str}")
    
#     # 2. 定義 Contact auto_detect_plateau 的路徑
#     contact_auto_detect_plateau_dir = os.path.join(processed_CAD_root, "normal_cloud", f"normal_cloud_upright_z_parts_fps_contact_auto_detect_plateau_{size_str}")
    
#     # 3. 定義 Identify 的路徑
#     csv_identify_dir = os.path.join(processed_CAD_root, "csv_identify_parts")
#     final_output_dir = os.path.join(processed_CAD_root, "normal_cloud", f"normal_cloud_upright_z_parts_fps_contact_auto_detect_plateau_identify_{size_str}")

#     print(f"--- 正在處理 2^{exp} (Size: {size_str}) ---")

#     # 執行 Contact Generation
#     transform_3D_batch.batch_process_contact_gen(
#         input_cloud_dir,
#         contact_auto_detect_plateau_dir,
#         label_mode="auto_detect_plateau"
#     )

#     # 執行 Rename 與 Copy
#     transform_3D_batch.batch_rename_and_copy_by_mode(
#         csv_identify_dir,
#         os.path.join(contact_auto_detect_plateau_dir,"tree"),
#         os.path.join(final_output_dir,"tree")
#     )

# print("所有批次任務已完成！")

# for exp in range(13, 15):
#     size_str = str(2**exp)
    
#     # 1. 定義輸入與輸出的路徑
#     input_cloud_dir = os.path.join(processed_CAD_root, "normal_cloud", f"normal_cloud_upright_z_parts_surface_uniform_{size_str}")
    
#     # 2. 定義 Contact auto_detect_plateau 的路徑
#     contact_auto_detect_plateau_dir = os.path.join(processed_CAD_root, "normal_cloud", f"normal_cloud_upright_z_parts_surface_uniform_contact_auto_detect_plateau_{size_str}")
    
#     # 3. 定義 Identify 的路徑
#     csv_identify_dir = os.path.join(processed_CAD_root, "csv_identify_parts")
#     final_output_dir = os.path.join(processed_CAD_root, "normal_cloud", f"normal_cloud_upright_z_parts_surface_uniform_contact_auto_detect_plateau_auto_detect_plateau_{size_str}")

#     print(f"--- 正在處理 2^{exp} (Size: {size_str}) ---")

#     # 執行 Contact Generation
#     transform_3D_batch.batch_process_contact_gen(
#         input_cloud_dir,
#         contact_auto_detect_plateau_dir,
#         label_mode="auto_detect_plateau"
#     )

#     # 執行 Rename 與 Copy
#     transform_3D_batch.batch_rename_and_copy_by_mode(
#         csv_identify_dir,
#         os.path.join(contact_auto_detect_plateau_dir,"tree"),
#         os.path.join(final_output_dir,"tree")
#     )

# print("所有批次任務已完成！")

# for exp in range(13, 15):
#     size_str = str(2**exp)
    
#     # 1. 定義輸入與輸出的路徑
#     input_cloud_dir = os.path.join(processed_CAD_root, "normal_cloud", f"normal_cloud_upright_z_parts_fps_{size_str}")
    
#     # 2. 定義 Contact auto_detect_plateau 的路徑
#     contact_auto_detect_plateau_dir = os.path.join(processed_CAD_root, "normal_cloud", f"normal_cloud_upright_z_parts_fps_contact_auto_detect_plateau_{size_str}")
    
#     # 3. 定義 Identify 的路徑
#     csv_identify_dir = os.path.join(processed_CAD_root, "csv_identify_parts")
#     final_output_dir = os.path.join(processed_CAD_root, "normal_cloud", f"normal_cloud_upright_z_parts_fps_contact_auto_detect_plateau_identify_{size_str}")

#     print(f"--- 正在處理 2^{exp} (Size: {size_str}) ---")

#     # 執行 Contact Generation
#     transform_3D_batch.batch_process_contact_gen(
#         input_cloud_dir,
#         contact_auto_detect_plateau_dir,
#         label_mode="auto_detect_plateau"
#     )

#     # 執行 Rename 與 Copy
#     transform_3D_batch.batch_rename_and_copy_by_mode(
#         csv_identify_dir,
#         os.path.join(contact_auto_detect_plateau_dir,"tree"),
#         os.path.join(final_output_dir,"tree")
#     )

# print("所有批次任務已完成！")

# for exp in range(13, 15):
#     size_str = str(2**exp)
    
#     # 1. 定義輸入與輸出的路徑
#     input_cloud_dir = os.path.join(processed_CAD_root, "normal_cloud", f"normal_cloud_upright_z_parts_surface_uniform_{size_str}")
    
#     # 2. 定義 Contact auto_detect_plateau 的路徑
#     contact_auto_detect_plateau_dir = os.path.join(processed_CAD_root, "normal_cloud", f"normal_cloud_upright_z_parts_surface_uniform_contact_auto_detect_plateau_{size_str}")
    
#     # 3. 定義 Identify 的路徑
#     csv_identify_dir = os.path.join(processed_CAD_root, "csv_identify_parts")
#     final_output_dir = os.path.join(processed_CAD_root, "normal_cloud", f"normal_cloud_upright_z_parts_surface_uniform_contact_auto_detect_plateau_identify_{size_str}")

#     print(f"--- 正在處理 2^{exp} (Size: {size_str}) ---")

#     # 執行 Contact Generation
#     transform_3D_batch.batch_process_contact_gen(
#         input_cloud_dir,
#         contact_auto_detect_plateau_dir,
#         label_mode="auto_detect_plateau"
#     )

#     # 執行 Rename 與 Copy
#     transform_3D_batch.batch_rename_and_copy_by_mode(
#         csv_identify_dir,
#         os.path.join(contact_auto_detect_plateau_dir,"tree"),
#         os.path.join(final_output_dir,"tree")
#     )

# print("所有批次任務已完成！")
for exp in range(13, 15):
    size_str = str(2**exp)
    
    # 1. 定義輸入與輸出的路徑
    input_cloud_dir = os.path.join(processed_CAD_root, "normal_cloud", f"normal_cloud_upright_z_parts_random_{size_str}")
    
    # 2. 定義 Contact global_gaussian 的路徑
    contact_global_gaussian_dir = os.path.join(processed_CAD_root, "normal_cloud", f"normal_cloud_upright_z_parts_random_contact_global_gaussian_{size_str}")
    
    # 3. 定義 Identify 的路徑
    csv_identify_dir = os.path.join(processed_CAD_root, "csv_identify_parts")
    final_output_dir = os.path.join(processed_CAD_root, "normal_cloud", f"normal_cloud_upright_z_parts_random_contact_global_gaussian_global_identify_{size_str}")

    print(f"--- 正在處理 2^{exp} (Size: {size_str}) ---")

    # 執行 Contact Generation
    transform_3D_batch.batch_process_contact_gen(
        input_cloud_dir,
        contact_global_gaussian_dir,
        label_mode="global_gaussian"
    )

    # 執行 Rename 與 Copy
    transform_3D_batch.batch_rename_and_copy_by_mode(
        csv_identify_dir,
        os.path.join(contact_global_gaussian_dir,"tree"),
        os.path.join(final_output_dir,"tree")
    )

print("所有批次任務已完成！")

# for exp in range(13, 15):
#     size_str = str(2**exp)
    
#     # 1. 定義輸入與輸出的路徑
#     input_cloud_dir = os.path.join(processed_CAD_root, "normal_cloud", f"normal_cloud_upright_z_parts_fps_{size_str}")
    
#     # 2. 定義 Contact global_gaussian 的路徑
#     contact_global_gaussian_dir = os.path.join(processed_CAD_root, "normal_cloud", f"normal_cloud_upright_z_parts_fps_contact_global_gaussian_{size_str}")
    
#     # 3. 定義 Identify 的路徑
#     csv_identify_dir = os.path.join(processed_CAD_root, "csv_identify_parts")
#     final_output_dir = os.path.join(processed_CAD_root, "normal_cloud", f"normal_cloud_upright_z_parts_fps_contact_global_gaussian_identify_{size_str}")

#     print(f"--- 正在處理 2^{exp} (Size: {size_str}) ---")

#     # 執行 Contact Generation
#     transform_3D_batch.batch_process_contact_gen(
#         input_cloud_dir,
#         contact_global_gaussian_dir,
#         label_mode="global_gaussian"
#     )

#     # 執行 Rename 與 Copy
#     transform_3D_batch.batch_rename_and_copy_by_mode(
#         csv_identify_dir,
#         os.path.join(contact_global_gaussian_dir,"tree"),
#         os.path.join(final_output_dir,"tree")
#     )

# print("所有批次任務已完成！")

# for exp in range(13, 15):
#     size_str = str(2**exp)
    
#     # 1. 定義輸入與輸出的路徑
#     input_cloud_dir = os.path.join(processed_CAD_root, "normal_cloud", f"normal_cloud_upright_z_parts_surface_uniform_{size_str}")
    
#     # 2. 定義 Contact global_gaussian 的路徑
#     contact_global_gaussian_dir = os.path.join(processed_CAD_root, "normal_cloud", f"normal_cloud_upright_z_parts_surface_uniform_contact_global_gaussian_{size_str}")
    
#     # 3. 定義 Identify 的路徑
#     csv_identify_dir = os.path.join(processed_CAD_root, "csv_identify_parts")
#     final_output_dir = os.path.join(processed_CAD_root, "normal_cloud", f"normal_cloud_upright_z_parts_surface_uniform_contact_global_gaussian_global_gaussian_{size_str}")

#     print(f"--- 正在處理 2^{exp} (Size: {size_str}) ---")

#     # 執行 Contact Generation
#     transform_3D_batch.batch_process_contact_gen(
#         input_cloud_dir,
#         contact_global_gaussian_dir,
#         label_mode="global_gaussian"
#     )

#     # 執行 Rename 與 Copy
#     transform_3D_batch.batch_rename_and_copy_by_mode(
#         csv_identify_dir,
#         os.path.join(contact_global_gaussian_dir,"tree"),
#         os.path.join(final_output_dir,"tree")
#     )

# print("所有批次任務已完成！")

# for exp in range(13, 15):
#     size_str = str(2**exp)
    
#     # 1. 定義輸入與輸出的路徑
#     input_cloud_dir = os.path.join(processed_CAD_root, "normal_cloud", f"normal_cloud_upright_z_parts_fps_{size_str}")
    
#     # 2. 定義 Contact global_gaussian 的路徑
#     contact_global_gaussian_dir = os.path.join(processed_CAD_root, "normal_cloud", f"normal_cloud_upright_z_parts_fps_contact_global_gaussian_{size_str}")
    
#     # 3. 定義 Identify 的路徑
#     csv_identify_dir = os.path.join(processed_CAD_root, "csv_identify_parts")
#     final_output_dir = os.path.join(processed_CAD_root, "normal_cloud", f"normal_cloud_upright_z_parts_fps_contact_global_gaussian_identify_{size_str}")

#     print(f"--- 正在處理 2^{exp} (Size: {size_str}) ---")

#     # 執行 Contact Generation
#     transform_3D_batch.batch_process_contact_gen(
#         input_cloud_dir,
#         contact_global_gaussian_dir,
#         label_mode="global_gaussian"
#     )

#     # 執行 Rename 與 Copy
#     transform_3D_batch.batch_rename_and_copy_by_mode(
#         csv_identify_dir,
#         os.path.join(contact_global_gaussian_dir,"tree"),
#         os.path.join(final_output_dir,"tree")
#     )

# print("所有批次任務已完成！")

# for exp in range(13, 15):
#     size_str = str(2**exp)
    
#     # 1. 定義輸入與輸出的路徑
#     input_cloud_dir = os.path.join(processed_CAD_root, "normal_cloud", f"normal_cloud_upright_z_parts_surface_uniform_{size_str}")
    
#     # 2. 定義 Contact global_gaussian 的路徑
#     contact_global_gaussian_dir = os.path.join(processed_CAD_root, "normal_cloud", f"normal_cloud_upright_z_parts_surface_uniform_contact_global_gaussian_{size_str}")
    
#     # 3. 定義 Identify 的路徑
#     csv_identify_dir = os.path.join(processed_CAD_root, "csv_identify_parts")
#     final_output_dir = os.path.join(processed_CAD_root, "normal_cloud", f"normal_cloud_upright_z_parts_surface_uniform_contact_global_gaussian_identify_{size_str}")

#     print(f"--- 正在處理 2^{exp} (Size: {size_str}) ---")

#     # 執行 Contact Generation
#     transform_3D_batch.batch_process_contact_gen(
#         input_cloud_dir,
#         contact_global_gaussian_dir,
#         label_mode="global_gaussian"
#     )

#     # 執行 Rename 與 Copy
#     transform_3D_batch.batch_rename_and_copy_by_mode(
#         csv_identify_dir,
#         os.path.join(contact_global_gaussian_dir,"tree"),
#         os.path.join(final_output_dir,"tree")
#     )

# print("所有批次任務已完成！")