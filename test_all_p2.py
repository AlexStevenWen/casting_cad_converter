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

transform_3D_batch.copy_cad_files_based_on_csv(CAD_source_root,
                                               processed_CAD_root +  "\step_raw_component",
                                               processed_table_root + "\cast_table_dataset.csv")
"""
transform_3D_batch.batch_transform_Step_to_3D(input_dir=processed_CAD_root + "\step_raw_component",
                                      output_dir=processed_CAD_root +  "\stl_raw_componet",
                                      mode=".stl")

transform_3D_batch.batch_transform_Step_to_3D_mergestl(input_dir=processed_CAD_root + "\stl_raw_componet",
                                      output_dir=processed_CAD_root +  "\stl_raw_merge",
                                      mode=".stl")

"""

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
    Frotation=0
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

"""
transform_3D_batch.batch_transform_Stl_to_Deep(processed_CAD_root +  "\stl_upright_z_merge",
                                               processed_CAD_root +  "\six_views_upright_z")

six_views_45 = [[45, 0, 0],    # Front
    [225, 0, 0],    # Back
    [135,  0, 0],    # Left
    [-45, 0, 0],    # Right
    [45,  90, 0],    # Top
    [45, -90, 0]     # Bottom
]
transform_3D_batch.batch_transform_Stl_to_Deep(processed_CAD_root +  "\stl_upright_z_merge",
                                               processed_CAD_root +  "\six_views_upright_z_45",
                                               camera_angles_list= six_views_45)





transform_3D_batch.batch_transform_Stl_to_cloud(processed_CAD_root +  "\stl_upright_z_merge",processed_CAD_root +  f"\cloud_upright_z_merge_{str(2**10)}",point_num=2**10)
transform_3D_batch.batch_transform_Stl_to_cloud(processed_CAD_root +  "\stl_upright_z_merge",processed_CAD_root +  f"\cloud_upright_z_merge_{str(2**11)}",point_num=2**11)
transform_3D_batch.batch_transform_Stl_to_cloud(processed_CAD_root +  "\stl_upright_z_merge",processed_CAD_root +  f"\cloud_upright_z_merge_{str(2**12)}",point_num=2**12)
transform_3D_batch.batch_transform_Stl_to_cloud(processed_CAD_root +  "\stl_upright_z_merge",processed_CAD_root +  f"\cloud_upright_z_merge_{str(2**13)}",point_num=2**13)
transform_3D_batch.batch_transform_Stl_to_cloud(processed_CAD_root +  "\stl_upright_z_merge",processed_CAD_root +  f"\cloud_upright_z_merge_{str(2**14)}",point_num=2**14)
transform_3D_batch.batch_transform_Stl_to_cloud(processed_CAD_root +  "\stl_upright_z_merge",processed_CAD_root +  f"\cloud_upright_z_merge_{str(2**15)}",point_num=2**15)
transform_3D_batch.batch_transform_Stl_to_cloud(processed_CAD_root +  "\stl_upright_z_merge",processed_CAD_root +  f"\cloud_upright_z_merge_{str(2**16)}",point_num=2**16)
"""

"""
transform_3D_batch.batch_transform_step_cloud_moving_double(
    input_dir_assembly= processed_CAD_root + "\step_raw_center_component",
    input_dir_merged=processed_CAD_root + "\step_raw_center_merge",
    output_dir_assembly=processed_CAD_root + "\step_upright_z_component",
    output_dir_merged=processed_CAD_root + "\step_upright_z_merge", # 這裡指定輸出資料
    )
"""
#transform_3D_batch.batch_transform_Step_to_3D_OCCsegre(processed_CAD_root + r"\step_upright_z_component\blank",processed_CAD_root + r"\step_upright_z_parts\tree",processed_CAD_root + r"\csv_identify_parts",)



#transform_3D_batch.batch_rename_and_copy_by_mode(processed_CAD_root + r"\csv_identify_parts",processed_CAD_root + r"\cloud_upright_z_parts_2048\tree",processed_CAD_root + r"\cloud_upright_z_parts_identify_2048\tree")

#transform_3D_batch.batch_rename_and_copy_by_mode(processed_CAD_root + r"\csv_identify_parts",processed_CAD_root + fr"\normal_cloud_upright_z_parts_{str(2**10)}\tree",processed_CAD_root + fr"\normal_cloud_upright_z_parts_identify_{str(2**10)}\tree")
#transform_3D_batch.batch_rename_and_copy_by_mode(processed_CAD_root + r"\csv_identify_parts",processed_CAD_root + fr"\normal_cloud_upright_z_parts_{str(2**10)}\tree",processed_CAD_root + fr"\normal_cloud_upright_z_parts_identify_{str(2**10)}\tree")
#transform_3D_batch.batch_rename_and_copy_by_mode(processed_CAD_root + r"\csv_identify_parts",processed_CAD_root + fr"\normal_cloud_upright_z_parts_{str(2**12)}\tree",processed_CAD_root + fr"\normal_cloud_upright_z_parts_identify_{str(2**12)}\tree")
#transform_3D_batch.generate_no_match_report(processed_CAD_root + r"\csv_identify_parts","no_match.csv")
#transform_3D_batch.batch_process_contact_gen(processed_CAD_root +f"\cloud_upright_z_parts_{str(2**10)}" ,processed_CAD_root +   f"\cloud_upright_z_parts_contact_{str(2**10)}")
#transform_3D_batch.batch_process_contact_gen(processed_CAD_root +f"\cloud_upright_z_parts_{str(2**11)}" ,processed_CAD_root +  f"\cloud_upright_z_parts_contact_{str(2**11)}")
#transform_3D_batch.batch_process_contact_gen(processed_CAD_root +f"\cloud_upright_z_parts_{str(2**12)}" ,processed_CAD_root +  f"\cloud_upright_z_parts_contact_{str(2**12)}")
#transform_3D_batch.batch_process_contact_gen(processed_CAD_root +f"\cloud_upright_z_parts_{str(2**13)}" ,processed_CAD_root +  f"\cloud_upright_z_parts_contact_{str(2**13)}")
#transform_3D_batch.batch_process_contact_gen(processed_CAD_root +f"\cloud_upright_z_parts_{str(2**14)}" ,processed_CAD_root +  f"\cloud_upright_z_parts_contact_{str(2**14)}")
#transform_3D_batch.batch_process_contact_gen(processed_CAD_root +f"\cloud_upright_z_parts_{str(2**15)}" ,processed_CAD_root +  f"\cloud_upright_z_parts_contact_{str(2**15)}")
#transform_3D_batch.batch_process_contact_gen(processed_CAD_root +f"\cloud_upright_z_parts_{str(2**16)}" ,processed_CAD_root +  f"\cloud_upright_z_parts_contact_{str(2**16)}")



#transform_3D_batch.batch_process_contact_gen(processed_CAD_root +fr"\normal_cloud_upright_z_parts_{str(2**10)}" ,processed_CAD_root +   fr"\normal_cloud_upright_z_parts_contact_{str(2**10)}")
#ransform_3D_batch.batch_process_contact_gen(processed_CAD_root +fr"\normal_cloud_upright_z_parts_{str(2**11)}" ,processed_CAD_root +  fr"\normal_cloud_upright_z_parts_contact_{str(2**11)}")

#transform_3D_batch.batch_process_contact_gen(processed_CAD_root +fr"\normal_cloud_upright_z_parts_{str(2**10)}" ,processed_CAD_root +   fr"\normal_cloud_upright_z_parts_contact_clamped_decay_{str(2**10)}")
#transform_3D_batch.batch_process_contact_gen(processed_CAD_root +fr"\normal_cloud_upright_z_parts_{str(2**11)}" ,processed_CAD_root +  fr"\normal_cloud_upright_z_parts_contact_clamped_decay_{str(2**11)}")
#transform_3D_batch.batch_process_contact_gen(processed_CAD_root +fr"\normal_cloud_upright_z_parts_{str(2**12)}" ,processed_CAD_root +   fr"\normal_cloud_upright_z_parts_contact_{str(2**12)}")
#transform_3D_batch.batch_process_contact_gen(processed_CAD_root +fr"\normal_cloud_upright_z_parts_{str(2**13)}" ,processed_CAD_root +  fr"\normal_cloud_upright_z_parts_contact_{str(2**13)}")
#transform_3D_batch.batch_process_contact_gen(processed_CAD_root +fr"\normal_cloud_upright_z_parts_{str(2**14)}" ,processed_CAD_root +  fr"\normal_cloud_upright_z_parts_contact_{str(2**14)}")

#transform_3D_batch.batch_process_contact_gen(processed_CAD_root +fr"\normal_cloud_upright_z_parts_{str(2**10)}" ,processed_CAD_root +   fr"\normal_cloud_upright_z_parts_contact_th1.5_{str(2**10)}",contact_threshold=1.5)
#transform_3D_batch.batch_process_contact_gen(processed_CAD_root +fr"\normal_cloud_upright_z_parts_{str(2**11)}" ,processed_CAD_root +  fr"\normal_cloud_upright_z_parts_contact_th1.5_{str(2**11)}",contact_threshold=1.5)
#transform_3D_batch.batch_process_contact_gen(processed_CAD_root +fr"\normal_cloud_upright_z_parts_{str(2**12)}" ,processed_CAD_root +  fr"\normal_cloud_upright_z_parts_contact_th1.5_{str(2**12)}",contact_threshold=1.5)

#transform_3D_batch.batch_process_contact_gen(processed_CAD_root +fr"\normal_cloud_upright_z_parts_{str(2**12)}" ,processed_CAD_root +  fr"\normal_cloud_upright_z_parts_contact_{str(2**12)}")

#transform_3D_batch.batch_rename_and_copy_by_mode(processed_CAD_root + r"\csv_identify_parts",processed_CAD_root + fr"\normal_cloud_upright_z_parts_contact_2048\tree",processed_CAD_root + r"\normal_cloud_upright_z_parts_contact_identify_2048\tree")
#transform_3D_batch.batch_rename_and_copy_by_mode(processed_CAD_root + r"\csv_identify_parts",processed_CAD_root + fr"\normal_cloud_upright_z_parts_contact_4096\tree",processed_CAD_root + r"\normal_cloud_upright_z_parts_contact_identify_4096\tree")
#transform_3D_batch.batch_rename_and_copy_by_mode(processed_CAD_root + r"\csv_identify_parts",processed_CAD_root + fr"\normal_cloud_upright_z_parts_contact_8192\tree",processed_CAD_root + r"\normal_cloud_upright_z_parts_contact_identify_8192\tree")
#transform_3D_batch.batch_rename_and_copy_by_mode(processed_CAD_root + r"\csv_identify_parts",processed_CAD_root + fr"\normal_cloud_upright_z_parts_contact_16384\tree",processed_CAD_root + r"\normal_cloud_upright_z_parts_contact_identify_16384\tree")
#transform_3D_batch.batch_rename_and_copy_by_mode(processed_CAD_root + r"\csv_identify_parts",processed_CAD_root + fr"\normal_cloud_upright_z_parts_contact_32768\tree",processed_CAD_root + r"\normal_cloud_upright_z_parts_contact_identify_32768\tree")


#transform_3D_batch.batch_rename_and_copy_by_mode(processed_CAD_root + r"\csv_identify_parts",processed_CAD_root + fr"\normal_cloud_upright_z_parts_contact_th1.5_2048\tree",processed_CAD_root + r"\normal_cloud_upright_z_parts_contact_th1.5_identify_2048\tree")
#transform_3D_batch.batch_rename_and_copy_by_mode(processed_CAD_root + r"\csv_identify_parts",processed_CAD_root + fr"\normal_cloud_upright_z_parts_contact_th1.5_4096\tree",processed_CAD_root + r"\normal_cloud_upright_z_parts_contact_th1.5_identify_4096\tree")

#transform_3D_batch.batch_process_contact_gen(processed_CAD_root +fr"\normal_cloud_upright_z_parts_{str(2**13)}" ,processed_CAD_root +  fr"\normal_cloud_upright_z_parts_contact_{str(2**13)}")
#transform_3D_batch.batch_process_contact_gen(processed_CAD_root +fr"\normal_cloud_upright_z_parts_{str(2**14)}" ,processed_CAD_root +  fr"\normal_cloud_upright_z_parts_contact_{str(2**14)}")
#transform_3D_batch.batch_process_contact_gen(processed_CAD_root +fr"\normal_cloud_upright_z_parts_{str(2**15)}" ,processed_CAD_root +  fr"\normal_cloud_upright_z_parts_contact_{str(2**15)}")





#transform_3D_batch.batch_process_contact_gen(processed_CAD_root +fr"\normal_cloud_upright_z_parts_{str(2**11)}" ,processed_CAD_root +  fr"\normal_cloud_upright_z_parts_contact_global_linear_{str(2**11)}",label_mode="global_linear")
#transform_3D_batch.batch_rename_and_copy_by_mode(processed_CAD_root + r"\csv_identify_parts",processed_CAD_root + fr"\normal_cloud_upright_z_parts_contact_global_linear_2048\tree",processed_CAD_root + fr"\normal_cloud_upright_z_parts_contact_global_linear_identify_2048\tree")


# transform_3D_batch.batch_process_contact_gen(processed_CAD_root +fr"\normal_cloud_upright_z_parts_{str(2**11)}" ,processed_CAD_root +  fr"\normal_cloud_upright_z_parts_contact_clamped_decay_{str(2**11)}",label_mode="clamped_decay")
# transform_3D_batch.batch_rename_and_copy_by_mode(processed_CAD_root + r"\csv_identify_parts",processed_CAD_root + fr"\normal_cloud_upright_z_parts_contact_clamped_decay_2048\tree",processed_CAD_root + fr"\normal_cloud_upright_z_parts_contact_clamped_decay_identify_2048\tree")

# transform_3D_batch.batch_process_contact_gen(processed_CAD_root +fr"\normal_cloud_upright_z_parts_{str(2**11)}" ,processed_CAD_root +  fr"\normal_cloud_upright_z_parts_contact_global_gaussian_{str(2**11)}",label_mode="global_gaussian")
# transform_3D_batch.batch_rename_and_copy_by_mode(processed_CAD_root + r"\csv_identify_parts",processed_CAD_root + fr"\normal_cloud_upright_z_parts_contact_global_gaussian_2048\tree",processed_CAD_root + fr"\normal_cloud_upright_z_parts_contact_global_gaussian_identify_2048\tree")

#transform_3D_batch.batch_transform_Cloud_to_2D(processed_CAD_root + fr"\normal_cloud_upright_z_parts_contact_global_gaussian_identify_2048\tree",processed_CAD_root + fr"\normal_cloud_2D_upright_z_parts_contact_global_gaussian_identify_2048\tree")
# six_views_45 = [[45, 0, 0],    # Front
#     [225, 0, 0],    # Back
#     [135,  0, 0],    # Left
#     [-45, 0, 0],    # Right
#     [45,  90, 0],    # Top
#     [45, -90, 0]     # Bottom
# ]
# transform_3D_batch.batch_transform_Cloud_to_2D(processed_CAD_root + fr"\normal_cloud_upright_z_parts_contact_global_gaussian_identify_2048\tree",processed_CAD_root + fr"\normal_cloud_2D_45_upright_z_parts_contact_global_gaussian_identify_2048\tree",camera_angles_list=six_views_45)



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
# ai_deconverter_root = r"D:\ChynWangProject\data\ai_deconverter"

#transform_3D_batch.batch_transform_Cloud_to_2D(processed_CAD_root + fr"\cloud_upright_z_merge_2048",processed_CAD_root + fr"\cloud_standard_2D_45_upright_z_merge_2048",camera_angles_list=standard_views)

#transform_3D_batch.batch_transform_Cloud_to_2D(processed_CAD_root + fr"\cloud_upright_z_parts_identify_2048",processed_CAD_root + fr"\cloud_standard_2D_45_upright_z_parts_identify_2048",camera_angles_list=standard_views)

#transform_3D_batch.batch_transform_Cloud_to_2D(processed_CAD_root + fr"\normal_cloud_upright_z_parts_contact_global_gaussian_identify_2048\tree",processed_CAD_root + fr"\normal_cloud_standard_2D_45_upright_z_parts_contact_global_gaussian_identify_2048\tree",camera_angles_list=standard_views)

#transform_3D_batch.batch_transform_Cloud_to_2D(ai_deconverter_root + fr"\global_gaussian_gonormal",ai_deconverter_root+ fr"\global_gaussian_gonormal_standard_2D",camera_angles_list=standard_views)

#transform_3D_batch.batch_transform_Cloud_to_2D(processed_CAD_root + fr"\normal_cloud_upright_z_parts_contact_identify_2048\tree",processed_CAD_root + fr"\normal_cloud_standard_2D_45_upright_z_parts_contact_identify_2048\tree",camera_angles_list=standard_views)

#transform_3D_batch.batch_transform_Cloud_to_2D(ai_deconverter_root + fr"\segmentation_gonormal",ai_deconverter_root+ fr"\segmentation_gonormal_standard_2D",camera_angles_list=standard_views)

#transform_3D_batch.batch_transform_Cloud_STL_to_2D(processed_CAD_root + fr"\stl_upright_z_parts_identify\tree", ai_deconverter_root + fr"\exp_pointnext_part_seg_nocls_regress_nostn_global_gaussian_gonormal\ground_truth",ai_deconverter_root + fr"\exp_pointnext_part_seg_nocls_regress_nostn_global_gaussian_gonormal_standard_2D_add_stl\ground_truth",camera_angles_list=standard_views)
#transform_3D_batch.batch_transform_Cloud_STL_to_2D(processed_CAD_root + fr"\stl_upright_z_parts_identify\tree", ai_deconverter_root + fr"\exp_pointnext_part_seg_nocls_regress_nostn_global_gaussian_gonormal\prediction",ai_deconverter_root + fr"\exp_pointnext_part_seg_nocls_regress_nostn_global_gaussian_gonormal_standard_2D_add_stl\prediction",camera_angles_list=standard_views)

#transform_3D_batch.batch_transform_Cloud_STL_to_2D(processed_CAD_root + fr"\stl_upright_z_parts_identify\tree", ai_deconverter_root + fr"\exp_pointnext_part_seg_nocls_segmentation_nostn_segmentation_gonormal\ground_truth",ai_deconverter_root + fr"\exp_pointnext_part_seg_nocls_segmentation_nostn_segmentation_gonormal_standard_2D_add_stl\ground_truth",camera_angles_list=standard_views)
#transform_3D_batch.batch_transform_Cloud_STL_to_2D(processed_CAD_root + fr"\stl_upright_z_parts_identify\tree", ai_deconverter_root + fr"\exp_pointnext_part_seg_nocls_segmentation_nostn_segmentation_gonormal\prediction",ai_deconverter_root + fr"\exp_pointnext_part_seg_nocls_segmentation_nostn_segmentation_gonormal_standard_2D_add_stl\prediction",camera_angles_list=standard_views)

#transform_3D_batch.batch_transform_Cloud_STL_to_2D(processed_CAD_root + fr"\stl_upright_z_parts_identify\tree", ai_deconverter_root + fr"\exp_pointnext_part_seg_nocls_regress_stn_global_gaussian_gonormal\ground_truth",ai_deconverter_root + fr"\exp_pointnext_part_seg_nocls_regress_stn_global_gaussian_gonormal_standard_2D_add_stl\ground_truth",camera_angles_list=standard_views)
#ransform_3D_batch.batch_transform_Cloud_STL_to_2D(processed_CAD_root + fr"\stl_upright_z_parts_identify\tree", ai_deconverter_root + fr"\exp_pointnext_part_seg_nocls_regress_stn_global_gaussian_gonormal\prediction",ai_deconverter_root + fr"\exp_pointnext_part_seg_nocls_regress_stn_global_gaussian_gonormal_standard_2D_add_stl\prediction",camera_angles_list=standard_views)


# transform_3D_batch.batch_transform_Cloud_STL_to_2D(processed_CAD_root + fr"\stl_upright_z_parts_identify\tree", ai_deconverter_root + fr"\exp_pointnext_part_seg_nocls_segmentation_stn_segmentation_gonormal\prediction",ai_deconverter_root + fr"\exp_pointnext_part_seg_nocls_segmentation_stn_segmentation_gonormal_standard_2D_add_stl\prediction",camera_angles_list=standard_views)
# transform_3D_batch.batch_transform_Cloud_STL_to_2D(processed_CAD_root + fr"\stl_upright_z_parts_identify\tree", ai_deconverter_root + fr"\exp_pointnext_part_seg_nocls_segmentation_stn_segmentation_gonormal\ground_truth",ai_deconverter_root + fr"\exp_pointnext_part_seg_nocls_segmentation_stn_segmentation_gonormal_standard_2D_add_stl\ground_truth",camera_angles_list=standard_views)


# transform_3D_batch.batch_process_contact_gen(processed_CAD_root +fr"\normal_cloud_upright_z_parts_{str(2**11)}" ,processed_CAD_root +  fr"\normal_cloud_upright_z_parts_contact_controlled_gaussian_{s
# tr(2**11)}",label_mode="controlled_gaussian")
# transform_3D_batch.batch_rename_and_copy_by_mode(processed_CAD_root + r"\csv_identify_parts",processed_CAD_root + fr"\normal_cloud_upright_z_parts_contact_controlled_gaussian_2048\tree",processed_CAD_root + fr"\normal_cloud_upright_z_parts_contact_controlled_gaussian_identify_2048\tree")

# transform_3D_batch.batch_process_contact_gen(processed_CAD_root +fr"\normal_cloud_upright_z_parts_{str(2**12)}" ,processed_CAD_root +  fr"\normal_cloud_upright_z_parts_contact_controlled_gaussian_{str(2**12)}",label_mode="controlled_gaussian")
# transform_3D_batch.batch_rename_and_copy_by_mode(processed_CAD_root + r"\csv_identify_parts",processed_CAD_root + fr"\normal_cloud_upright_z_parts_contact_controlled_gaussian_4096\tree",processed_CAD_root + fr"\normal_cloud_upright_z_parts_contact_controlled_gaussian_identify_4096\tree")

# transform_3D_batch.batch_process_contact_gen(processed_CAD_root +fr"\normal_cloud_upright_z_parts_{str(2**13)}" ,processed_CAD_root +  fr"\normal_cloud_upright_z_parts_contact_controlled_gaussian_{str(2**13)}",label_mode="controlled_gaussian")
# transform_3D_batch.batch_rename_and_copy_by_mode(processed_CAD_root + r"\csv_identify_parts",processed_CAD_root + fr"\normal_cloud_upright_z_parts_contact_controlled_gaussian_8192\tree",processed_CAD_root + fr"\normal_cloud_upright_z_parts_contact_controlled_gaussian_identify_8192\tree")

