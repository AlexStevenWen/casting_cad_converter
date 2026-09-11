import transform_3D
import transform_3D_batch
def process_3d_file_unified(
    operation: str,
    in_path: str,
    out_path: str,
    # --- 以下是所有可選參數 ---
    # STEP 相關
    in_path_merged: str = None,
    out_path_merged: str = "out_merged",
    # 通用轉換參數
    Fvector: tuple = (0, 0, 0),
    Frotation: float = 0,
    Fmoving: tuple = (0, 0, 0),
    # STEP 轉網格參數
    tolerance: float = 0.1,
    tessellate_value: float = 0.1,
    # STL 處理參數
    mode: str = 'random',
    number_of_points: int = 65536,
    voxel_size: float = 1.0,
    # STL 轉深度圖參數
    camera_angles_list: list = None,
    image_width: int = 512,
    image_height: int = 512,
    radius: float = 150.0,
    depth_range: list = None
):
    """
    統一處理3D檔案轉換和操作的函數 (所有參數都在簽名中)。

    :param operation: 要執行的操作類型。
    :param in_path: 輸入檔案路徑。
    :param out_path: 輸出檔案路徑。
    :param ...: 其他所有可選參數。
    """
    print(f"\n--- Executing operation: '{operation}' ---")
    print(f"Input: '{in_path}', Output: '{out_path}'")
    
    try:
        if operation == 'move_step':
            transform_3D.transform_moving_step(
                in_path_assembly=in_path,
                in_path_merged=in_path_merged,
                out_path_assembly=out_path,
                out_path_merged=out_path_merged,
                Fvector=Fvector,
                Frotation=Frotation
            )

        elif operation == 'merge_step':
            transform_3D.transform_Step_OCC(in_path, out_path)

        elif operation == 'step_to_mesh':
            transform_3D.transform_3D(
                in_path,
                out_path,
                Fvector=Fvector,
                Frotation=Frotation,
                Fmoving=Fmoving,
                tolerance=tolerance,
                tessellate_value=tessellate_value
            )
        elif operation == 'step_to_parameter':
            transform_3D.Parameter_DATA(in_path,
                                        mode=mode,
                                        Fvector=Fvector,
                                        Frotation=Frotation,).to_hdf5(out_path, mode='w')

        elif operation in ['stl_to_cloud', 'stl_to_mesh', 'stl_to_normal_cloud', 'stl_to_voxel', 'stl_to_deep']:
            stl_processor = transform_3D.STL_DATA(in_path=in_path, out_path=out_path)
            
            if operation == 'stl_to_cloud':
                stl_processor.STLtoCloud(mode=mode, number_of_points=number_of_points, voxel_size=voxel_size)
            
            elif operation == 'stl_to_mesh':
                stl_processor.STLtoMesh()

            elif operation == 'stl_to_normal_cloud':
                stl_processor.STLtoNormalCloud(mode=mode, number_of_points=number_of_points, voxel_size=voxel_size)

            elif operation == 'stl_to_voxel':
                stl_processor.STLtoVoxel(voxel_size=voxel_size)

            elif operation == 'stl_to_deep':
                if not camera_angles_list or not depth_range:
                     raise ValueError("'stl_to_deep' 需要 'camera_angles_list' 和 'depth_range' 參數。")
                stl_processor.STLtoDeep(
                    camera_angles_list, image_width, image_height, radius, depth_range
                )
        
        # ... 其他 operation 可以繼續添加
        
        else:
            print(f"Error: Unknown operation '{operation}'")

        print(f"--- Operation '{operation}' completed successfully. ---")

    except Exception as e:
        print(f"Error during operation '{operation}': {e}")
def process_3d_file_unified_batch(
    operation: str,
    # --- 批量處理的目錄參數 ---
    input_dir: str = None,
    output_dir: str = None,
    input_dir_assembly: str = None,
    input_dir_merged: str = None,
    output_dir_assembly: str = None,
    output_dir_merged: str = None,
    # --- 所有子函數的可選參數 ---
    Fvector: tuple = (0, 0, 0),
    Frotation: float = 0,
    tolerance: float = 0.1,
    tessellate_value: float = 0.1, # 統一使用 tessellate_value
    mode: str = None,
    number_of_points: int = 1024, # 統一使用 number_of_points
    voxel_size: float = 10.0,
    camera_angles_list: list = None,
    image_width: int = 1024,
    image_height: int = 1024,
    radius: float = 128,
    depth_range: list = None
):
    """
    統一的批量任務調度函數 (Facade)。
    根據 operation 參數，呼叫 transform_3D_batch 模組中對應的函數。
    """
    print(f"\n===== Dispatching Batch Job: '{operation}' =====")
    
    if operation == 'step_to_3D':
        # 預設輸出模式為 .stl
        output_mode = mode if mode is not None else '.stl'
        transform_3D_batch.batch_transform_Step_to_3D(
            input_dir=input_dir,
            output_dir=output_dir,
            mode=output_mode,
            Fvector=Fvector,
            Frotation=Frotation,
            tolerance=tolerance,
            # 注意：這裡將 tessellate_value 傳遞給底層函數的 tessellate 參數
            tessellate=tessellate_value
        )
    elif operation == 'step_to_parameter':
        transform_3D_batch.batch_transform_Step_to_Parameter(
            input_dir=input_dir,
            output_dir=output_dir
        )
        
    elif operation == 'merge_step':
        output_mode = mode if mode is not None else '.step'
        transform_3D_batch.batch_transform_Step_to_3D_OCC(
            input_dir=input_dir,
            output_dir=output_dir,
            mode=output_mode
        )

    elif operation == 'stl_to_cloud':
        output_mode = mode if mode is not None else '.h5'
        transform_3D_batch.batch_transform_Stl_to_cloud(
            input_dir=input_dir,
            output_dir=output_dir,
            # 注意：參數名稱的對應
            point_num=number_of_points,
            mode=output_mode
        )
    elif operation == 'stl_to_deep':
        # 對於 stl_to_deep，其 mode 預設為空字串 (代表建立子目錄)
        output_mode = mode if mode is not None else ""
        transform_3D_batch.batch_transform_Stl_to_Deep(
            input_dir=input_dir,
            output_dir=output_dir,
            camera_angles_list=camera_angles_list,
            image_width=image_width,
            image_height=image_height,
            radius=radius,
            depth_range=depth_range,
            mode=output_mode
        )
        
        
    elif operation == 'stl_to_voxel':
        output_mode = mode if mode is not None else '.h5'
        transform_3D_batch.batch_transform_Stl_to_voxel(
            input_dir=input_dir,
            output_dir=output_dir,
            voxel_size=voxel_size,
            mode=output_mode
        )

    elif operation == 'move_step_by_merged':
        output_mode = mode if mode is not None else '.step'
        transform_3D_batch.batch_transform_Step_to_3D_moving(
            input_dir_assembly=input_dir_assembly,
            input_dir_merged=input_dir_merged,
            output_dir=output_dir, # moving 只有一個 output_dir
            mode=output_mode,
            Fvector=Fvector,
            Frotation=Frotation
        )

    elif operation == 'move_step_by_merged_double':
        output_mode = mode if mode is not None else '.step'
        transform_3D_batch.batch_transform_Step_to_3D_moving_double(
            input_dir_assembly=input_dir_assembly,
            input_dir_merged=input_dir_merged,
            output_dir_assembly=output_dir_assembly,
            output_dir_merged=output_dir_merged,
            mode=output_mode,
            Fvector=Fvector,
            Frotation=Frotation
        )

    # ...可以繼續添加其他 operation 的 elif 分支...
    # 例如：'step_to_parameter', 'stl_to_normalcloud', 'stl_to_deep'
        
    else:
        print(f"Error: Unknown operation '{operation}'")
        
    print(f"===== Batch Job '{operation}' Dispatched. =====")
    




