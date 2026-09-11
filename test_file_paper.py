
import time 
#from transform_3D import STL_DATA , transform_Step_OCC ,transform_Step_OCCseg,transform_Step_OCCsegre,transform_3D,transform_moving_step,CloudtoSkl,MeshtoSkl,Plot_to_stl_Skl,Plot_to_pc_Skl,transform_OCCstl,transform_stlmerge,transform_step_cloud,ParameterExtractor,transform_Cloud_2D,transform_Cloud_STL_2D
import transform_3D
from transform_3D_batch import batch_transform_Step_to_3D ,batch_transform_Stl_to_cloud
from pc_surface_detection import visualize_dataset ,process_assembly_data_gen
import os
six_views = [
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
#原始組樹圖檔
transform_3D.STEPto2D(step_file=r"D:\ChynWangProject\data\processed_CAD\step_raw_component\tree\1-1152-S260225\1-1152 assembly.step",
                      output_folder=r"D:\ChynWangProject\automated_cad_pipeline\src\ai_deconveter\All_Restored_Experiments\1-1152\1treeraw"
                      ,camera_angles=six_views,image_width=1024,image_height=1024)
#合併組樹圖檔
transform_3D.STEPto2D(step_file=r"D:\ChynWangProject\data\processed_CAD\step_raw_merge\tree\1-1152-S260225\1-1152 assembly.step",
                      output_folder=r"D:\ChynWangProject\automated_cad_pipeline\src\ai_deconveter\All_Restored_Experiments\1-1152\2treemer"
                      ,camera_angles=six_views,image_width=1024,image_height=1024)

#中心圖檔
transform_3D.STEPto2D(step_file=r"D:\ChynWangProject\data\processed_CAD\step_upright_z_merge\tree\1-1152-S260225\1-1152 assembly.step",
                      output_folder=r"D:\ChynWangProject\automated_cad_pipeline\src\ai_deconveter\All_Restored_Experiments\1-1152\3treemerce"
                      ,camera_angles=six_views,image_width=1024,image_height=1024)


#原始組樹圖檔
transform_3D.STEPto2D(step_file=r"D:\ChynWangProject\data\processed_CAD\step_raw_component\tree\89S3-A1-08-S240717\89S3-A1-08 assembly.step",
                      output_folder=r"D:\ChynWangProject\automated_cad_pipeline\src\ai_deconveter\All_Restored_Experiments\89S3-A1-08\1treeraw"
                      ,camera_angles=six_views,image_width=1024,image_height=1024)
#合併組樹圖檔
transform_3D.STEPto2D(step_file=r"D:\ChynWangProject\data\processed_CAD\step_raw_merge\tree\89S3-A1-08-S240717\89S3-A1-08 assembly.step",
                      output_folder=r"D:\ChynWangProject\automated_cad_pipeline\src\ai_deconveter\All_Restored_Experiments\89S3-A1-08\2treemer"
                      ,camera_angles=six_views,image_width=1024,image_height=1024)

#中心圖檔
transform_3D.STEPto2D(step_file=r"D:\ChynWangProject\data\processed_CAD\step_upright_z_merge\tree\89S3-A1-08-S240717\89S3-A1-08 assembly.step",
                      output_folder=r"D:\ChynWangProject\automated_cad_pipeline\src\ai_deconveter\All_Restored_Experiments\89S3-A1-08\3treemerce"
                      ,camera_angles=six_views,image_width=1024,image_height=1024)
# ==============================================================================
# 1. 零件與實驗目錄動態參數設定（只需改這裡）
# ==============================================================================
#, "103-200213", "10713627", "10731478", "20446701D", "G02G670600", "M107-52-01", "SW0203VW01-TL"
PART_NAMES = ["1-1152", "89S3-A1-08"]

for PART_NAME in PART_NAMES:

    # 填入對應實驗的完整資料夾名稱
    EXP_LOCAL_LINEAR = "exp_pointnext_part_seg_nocls_msg_bottleneckmlp_nostn_regress_custom_local_linear_4096_2026-06-29_21-32-16"
    EXP_GAUSSIAN = "exp_pointnext_part_seg_nocls_msg_bottleneckmlp_nostn_regress_custom_gaussian_4096_2026-06-30_08-06-02"
    EXP_GLOBAL_GAUSSIAN = "exp_pointnext_part_seg_nocls_msg_bottleneckmlp_nostn_regress_custom_global_gaussian_4096_2026-06-30_17-30-32"
    EXP_GLOBAL_LINEAR = "exp_pointnext_part_seg_nocls_msg_bottleneckmlp_nostn_regress_custom_global_linear_4096_2026-06-30_14-27-05"
    EXP_BINARY = "exp_pointnext_part_seg_nocls_msg_bottleneckmlp_nostn_seg_custom_4096_2026-06-29_10-15-09"

    # ==============================================================================
    # 2. 共用基礎路徑定義
    # ==============================================================================
    BASE_PROCESSED_CAD = r"D:\ChynWangProject\data\processed_CAD"
    BASE_EXPERIMENTS = r"D:\ChynWangProject\automated_cad_pipeline\src\ai_deconveter\All_Restored_Experiments"

    # 自動組裝輸出與輸入的基本路徑
    out_base_dir = os.path.join(BASE_EXPERIMENTS, PART_NAME)
    stl_file_path = os.path.join(BASE_PROCESSED_CAD, "stl_upright_z_parts_id", f"{PART_NAME}.stl")

    # 視角與圖檔解析度參數設定
    view_params = {
        "camera_angles_list": six_views,
        "image_width": 1024,
        "image_height": 1024,
        "radius": 200,
        "depth_range": [0, 200]
    }

    #STEP 轉 2D 備用 (若有需要取消註解即可)
    transform_3D.STEPto2D(
        step_file=os.path.join(BASE_PROCESSED_CAD, "step_upright_z_parts_identify", "id_parts", f"{PART_NAME}.step"),
        output_folder=os.path.join(out_base_dir, "4blk"),
        camera_angles=six_views, image_width=1024, image_height=1024
    )

    # ==============================================================================
    # 3. 基礎特徵 Cloudto2D 轉換 (樹狀結構特徵)
    # ==============================================================================
    # features = {
    #     "5blkccbinary": "normalcloud_upright_z_parts_fps_binary_identify_4096",
    #     "5blkcclocal_linear": "normalcloud_upright_z_parts_fps_local_linear_identify_4096",
    #     "5blkcclocal_gaussian": "normalcloud_upright_z_parts_fps_local_linear_identify_4096", # 依原稿維持該路徑
    #     "5blkccglobal_gaussian": "normalcloud_upright_z_parts_fps_global_gaussian_identify_4096",
    #     "5blkccglobal_linear": "normalcloud_upright_z_parts_fps_global_linear_identify_4096"
    # }

    # for sub_folder, feature_dir in features.items():
    #     in_h5 = os.path.join(BASE_PROCESSED_CAD, "normalcloud_upright_z_identify", feature_dir, "tree", f"{PART_NAME}.h5")
    #     out_dir = os.path.join(out_base_dir, sub_folder)
        
    #     transform_3D.STL_DATA(in_path=in_h5, out_path=out_dir).Cloudto2D(
    #         camera_angles_list=six_views, image_width=1024, image_height=1024, radius=200, depth_range=100
    #     )

    # # ==============================================================================
    # # 4. AI 模型預測與 Ground Truth 實驗對比（已加入二元版本）
    # # ==============================================================================
    # experiments = [
    #     {"name": "local_linear", "exp_folder": EXP_LOCAL_LINEAR, "prefix": "5blkcc_"},
    #     {"name": "gaussian", "exp_folder": EXP_GAUSSIAN, "prefix": "5blkcc_"},
    #     {"name": "global_gaussian", "exp_folder": EXP_GLOBAL_GAUSSIAN, "prefix": "5blkcc_"},
    #     {"name": "global_linear", "exp_folder": EXP_GLOBAL_LINEAR, "prefix": "5blkcc_"},
    #     {"name": "binary", "exp_folder": EXP_BINARY, "prefix": ""} # 二元版本沒有 5blkcc_ 前綴
    # ]

    # for exp in experiments:
    #     exp_name = exp["name"]
    #     exp_folder = exp["exp_folder"]
    #     pfx = exp["prefix"]
        
    #     # --- Prediction ---
    #     pd_cloud = os.path.join(BASE_EXPERIMENTS, exp_folder, "test", "prediction", f"{PART_NAME}.h5")
    #     pd_out = os.path.join(out_base_dir, f"{pfx}pd_{exp_name}")
        
    #     tp_pd = transform_3D.transform_Cloud_STL_2D(cloud_path=pd_cloud, stl_path=stl_file_path, out_path=pd_out)
    #     tp_pd.Cloudto2D(**view_params)
        
    #     # --- Ground Truth ---
    #     gt_cloud = os.path.join(BASE_EXPERIMENTS, exp_folder, "test", "ground_truth", f"{PART_NAME}.h5")
    #     gt_out = os.path.join(out_base_dir, f"{pfx}gt_{exp_name}")
        
    #     tp_gt = transform_3D.transform_Cloud_STL_2D(cloud_path=gt_cloud, stl_path=stl_file_path, out_path=gt_out)
    #     tp_gt.Cloudto2D(**view_params)

    print(f" 零件 {PART_NAME} 所有獨立毛胚 2D 圖檔與 AI 預測對比圖渲染完成！")


