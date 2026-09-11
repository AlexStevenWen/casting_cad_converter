import sys
import os
import csv
import traceback
import numpy as np
import open3d as o3d
import shutil
from pathlib import Path
import math
sys.stdout.reconfigure(encoding='utf-8')
import tempfile

# 匯入 OCC 相關模組
from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.StlAPI import StlAPI_Writer
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import (
    TopAbs_SOLID, TopAbs_SHELL,
    TopAbs_COMPOUND, TopAbs_REVERSED
)
from OCC.Core.TopoDS import topods_Solid, topods_Shell
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeSolid
from OCC.Core.BRepCheck import BRepCheck_Analyzer
from OCC.Core.BRepGProp import brepgprop
from OCC.Core.GProp import GProp_GProps
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh

def is_valid_solid(solid):
    """檢查實體是否有效。"""
    analyzer = BRepCheck_Analyzer(solid)
    return analyzer.IsValid()

def get_shape_volume(shape):
    """計算形狀的體積。"""
    props = GProp_GProps()
    brepgprop.VolumeProperties(shape, props)
    vol = props.Mass()
    return vol if vol > 1e-9 else 0.0

def explore_solids(shape):
    """遞歸探索幾何結構中的所有有效實體。"""
    solids = []

    def add_unique_solid(new_solid):
        volume = get_shape_volume(new_solid)
        if volume <= 1e-6:
            return
        for s in solids:
            if s.IsSame(new_solid):
                return
        solids.append(new_solid)

    if shape.ShapeType() == TopAbs_SOLID:
        solid = topods_Solid(shape)
        add_unique_solid(solid)

    if shape.ShapeType() == TopAbs_SHELL:
        shell = topods_Shell(shape)
        if shell.Orientation() != TopAbs_REVERSED:
            builder = BRepBuilderAPI_MakeSolid(shell)
            if builder.IsDone():
                add_unique_solid(builder.Solid())

    if shape.ShapeType() == TopAbs_COMPOUND:
        exp_shell = TopExp_Explorer(shape, TopAbs_SHELL)
        while exp_shell.More():
            shell = topods_Shell(exp_shell.Current())
            if shell.Orientation() != TopAbs_REVERSED:
                builder = BRepBuilderAPI_MakeSolid(shell)
                if builder.IsDone():
                    add_unique_solid(builder.Solid())
            exp_shell.Next()

        exp_all = TopExp_Explorer(shape, TopAbs_SOLID)
        while exp_all.More():
            add_unique_solid(topods_Solid(exp_all.Current()))
            exp_all.Next()

        exp_comp = TopExp_Explorer(shape, TopAbs_COMPOUND)
        while exp_comp.More():
            sub = exp_comp.Current()
            if not sub.IsEqual(shape):
                for s in explore_solids(sub):
                    add_unique_solid(s)
            exp_comp.Next()

    return solids

import time # 用 time 替代 uuid

def read_main_solid_and_volume(step_path):
    safe_temp_dir = Path("./temp_step_safedir")
    safe_temp_dir.mkdir(parents=True, exist_ok=True)
    
    # 用當下時間的毫秒數來當檔名，例如: temp_1718693421.step
    safe_temp_filename = f"temp_{int(time.time() * 1000)}.step"
    temp_path = safe_temp_dir / safe_temp_filename

    main_solid = None
    max_volume = 0.0

    try:
        # 將原始 STEP 複製到純英文的安全路徑
        shutil.copy2(str(step_path), str(temp_path))
        
        reader = STEPControl_Reader()
        status = reader.ReadFile(str(temp_path))
        
        if status != 1:
            print(f"ERROR: 讀取 STEP 檔案失敗 (OCC 解析錯誤): {step_path.name}")
            return None, 0

        reader.TransferRoots()
        shape = reader.OneShape()

        if shape is None:
            print(f"ERROR: {step_path.name} 的幾何資料為空")
            return None, 0

        all_solids = explore_solids(shape)
        if not all_solids:
            # 觸發此錯誤代表檔案是曲面模型，缺乏實體
            print(f"ERROR: 在 {step_path.name} 中未找到有效的實體 (可能為純曲面模型)")
            return None, 0

        max_volume = -1.0
        for s in all_solids:
            vol = get_shape_volume(s)
            if vol > max_volume:
                max_volume = vol
                main_solid = s

        if main_solid is None or max_volume <= 1e-6:
            print(f"ERROR: 未能在 {step_path.name} 中找到體積大於0的主實體")
            return None, 0

    except Exception as e:
        print(f"ERROR: 解析檔案 {step_path.name} 時發生異常: {e}")
        return None, 0
    finally:
        # 清理暫存檔
        try:
            if temp_path.exists():
                temp_path.unlink()
        except OSError:
            pass

    return main_solid, max_volume

def convert_shape_to_stl(shape, stl_path):
    """將 OpenCASCADE 拓撲形狀網格化並輸出為 STL。"""
    try:
        linear_deflection = 0.05  # 提高網格精細度以利點雲採樣
        angular_deflection = 0.3
        mesh = BRepMesh_IncrementalMesh(shape, linear_deflection, False, angular_deflection, False)
        mesh.Perform()
        if not mesh.IsDone():
            print("ERROR: BRepMesh 網格化失敗")
            return False

        writer = StlAPI_Writer()
        writer.SetASCIIMode(False)
        return writer.Write(shape, str(stl_path))
    except Exception as e:
        print(f"ERROR: 轉換 STL 失敗: {e}")
        return False

def load_and_center_pcd(stl_path, num_points=25000):
    """載入 STL 網格，均勻採樣點雲並置中。"""
    try:
        mesh = o3d.io.read_triangle_mesh(str(stl_path))
        if not mesh.has_vertices():
            return None, None

        pcd = mesh.sample_points_poisson_disk(num_points)
        if not pcd.has_points():
            return None, None

        original_centroid = pcd.get_center()
        pcd_centered = pcd.translate(-original_centroid, relative=False)

        # 根據點雲包圍盒動態估計合適的法線搜尋半徑
        bbox = pcd_centered.get_axis_aligned_bounding_box()
        diag = np.linalg.norm(bbox.get_max_bound() - bbox.get_min_bound())
        radius_normal = max(0.5, diag / 40.0)
        
        pcd_centered.estimate_normals(
            search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=radius_normal, max_nn=40))
        pcd_centered.orient_normals_consistent_tangent_plane(15)

        return pcd_centered, original_centroid
    except Exception as e:
        print(f"ERROR: 處理點雲失敗 {stl_path}: {e}")
        return None, None

def preprocess_point_cloud(pcd, voxel_size):
    """特徵下採樣與 FPFH 計算（搜尋半徑與體素大小連動）。"""
    pcd_down = pcd.voxel_down_sample(voxel_size)
    
    radius_normal = voxel_size * 2.5
    pcd_down.estimate_normals(
        o3d.geometry.KDTreeSearchParamHybrid(radius=radius_normal, max_nn=30))
    
    radius_feature = voxel_size * 5.0
    pcd_fpfh = o3d.pipelines.registration.compute_fpfh_feature(
        pcd_down,
        o3d.geometry.KDTreeSearchParamHybrid(radius=radius_feature, max_nn=100))
    return pcd_down, pcd_fpfh

def find_best_match(test_pcd_centered, candidate_reference_pcds_and_volumes):
    """
    採用動態體素尺寸與多階段漸進式 ICP（Coarse-to-Fine）進行精密比對。
    """
    # 1. 根據測試件的幾何尺寸，動態決定體素大小（避免大件過疏、小件過密）
    bbox = test_pcd_centered.get_axis_aligned_bounding_box()
    diag = np.linalg.norm(bbox.get_max_bound() - bbox.get_min_bound())
    voxel_size = max(0.5, diag / 60.0) 

    best_match = {
        "name": "None",
        "fitness": -1.0,
        "rmse": float('inf'),
        "transform": np.identity(4),
        "ref_volume": 0.0
    }

    source_down, source_fpfh = preprocess_point_cloud(test_pcd_centered, voxel_size)

    for ref_name, ref_data in candidate_reference_pcds_and_volumes.items():
        ref_pcd = ref_data["pcd"]
        ref_volume = ref_data["volume"]

        target_down, target_fpfh = preprocess_point_cloud(ref_pcd, voxel_size)

        # 階段一：精細化 RANSAC 特徵匹配（提高對準成功率）
        distance_threshold_ransac = voxel_size * 1.5
        ransac_result = o3d.pipelines.registration.registration_ransac_based_on_feature_matching(
            source_down, target_down, source_fpfh, target_fpfh, True,
            distance_threshold_ransac,
            o3d.pipelines.registration.TransformationEstimationPointToPoint(False), 3,
            [
                o3d.pipelines.registration.CorrespondenceCheckerBasedOnEdgeLength(0.9),
                o3d.pipelines.registration.CorrespondenceCheckerBasedOnDistance(distance_threshold_ransac)
            ],
            o3d.pipelines.registration.RANSACConvergenceCriteria(5000000, 0.999)
        )
        
        current_transform = ransac_result.transformation

        # 階段二：漸進式多階段 ICP 比對 (Coarse -> Medium -> Fine)
        # 逐步縮小收斂通道，確保大角度旋轉能拉回，且最終精確度極高
        icp_stages = [voxel_size * 4.0, voxel_size * 1.5, voxel_size * 0.4]
        
        icp_result = None
        for thres in icp_stages:
            icp_result = o3d.pipelines.registration.registration_icp(
                test_pcd_centered, ref_pcd, thres, current_transform,
                o3d.pipelines.registration.TransformationEstimationPointToPoint()
            )
            current_transform = icp_result.transformation

        if icp_result is not None:
            fitness = icp_result.fitness
            rmse = icp_result.inlier_rmse

            # 優先篩選 RMSE 較低且重合率足夠的參考件
            if rmse < best_match["rmse"]:
                best_match = {
                    "name": ref_name,
                    "fitness": fitness,
                    "rmse": rmse,
                    "transform": current_transform,
                    "ref_volume": ref_volume
                }

    return best_match

def matrix_to_strings(matrix):
    r_str = str(matrix[0:3, 0:3].flatten()).replace('\n', '')
    t_str = str(matrix[0:3, 3].flatten()).replace('\n', '')
    return r_str, t_str

def main():
    if len(sys.argv) < 4:
        print("用途: python match_parts.py <reference_path> <test_path> <output_csv_file>")
        return

    ref_path = Path(sys.argv[1])
    test_path = Path(sys.argv[2])
    output_csv = Path(sys.argv[3])

    if not ref_path.exists() or not test_path.exists():
        print("ERROR: 輸入的路徑不存在")
        return

    temp_dir = Path("./temp_stl_files")
    temp_ref_dir = temp_dir / "reference"
    temp_test_dir = temp_dir / "test"

    if temp_dir.exists():
        try: shutil.rmtree(temp_dir)
        except OSError: pass

    temp_ref_dir.mkdir(parents=True, exist_ok=True)
    temp_test_dir.mkdir(parents=True, exist_ok=True)

    reference_data_map = {}
    ref_files = list(ref_path.glob("*.step")) if ref_path.is_dir() else [ref_path]

    for idx, step_file in enumerate(ref_files):
        part_name = step_file.stem
        shape, volume = read_main_solid_and_volume(step_file)
        if not shape or volume <= 0: continue

        stl_path = temp_ref_dir / f"ref_part_{idx}.stl"
        if not convert_shape_to_stl(shape, stl_path): continue

        pcd_centered, _ = load_and_center_pcd(str(stl_path))
        if pcd_centered:
            reference_data_map[part_name] = {"pcd": pcd_centered, "volume": volume}

    results_data = []
    test_files = list(test_path.glob("*.step")) if test_path.is_dir() else [test_path]

    for idx, step_file in enumerate(test_files):
        test_part_name = step_file.stem
        shape, test_volume = read_main_solid_and_volume(step_file)
        if not shape or test_volume <= 0:
            results_data.append([test_part_name, "StepReadError", 0, 0, "N/A", "N/A", "N/A", "N/A", "N/A"])
            continue

        # 調整體積預篩選機制：放寬至 2.5% 以容忍鑄件毛邊或局部網格修補差異
        volume_tolerance = 0.025
        candidate_references = {}
        
        for ref_name, ref_data in reference_data_map.items():
            ref_volume = ref_data["volume"]
            is_close = math.isclose(test_volume, ref_volume, rel_tol=volume_tolerance)
            if is_close:
                candidate_references[ref_name] = ref_data

        if not candidate_references:
            stl_path_temp = temp_test_dir / f"test_temp_{idx}.stl"
            centroid_str = "N/A"
            if convert_shape_to_stl(shape, stl_path_temp):
                _, test_original_centroid = load_and_center_pcd(str(stl_path_temp))
                if test_original_centroid is not None:
                    centroid_str = f"{test_original_centroid[0]:.6f}, {test_original_centroid[1]:.6f}, {test_original_centroid[2]:.6f}"
                try: os.remove(stl_path_temp)
                except OSError: pass
            results_data.append([test_part_name, "NoVolumeMatch", 0, 0, centroid_str, "N/A (No Scaling)", "N/A", "N/A", "N/A"])
            continue

        stl_path = temp_test_dir / f"test_part_{idx}.stl"
        if not convert_shape_to_stl(shape, stl_path):
            results_data.append([test_part_name, "StlConvertError", 0, 0, "N/A", "N/A", "N/A", "N/A", "N/A"])
            continue

        test_pcd_centered, test_original_centroid = load_and_center_pcd(str(stl_path))
        if not test_pcd_centered:
            results_data.append([test_part_name, "PcdError", 0, 0, "N/A", "N/A", "N/A", "N/A", "N/A"])
            continue

        best_match = find_best_match(test_pcd_centered, candidate_references)
        matched_name = best_match["name"]
        fitness = best_match["fitness"]
        rmse = best_match["rmse"]
        ref_volume = best_match["ref_volume"]

        centroid_str = f"{test_original_centroid[0]:.6f}, {test_original_centroid[1]:.6f}, {test_original_centroid[2]:.6f}"
        
        volume_diff_percent_str = "N/A"
        if ref_volume > 1e-9 and test_volume > 1e-9:
            volume_diff_percent = abs(test_volume - ref_volume) / test_volume * 100
            volume_diff_percent_str = f"{volume_diff_percent:.2f}%"

        # 由於改用精細化 Coarse-to-Fine ICP，成功對齊的 RMSE 通常會顯著降至 1.5 以下
        fitness_ok = fitness > 0.82
        absolute_rmse_ok = rmse < 2.0 

        if matched_name != "None" and fitness_ok and absolute_rmse_ok:
            r_str, t_str = matrix_to_strings(best_match["transform"])
            results_data.append([test_part_name, matched_name, f"{fitness:.6f}", f"{rmse:.6f}", centroid_str, "N/A (No Scaling)", r_str, t_str, volume_diff_percent_str])
        else:
            results_data.append([test_part_name, "NoMatch", f"{fitness:.6f}", f"{rmse:.6f}", centroid_str, "N/A (No Scaling)", "N/A", "N/A", volume_diff_percent_str])

    try:
        if temp_dir.exists(): shutil.rmtree(temp_dir)
    except OSError: pass

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["TestPartFile", "MatchedReference", "ICP_Fitness (越高越好)", "ICP_RMSE (越低越好)", "Original_Centroid (X,Y,Z)", "Original_Scale (AvgRadius)", "Alignment_Rotation (3x3 Matrix)", "Alignment_Translation (X,Y,Z)", "VolumeDiff_Percent (%)"])
        writer.writerows(results_data)

if __name__ == "__main__":
    o3d.utility.set_verbosity_level(o3d.utility.VerbosityLevel.Error)
    main()