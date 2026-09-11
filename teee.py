for exp in range(10, 15):
    size_str = str(2**exp)
    
    # 1. 定義輸入與輸出的路徑
    input_cloud_dir = os.path.join(processed_CAD_root, "normal_cloud", f"normal_cloud_upright_z_parts_random_{size_str}")
    
    # 2. 定義 Contact controlled_gaussian 的路徑
    contact_controlled_gaussian_dir = os.path.join(processed_CAD_root, "normal_cloud", f"normal_cloud_upright_z_parts_random_contact_controlled_gaussian_{size_str}")
    
    # 3. 定義 Identify 的路徑
    csv_identify_dir = os.path.join(processed_CAD_root, "csv_identify_parts")
    final_output_dir = os.path.join(processed_CAD_root, "normal_cloud", f"normal_cloud_upright_z_parts_random_contact_controlled_gaussian_identify_{size_str}")

    print(f"--- 正在處理 2^{exp} (Size: {size_str}) ---")

    # 執行 Contact Generation
    transform_3D_batch.batch_process_contact_gen(
        input_cloud_dir,
        contact_controlled_gaussian_dir,
        label_mode="controlled_gaussian"
    )

    # 執行 Rename 與 Copy
    transform_3D_batch.batch_rename_and_copy_by_mode(
        csv_identify_dir,
        os.path.join(contact_controlled_gaussian_dir,"tree"),
        os.path.join(final_output_dir,"tree")
    )

print("所有批次任務已完成！")

for exp in range(10, 15):
    size_str = str(2**exp)
    
    # 1. 定義輸入與輸出的路徑
    input_cloud_dir = os.path.join(processed_CAD_root, "normal_cloud", f"normal_cloud_upright_z_parts_fps_{size_str}")
    
    # 2. 定義 Contact controlled_gaussian 的路徑
    contact_controlled_gaussian_dir = os.path.join(processed_CAD_root, "normal_cloud", f"normal_cloud_upright_z_parts_fps_contact_controlled_gaussian_{size_str}")
    
    # 3. 定義 Identify 的路徑
    csv_identify_dir = os.path.join(processed_CAD_root, "csv_identify_parts")
    final_output_dir = os.path.join(processed_CAD_root, "normal_cloud", f"normal_cloud_upright_z_parts_fps_contact_controlled_gaussian_identify_{size_str}")

    print(f"--- 正在處理 2^{exp} (Size: {size_str}) ---")

    # 執行 Contact Generation
    transform_3D_batch.batch_process_contact_gen(
        input_cloud_dir,
        contact_controlled_gaussian_dir,
        label_mode="controlled_gaussian"
    )

    # 執行 Rename 與 Copy
    transform_3D_batch.batch_rename_and_copy_by_mode(
        csv_identify_dir,
        os.path.join(contact_controlled_gaussian_dir,"tree"),
        os.path.join(final_output_dir,"tree")
    )

print("所有批次任務已完成！")

for exp in range(10, 15):
    size_str = str(2**exp)
    
    # 1. 定義輸入與輸出的路徑
    input_cloud_dir = os.path.join(processed_CAD_root, "normal_cloud", f"normal_cloud_upright_z_parts_surface_uniform_{size_str}")
    
    # 2. 定義 Contact controlled_gaussian 的路徑
    contact_controlled_gaussian_dir = os.path.join(processed_CAD_root, "normal_cloud", f"normal_cloud_upright_z_parts_surface_uniform_contact_controlled_gaussian_{size_str}")
    
    # 3. 定義 Identify 的路徑
    csv_identify_dir = os.path.join(processed_CAD_root, "csv_identify_parts")
    final_output_dir = os.path.join(processed_CAD_root, "normal_cloud", f"normal_cloud_upright_z_parts_surface_uniform_contact_controlled_gaussian_controlled_gaussian_{size_str}")

    print(f"--- 正在處理 2^{exp} (Size: {size_str}) ---")

    # 執行 Contact Generation
    transform_3D_batch.batch_process_contact_gen(
        input_cloud_dir,
        contact_controlled_gaussian_dir,
        label_mode="controlled_gaussian"
    )

    # 執行 Rename 與 Copy
    transform_3D_batch.batch_rename_and_copy_by_mode(
        csv_identify_dir,
        os.path.join(contact_controlled_gaussian_dir,"tree"),
        os.path.join(final_output_dir,"tree")
    )

print("所有批次任務已完成！")