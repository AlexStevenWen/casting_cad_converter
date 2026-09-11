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
"""
transform_3D_batch.copy_cad_files_based_on_csv(CAD_source_root,
                                               processed_CAD_root +  "\step_raw_component",
                                               processed_table_root + "\cast_table_dataset.csv")

transform_3D_batch.batch_transform_Step_to_3D(input_dir=processed_CAD_root + "\step_raw_component",
                                      output_dir=processed_CAD_root +  "\stl_raw_componet",
                                      mode=".stl")

transform_3D_batch.batch_transform_Step_to_3D_mergestl(input_dir=processed_CAD_root + "\stl_raw_componet",
                                      output_dir=processed_CAD_root +  "\stl_raw_merge",
                                      mode=".stl")



transform_3D_batch.batch_transform_Step_to_3D_OCC(input_dir=processed_CAD_root + "\step_raw_component",
                                                 output_dir=processed_CAD_root +  "\step_raw_merge",
                                      mode=".step")




transform_3D_batch.batch_transform_Step_to_3D_moving_double(
    input_dir_assembly= processed_CAD_root + "\step_raw_component",
    input_dir_merged=processed_CAD_root + "\step_raw_merge",
    output_dir_assembly=processed_CAD_root + "\step_raw_center_component",
    output_dir_merged=processed_CAD_root + "\step_raw_center_merge", # 這裡指定輸出資料夾
    mode=".step",
    Fvector=(0, 0, 0),
    Frotation=0S
    )

transform_3D_batch.batch_transform_Step_to_3D_moving_double(
    input_dir_assembly= processed_CAD_root + "\step_raw_center_component",
    input_dir_merged=processed_CAD_root + "\step_raw_center_merge",
    output_dir_assembly=processed_CAD_root + "\step_upright_z_component",
    output_dir_merged=processed_CAD_root + "\step_upright_z_merge", # 這裡指定輸出資料夾
    mode=".step",
    Fvector=(1, 0, 0),
    Frotation=-90
    )


transform_3D_batch.batch_transform_Step_to_3D(processed_CAD_root +  "\step_upright_z_merge",
                                              processed_CAD_root +  "\stl_upright_z_merge",
                                              mode=".stl",Fvector=(0,0,0),Frotation= 0)


transform_3D_batch.batch_transform_Stl_to_Deep(processed_CAD_root +  "\stl_upright_z_merge",
                                               processed_CAD_root +  "\six_views_upright_z")

transform_3D_batch.batch_transform_Stl_to_Deep(processed_CAD_root +  "\stl_upright_z_merge",
                                               processed_CAD_root +  "\six_views_upright_z_45",
                                               camera_angles_list= six_views_45)
"""
standard_views = [
    # ==========================================
    # ★ 極點區域 (Poles) - 2組 x 4變體 = 8張
    # ==========================================
    # 1. 北極點 (Top)
    [-90, 0, 0], [-90, 0, 90], [-90, 0, 180], [-90, 0, -90],
    
    # 2. 南極點 (Bottom)
    [90, 0, 0],  [90, 0, 90],  [90, 0, 180],  [90, 0, -90],

    # ==========================================
    # ★ 第一層：北半球環 (North Ring, y=-45) - 8組 x 4變體 = 32張
    # ==========================================
    # 3. 北-正
    [-45, 0, 0],   [-45, 0, 90],   [-45, 0, 180],   [-45, 0, -90],
    
    # 4. 北-右前
    [-45, 45, 0],  [-45, 45, 90],  [-45, 45, 180],  [-45, 45, -90],
    
    # 5. 北-右
    [-45, 90, 0],  [-45, 90, 90],  [-45, 90, 180],  [-45, 90, -90],
    
    # 6. 北-右後
    [-45, 135, 0], [-45, 135, 90], [-45, 135, 180], [-45, 135, -90],
    
    # 7. 北-後 (★ 重點檢查區：最可能看到澆口杯靠右)
    [-45, 180, 0], [-45, 180, 90], [-45, 180, 180], [-45, 180, -90],
    
    # 8. 北-左後
    [-45, -135, 0],[-45, -135, 90],[-45, -135, 180],[-45, -135, -90],
    
    # 9. 北-左
    [-45, -90, 0], [-45, -90, 90], [-45, -90, 180], [-45, -90, -90],
    
    # 10. 北-左前
    [-45, -45, 0], [-45, -45, 90], [-45, -45, 180], [-45, -45, -90],

    # ==========================================
    # ★ 第二層：赤道環 (Equator Ring, y=0) - 8組 x 4變體 = 32張
    # ==========================================
    # 11. 正平視
    [0, 0, 0],     [0, 0, 90],     [0, 0, 180],     [0, 0, -90],
    
    # 12. 右前平視
    [0, 45, 0],    [0, 45, 90],    [0, 45, 180],    [0, 45, -90],
    
    # 13. 右平視 (你之前測過的側面)
    [0, 90, 0],    [0, 90, 90],    [0, 90, 180],    [0, 90, -90],
    
    # 14. 右後平視
    [0, 135, 0],   [0, 135, 90],   [0, 135, 180],   [0, 135, -90],
    
    # 15. 後平視 (正背面)
    [0, 180, 0],   [0, 180, 90],   [0, 180, 180],   [0, 180, -90],
    
    # 16. 左後平視
    [0, -135, 0],  [0, -135, 90],  [0, -135, 180],  [0, -135, -90],
    
    # 17. 左平視
    [0, -90, 0],   [0, -90, 90],   [0, -90, 180],   [0, -90, -90],
    
    # 18. 左前平視
    [0, -45, 0],   [0, -45, 90],   [0, -45, 180],   [0, -45, -90],

    # ==========================================
    # ★ 第三層：南半球環 (South Ring, y=45) - 8組 x 4變體 = 32張
    # ==========================================
    # 19. 南-正
    [45, 0, 0],    [45, 0, 90],    [45, 0, 180],    [45, 0, -90],
    
    # 20. 南-右前
    [45, 45, 0],   [45, 45, 90],   [45, 45, 180],   [45, 45, -90],
    
    # 21. 南-右
    [45, 90, 0],   [45, 90, 90],   [45, 90, 180],   [45, 90, -90],
    
    # 22. 南-右後
    [45, 135, 0],  [45, 135, 90],  [45, 135, 180],  [45, 135, -90],
    
    # 23. 南-後
    [45, 180, 0],  [45, 180, 90],  [45, 180, 180],  [45, 180, -90],
    
    # 24. 南-左後
    [45, -135, 0], [45, -135, 90], [45, -135, 180], [45, -135, -90],
    
    # 25. 南-左
    [45, -90, 0],  [45, -90, 90],  [45, -90, 180],  [45, -90, -90],
    
    # 26. 南-左前
    [45, -45, 0],  [45, -45, 90],  [45, -45, 180],  [45, -45, -90],
]
"""
transform_3D_batch.batch_transform_STEP_to_2D(processed_CAD_root +  "\step_upright_z_component",
                                               processed_CAD_root +  "\step_six_views_45_step_upright_z_component",
                                               camera_angles_list= six_views_45)


transform_3D_batch.batch_transform_STEP_to_2D(processed_CAD_root +  "\step_upright_z_merge",
                                               processed_CAD_root +  "\step_six_views_45_upright_z_merge",
                                               camera_angles_list= six_views_45)
"""

# transform_3D_batch.batch_transform_STEP_to_2D(processed_CAD_root +  "\step_raw_component",
#                                                processed_CAD_root +  "\step_standard_views_step_raw_component",
#                                                camera_angles_list= standard_views)

# transform_3D_batch.batch_transform_STEP_to_2D(processed_CAD_root +  "\step_upright_z_component",
#                                                processed_CAD_root +  "\step_standard_views_step_upright_z_component",
#                                                camera_angles_list= standard_views)


# transform_3D_batch.batch_transform_STEP_to_2D(processed_CAD_root +  "\step_upright_z_merge",
#                                                processed_CAD_root +  "\step_standard_views_step_upright_z_merge",
#                                                camera_angles_list= standard_views)
# transform_3D_batch.batch_rename_and_copy_by_mode(processed_CAD_root + r"\csv_identify_parts",processed_CAD_root + fr"\step_upright_z_parts\tree",processed_CAD_root + fr"\step_upright_z_parts_identify\tree",mode = ".step")
# transform_3D_batch.batch_transform_STEP_to_2D(processed_CAD_root +  "\step_upright_z_parts_identify",
#                                                 processed_CAD_root +  "\step_standard_z_parts_identify",
#                                                 camera_angles_list= standard_views)


transform_3D_batch.batch_rename_and_copy_by_mode(processed_CAD_root + r"\csv_identify_parts",processed_CAD_root + fr"\stl_upright_z_parts\tree",processed_CAD_root + fr"\stl_upright_z_parts_identify\tree",mode = ".stl")
"""
transform_3D_batch.batch_transform_Stl_to_cloud(processed_CAD_root +  "\stl_upright_z_merge",processed_CAD_root +  f"\cloud_upright_z_merge_{str(2**10)}",point_num=2**10)
transform_3D_batch.batch_transform_Stl_to_cloud(processed_CAD_root +  "\stl_upright_z_merge",processed_CAD_root +  f"\cloud_upright_z_merge_{str(2**11)}",point_num=2**11)
transform_3D_batch.batch_transform_Stl_to_cloud(processed_CAD_root +  "\stl_upright_z_merge",processed_CAD_root +  f"\cloud_upright_z_merge_{str(2**12)}",point_num=2**12)
transform_3D_batch.batch_transform_Stl_to_cloud(processed_CAD_root +  "\stl_upright_z_merge",processed_CAD_root +  f"\cloud_upright_z_merge_{str(2**13)}",point_num=2**13)
transform_3D_batch.batch_transform_Stl_to_cloud(processed_CAD_root +  "\stl_upright_z_merge",processed_CAD_root +  f"\cloud_upright_z_merge_{str(2**14)}",point_num=2**14)
transform_3D_batch.batch_transform_Stl_to_cloud(processed_CAD_root +  "\stl_upright_z_merge",processed_CAD_root +  f"\cloud_upright_z_merge_{str(2**15)}",point_num=2**15)
transform_3D_batch.batch_transform_Stl_to_cloud(processed_CAD_root +  "\stl_upright_z_merge",processed_CAD_root +  f"\cloud_upright_z_merge_{str(2**16)}",point_num=2**16)

transform_3D_batch.batch_transform_Step_to_3D_OCCseg(processed_CAD_root + "\step_upright_z_component",processed_CAD_root + "\step_upright_z_parts")

transform_3D_batch.batch_transform_Step_to_3D(processed_CAD_root +  "\step_upright_z_parts",
                                              processed_CAD_root +  "\stl_upright_z_parts",
                                              mode=".stl",Fvector=(0,0,0),Frotation= 0)

transform_3D_batch.batch_transform_step_cloud_moving_double(
    input_dir_assembly= processed_CAD_root + "\step_raw_center_component",
    input_dir_merged=processed_CAD_root + "\step_raw_center_merge",
    output_dir_assembly=processed_CAD_root + "\step_upright_z_component",
    output_dir_merged=processed_CAD_root + "\step_upright_z_merge", # 這裡指定輸出資料
    )


transform_3D_batch.batch_transform_Stl_to_cloud(processed_CAD_root +  "\stl_upright_z_parts",processed_CAD_root +  f"\cloud_upright_z_parts_{str(2**10)}",point_num=2**10)
transform_3D_batch.batch_transform_Stl_to_cloud(processed_CAD_root +  "\stl_upright_z_parts",processed_CAD_root +  f"\cloud_upright_z_parts_{str(2**11)}",point_num=2**11)
transform_3D_batch.batch_transform_Stl_to_cloud(processed_CAD_root +  "\stl_upright_z_parts",processed_CAD_root +  f"\cloud_upright_z_parts_{str(2**12)}",point_num=2**12)
transform_3D_batch.batch_transform_Stl_to_cloud(processed_CAD_root +  "\stl_upright_z_parts",processed_CAD_root +  f"\cloud_upright_z_parts_{str(2**13)}",point_num=2**13)
transform_3D_batch.batch_transform_Stl_to_cloud(processed_CAD_root +  "\stl_upright_z_parts",processed_CAD_root +  f"\cloud_upright_z_parts_{str(2**14)}",point_num=2**14)
transform_3D_batch.batch_transform_Stl_to_cloud(processed_CAD_root +  "\stl_upright_z_parts",processed_CAD_root +  f"\cloud_upright_z_parts_{str(2**15)}",point_num=2**15)
transform_3D_batch.batch_transform_Stl_to_cloud(processed_CAD_root +  "\stl_upright_z_parts",processed_CAD_root +  f"\cloud_upright_z_parts_{str(2**16)}",point_num=2**16)

transform_3D_batch.batch_process_contact_gen()
"""
# transform_3D_batch.batch_transform_Stl_to_cloud(processed_CAD_root +  "\stl_upright_z_parts",processed_CAD_root +  rf"\normal_cloud_upright_z_parts_{str(2**10)}",point_num=2**10)
# transform_3D_batch.batch_transform_Stl_to_cloud(processed_CAD_root +  "\stl_upright_z_parts",processed_CAD_root +  rf"\normal_cloud_upright_z_parts_{str(2**11)}",point_num=2**11)
# transform_3D_batch.batch_transform_Stl_to_cloud(processed_CAD_root +  "\stl_upright_z_parts",processed_CAD_root +  rf"\normal_cloud_upright_z_parts_{str(2**12)}",point_num=2**12)
# transform_3D_batch.batch_transform_Stl_to_cloud(processed_CAD_root +  "\stl_upright_z_parts",processed_CAD_root +  rf"\normal_cloud_upright_z_parts_{str(2**13)}",point_num=2**13)
# transform_3D_batch.batch_transform_Stl_to_cloud(processed_CAD_root +  "\stl_upright_z_parts",processed_CAD_root +  rf"\normal_cloud_upright_z_parts_{str(2**14)}",point_num=2**14)
# transform_3D_batch.batch_transform_Stl_to_cloud(processed_CAD_root +  "\stl_upright_z_parts",processed_CAD_root +  rf"\normal_cloud_upright_z_parts_{str(2**15)}",point_num=2**15)
# transform_3D_batch.batch_transform_Stl_to_cloud(processed_CAD_root +  "\stl_upright_z_parts",processed_CAD_root +  rf"\normal_cloud_upright_z_parts_{str(2**16)}",point_num=2**16)





# transform_3D_batch.batch_transform_Stl_vhacd(processed_CAD_root +  "\stl_upright_z_parts",processed_CAD_root +  "\stl_file\stl_vhacd_upright_z_parts",use_simple_hull=True)
# transform_3D_batch.batch_transform_Stl_smoothing(processed_CAD_root +  "\stl_upright_z_parts",processed_CAD_root +  "\stl_file\stl_smoothing_it15_la0.8_upright_z_parts",iterations=15, lambda_filter=0.8)

#transform_3D_batch.batch_transform_Stl_simplification(processed_CAD_root +  "\stl_upright_z_parts",processed_CAD_root +  "\stl_file\stl_simplification_ra0.001_upright_z_parts",ratio=0.001)

#transform_3D_batch.batch_transform_Stl_alpha_shape(processed_CAD_root +  "\stl_upright_z_parts",processed_CAD_root +  "\stl_file\stl_alpha_shape_al0.5_upright_z_parts",alpha=0.5)






#process_3d_file_unified_batch(operation="merge_step",input_dir=processed_CAD_root +  "\Step_file_raw",output_dir=processed_CAD_root +  "\Step_file_merge",mode=".step")
#transform_3D_batch.batch_transform_Step_to_3D_OCC(processed_CAD_root +  "\Step_file_raw",processed_CAD_root +  "\Step_file_merge")
"""
process_3d_file_unified_batch(operation="move_step_by_merged_double",input_dir_assembly= processed_CAD_root + "\Step_file_raw",
    input_dir_merged=processed_CAD_root + "\Step_file_merge",
    output_dir_assembly=processed_CAD_root + "\Step_file_process_assembly",
    output_dir_merged=processed_CAD_root + "\Step_file_process_merge", # 這裡指定輸出資料夾
    mode=".step",
    Fvector=(0, 0, 0),
    Frotation=0)
"""
"""
transform_3D_batch.batch_transform_Step_to_3D_moving_double(
    input_dir_assembly= processed_CAD_root + "\Step_file_raw",
    input_dir_merged=processed_CAD_root + "\Step_file_merge",
    output_dir_assembly=processed_CAD_root + "\Step_file_process_assembly",
    output_dir_merged=processed_CAD_root + "\Step_file_process_merge", # 這裡指定輸出資料夾
    mode=".step",
    Fvector=(0, 0, 0),
    Frotation=0
    )
transform_3D_batch.batch_transform_Step_to_3D_moving_double(
    input_dir_assembly= processed_CAD_root + "\Step_file_process_assembly",
    input_dir_merged=processed_CAD_root + "\Step_file_process_merge",
    output_dir_assembly=processed_CAD_root + "\Step_file_process_assembly_gravity",
    output_dir_merged=processed_CAD_root + "\Step_file_process_merge_gravity", # 這裡指定輸出資料夾
    mode=".step",
    Fvector=(1, 0, 0),
    Frotation=-90
    )
"""
"""
transform_3D_batch.batch_transform_Step_to_Parameter(processed_CAD_root + "\Step_file_process_merge",processed_CAD_root +  "\Step_file_Parameter")
"""

#transform_3D_batch.batch_transform_Step_to_3D(processed_CAD_root +  "\Step_file_process_merge",processed_CAD_root +  "\Stl_file",mode=".stl",Fvector=(0,0,1),Frotation= 180)

#transform_3D_batch.batch_transform_Step_to_3D(processed_CAD_root +  "\Step_file_merge",processed_CAD_root +  "\off_file",mode=".off",Fvector=(0,0,1),Frotation= 180)
#transform_3D_batch.batch_transform_Step_to_3D(processed_CAD_root +  "\Step_file_merge",processed_CAD_root +  "\ply_file",mode=".ply",Fvector=(0,0,1),Frotation= 180)
#transform_3D_batch.batch_transform_Step_to_3D(processed_CAD_root +  "\Step_file_merge",processed_CAD_root +  "\obj_file",mode=".obj",Fvector=(0,0,1),Frotation= 180)
"""
transform_3D_batch.batch_transform_Stl_to_cloud(processed_CAD_root +  "\stl_file",processed_CAD_root +  f"\cloud_file_{str(2**10)}",point_num=2**10)
transform_3D_batch.batch_transform_Stl_to_cloud(processed_CAD_root +  "\stl_file",processed_CAD_root +  f"\cloud_file_{str(2**11)}",point_num=2**11)
transform_3D_batch.batch_transform_Stl_to_cloud(processed_CAD_root +  "\stl_file",processed_CAD_root +  f"\cloud_file_{str(2**12)}",point_num=2**12)
transform_3D_batch.batch_transform_Stl_to_cloud(processed_CAD_root +  "\stl_file",processed_CAD_root +  f"\cloud_file_{str(2**13)}",point_num=2**13)
transform_3D_batch.batch_transform_Stl_to_cloud(processed_CAD_root +  "\stl_file",processed_CAD_root +  f"\cloud_file_{str(2**14)}",point_num=2**14)
transform_3D_batch.batch_transform_Stl_to_cloud(processed_CAD_root +  "\stl_file",processed_CAD_root +  f"\cloud_file_{str(2**15)}",point_num=2**15)
transform_3D_batch.batch_transform_Stl_to_cloud(processed_CAD_root +  "\stl_file",processed_CAD_root +  f"\cloud_file_{str(2**16)}",point_num=2**16)

transform_3D_batch.batch_transform_Stl_to_normalcloud(processed_CAD_root +  "\stl_file",processed_CAD_root +  rf"\normalcloud_file_{str(2**10)}",point_num=2**10)
transform_3D_batch.batch_transform_Stl_to_normalcloud(processed_CAD_root +  "\stl_file",processed_CAD_root +  rf"\normalcloud_file_{str(2**11)}",point_num=2**11)
transform_3D_batch.batch_transform_Stl_to_normalcloud(processed_CAD_root +  "\stl_file",processed_CAD_root +  rf"\normalcloud_file_{str(2**12)}",point_num=2**12)
transform_3D_batch.batch_transform_Stl_to_normalcloud(processed_CAD_root +  "\stl_file",processed_CAD_root +  rf"\normalcloud_file_{str(2**13)}",point_num=2**13)
transform_3D_batch.batch_transform_Stl_to_normalcloud(processed_CAD_root +  "\stl_file",processed_CAD_root +  rf"\normalcloud_file_{str(2**14)}",point_num=2**14)
transform_3D_batch.batch_transform_Stl_to_normalcloud(processed_CAD_root +  "\stl_file",processed_CAD_root +  rf"\normalcloud_file_{str(2**15)}",point_num=2**15)
transform_3D_batch.batch_transform_Stl_to_normalcloud(processed_CAD_root +  "\stl_file",processed_CAD_root +  rf"\normalcloud_file_{str(2**16)}",point_num=2**16)
transform_3D_batch.batch_transform_Stl_to_voxel(processed_CAD_root +  "\stl_file",processed_CAD_root +  rf"\voxel_file_{str(2**1)}",voxel_size=2**1)
transform_3D_batch.batch_transform_Stl_to_voxel(processed_CAD_root +  "\stl_file",processed_CAD_root +  rf"\voxel_file_{str(2**2)}",voxel_size=2**2)
transform_3D_batch.batch_transform_Stl_to_voxel(processed_CAD_root +  "\stl_file",processed_CAD_root +  rf"\voxel_file_{str(2**3)}",voxel_size=2**3)
transform_3D_batch.batch_transform_Stl_to_voxel(processed_CAD_root +  "\stl_file",processed_CAD_root +  rf"\voxel_file_{str(2**4)}",voxel_size=2**4)
transform_3D_batch.batch_transform_Stl_to_voxel(processed_CAD_root +  "\stl_file",processed_CAD_root +  rf"\voxel_file_{str(2**5)}",voxel_size=2**5)
transform_3D_batch.batch_transform_Stl_to_voxel(processed_CAD_root +  "\stl_file",processed_CAD_root +  rf"\voxel_file_{str(2**6)}",voxel_size=2**6)
transform_3D_batch.batch_transform_Stl_to_voxel(processed_CAD_root +  "\stl_file",processed_CAD_root +  rf"\voxel_file_{str(2**7)}",voxel_size=2**7)
transform_3D_batch.batch_transform_Stl_to_voxel(processed_CAD_root +  "\stl_file",processed_CAD_root +  rf"\voxel_file_{str(2**7)}",voxel_size=2**8)
"""
#transform_3D_batch.batch_transform_Stl_to_Deep(processed_CAD_root +  "\stl_file",processed_CAD_root +  rf"\six_views")
#transform_3D_batch.batch_transform_Step_to_3D(processed_CAD_root +  "\Step_file_process_merge_gravity",processed_CAD_root +  "\Stl_file_Z_positive",mode=".stl")


"z 軸對"
"""
transform_3D_batch.batch_transform_Stl_to_normalcloud(processed_CAD_root +  "\stl_file_Z_positive",processed_CAD_root +  rf"\normalcloud_file_Z_positive_{str(2**10)}",point_num=2**10)
transform_3D_batch.batch_transform_Stl_to_normalcloud(processed_CAD_root +  "\stl_file_Z_positive",processed_CAD_root +  rf"\normalcloud_file_Z_positive_{str(2**11)}",point_num=2**11)
transform_3D_batch.batch_transform_Stl_to_normalcloud(processed_CAD_root +  "\stl_file_Z_positive",processed_CAD_root +  rf"\normalcloud_file_Z_positive_{str(2**12)}",point_num=2**12)
transform_3D_batch.batch_transform_Stl_to_normalcloud(processed_CAD_root +  "\stl_file_Z_positive",processed_CAD_root +  rf"\normalcloud_file_Z_positive_{str(2**13)}",point_num=2**13)
transform_3D_batch.batch_transform_Stl_to_normalcloud(processed_CAD_root +  "\stl_file_Z_positive",processed_CAD_root +  rf"\normalcloud_file_Z_positive_{str(2**14)}",point_num=2**14)
transform_3D_batch.batch_transform_Stl_to_normalcloud(processed_CAD_root +  "\stl_file_Z_positive",processed_CAD_root +  rf"\normalcloud_file_Z_positive_{str(2**15)}",point_num=2**15)
transform_3D_batch.batch_transform_Stl_to_normalcloud(processed_CAD_root +  "\stl_file_Z_positive",processed_CAD_root +  rf"\normalcloud_file_Z_positive_{str(2**16)}",point_num=2**16)




#transform_3D_batch.batch_transform_Step_to_3D_OCCseg(processed_CAD_root +  "\Step_file_process_assembly_gravity",processed_CAD_root +  rf"\\Step_file_process_parts_gravity")
transform_3D_batch.batch_transform_Step_to_3D(processed_CAD_root +  "\Step_file_process_parts_gravity",processed_CAD_root +  "\stl_file_parts_Z_positive",mode=".stl",Fvector=(0,0,1),Frotation= 180)
transform_3D_batch.batch_transform_Stl_to_normalcloud(processed_CAD_root +  "\stl_file_parts_Z_positive",processed_CAD_root +  rf"\normalcloud_parts_file_Z_positive_{str(2**10)}",point_num=2**10)
transform_3D_batch.batch_transform_Stl_to_normalcloud(processed_CAD_root +  "\stl_file_parts_Z_positive",processed_CAD_root +  rf"\normalcloud_parts_file_Z_positive_{str(2**11)}",point_num=2**11)
transform_3D_batch.batch_transform_Stl_to_normalcloud(processed_CAD_root +  "\stl_file_parts_Z_positive",processed_CAD_root +  rf"\normalcloud_parts_file_Z_positive_{str(2**12)}",point_num=2**12)
transform_3D_batch.batch_transform_Stl_to_normalcloud(processed_CAD_root +  "\stl_file_parts_Z_positive",processed_CAD_root +  rf"\normalcloud_parts_file_Z_positive_{str(2**13)}",point_num=2**13)
transform_3D_batch.batch_transform_Stl_to_normalcloud(processed_CAD_root +  "\stl_file_parts_Z_positive",processed_CAD_root +  rf"\normalcloud_parts_file_Z_positive_{str(2**14)}",point_num=2**14)
transform_3D_batch.batch_transform_Stl_to_normalcloud(processed_CAD_root +  "\stl_file_parts_Z_positive",processed_CAD_root +  rf"\normalcloud_parts_file_Z_positive_{str(2**15)}",point_num=2**15)
transform_3D_batch.batch_transform_Stl_to_normalcloud(processed_CAD_root +  "\stl_file_parts_Z_positive",processed_CAD_root +  rf"\normalcloud_parts_file_Z_positive_{str(2**16)}",point_num=2**16)

transform_3D_batch.batch_transform_Stl_to_cloud(processed_CAD_root +  "\stl_file_parts_Z_positive",processed_CAD_root +  rf"\cloud_parts_file_Z_positive_{str(2**10)}",point_num=2**10)
transform_3D_batch.batch_transform_Stl_to_cloud(processed_CAD_root +  "\stl_file_parts_Z_positive",processed_CAD_root +  rf"\cloud_parts_file_Z_positive_{str(2**11)}",point_num=2**11)
transform_3D_batch.batch_transform_Stl_to_cloud(processed_CAD_root +  "\stl_file_parts_Z_positive",processed_CAD_root +  rf"\cloud_parts_file_Z_positive_{str(2**12)}",point_num=2**12)
transform_3D_batch.batch_transform_Stl_to_cloud(processed_CAD_root +  "\stl_file_parts_Z_positive",processed_CAD_root +  rf"\cloud_parts_file_Z_positive_{str(2**13)}",point_num=2**13)
transform_3D_batch.batch_transform_Stl_to_cloud(processed_CAD_root +  "\stl_file_parts_Z_positive",processed_CAD_root +  rf"\cloud_parts_file_Z_positive_{str(2**14)}",point_num=2**14)
transform_3D_batch.batch_transform_Stl_to_cloud(processed_CAD_root +  "\stl_file_parts_Z_positive",processed_CAD_root +  rf"\cloud_parts_file_Z_positive_{str(2**15)}",point_num=2**15)
transform_3D_batch.batch_transform_Stl_to_cloud(processed_CAD_root +  "\stl_file_parts_Z_positive",processed_CAD_root +  rf"\cloud_parts_file_Z_positive_{str(2**16)}",point_num=2**16)
"""
"""
transform_3D_batch.batch_process_assemblies(processed_CAD_root +  rf"\cloud_parts_file_Z_positive_{str(2**10)}",rf"\cloud_parts_surface_detection_{str(2**10)}",contact_threshold = 1)
transform_3D_batch.batch_process_assemblies(processed_CAD_root +  rf"\cloud_parts_file_Z_positive_{str(2**11)}",rf"\cloud_parts_surface_detection_{str(2**11)}",contact_threshold = 1)
transform_3D_batch.batch_process_assemblies(processed_CAD_root +  rf"\cloud_parts_file_Z_positive_{str(2**12)}",rf"\cloud_parts_surface_detection_{str(2**12)}",contact_threshold = 1)
transform_3D_batch.batch_process_assemblies(processed_CAD_root +  rf"\cloud_parts_file_Z_positive_{str(2**13)}",rf"\cloud_parts_surface_detection_{str(2**13)}",contact_threshold = 1)
transform_3D_batch.batch_process_assemblies(processed_CAD_root +  rf"\cloud_parts_file_Z_positive_{str(2**14)}",rf"\cloud_parts_surface_detection_{str(2**14)}",contact_threshold = 1)
transform_3D_batch.batch_process_assemblies(processed_CAD_root +  rf"\cloud_parts_file_Z_positive_{str(2**15)}",rf"\cloud_parts_surface_detection_{str(2**15)}",contact_threshold = 1)
transform_3D_batch.batch_process_assemblies(processed_CAD_root +  rf"\cloud_parts_file_Z_positive_{str(2**16)}",rf"\cloud_parts_surface_detection_{str(2**16)}",contact_threshold = 1)
"""