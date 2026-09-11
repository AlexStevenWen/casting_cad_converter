# cad_converter (3D CAD & Point Cloud Processing Pipeline)

**cad_converter** is a highly integrated 3D geometry preprocessing module designed for precision investment casting prediction systems. It serves as a core data-preprocessing component for the master's thesis research on **Classification and Process Prediction of Gating Systems for Investment Casting of A356 Aluminum Alloy**. This module is responsible for transforming raw engineering CAD files (STEP) with high geometric noise into standardized feature vectors and multi-modal point cloud data. These outputs can be directly consumed by downstream machine learning and deep learning models (e.g., Auto-sklearn, PointNeXt, UprightRL).

To resolve dependency conflicts among different underlying geometry engines, this module features a built-in **hybrid environment scheduler**. It automatically isolates and invokes multiple virtual environments, including FreeCAD, PythonOCC, Open3D, and PcSkeletor, for dedicated computations.

## Project Background and Academic Context

This tool is part of the experimental methodology of the following master's thesis:

- **Thesis Title**: A Study on the Classification and Process Prediction of Gating Systems for Investment Casting of A356 Aluminum Alloy
- **Author**: HSU, WEN-HO
- **Advisor**: CHEN, TZUNG-MING
- **Institution**: National Changhua University of Education
- **Department**: Department of Electrical and Mechanical Technology
- **Degree**: Master's Thesis
- **Oral Defense Date**: 2026-07-10
- **Permanent URL**: [https://hdl.handle.net/11296/32a644](https://hdl.handle.net/11296/32a644)

**Keywords**: A356 aluminum alloy, investment casting, automated machine learning (AutoML), 3D point cloud semantic segmentation.

The research aims to establish a gating system classification model and process prediction system for A356 aluminum alloy investment casting. A critical step is the conversion of raw CAD assemblies into clean, standardized representations suitable for automated machine learning (AutoML) and 3D point cloud semantic segmentation. `cad_converter` fulfills this role by providing robust topology repair, blank identification, point cloud sampling, feature extraction, and soft label generation, thereby enabling the downstream modeling and prediction tasks of the thesis.

## Key Features

*   **Automated Virtual Environment Management**:
    *   Built-in environment setup scripts (`OCCHybridEnvCreate`, `FreeCADvenvCreate`, etc.). Upon execution, the program automatically checks for and creates isolated Conda/Venv environments to resolve underlying C++ geometry engine package conflicts.
*   **Topology Repair & Multi-Solid Fusion (Deep Healing & Smart Fuse)**:
    *   Addresses common issues in STEP file conversions, such as broken faces and discrete solids. It utilizes bounding box collision pre-filtering and a three-stage merging strategy (Exact, Micro-Nudge, Fuzzy-Asymmetric). Supplemented by an anti-collapse mechanism, it reconstructs perfect, closed manifold solids.
*   **Automated Casting Blank Identification (ICP & Volume)**:
    *   Abandons traditional bounding box comparisons, which are susceptible to shape interference. Instead, it uses rigid body volume invariants for `O(1)` fast pre-screening, combined with FPFH + RANSAC and multi-stage ICP point cloud registration, to automatically extract the true casting blank from complex assembly trees.
*   **Mesh Reduction & Point Cloud Sampling**:
    *   Reduces continuous geometry into highly uniform point clouds. Built-in algorithms include Farthest Point Sampling (FPS), Surface Uniform Sampling, and Solid Voxelization, with strict tensor dimension alignment (N×3 or N×6 with normals).
*   **Macro-Feature & Spatial Fingerprint Extraction**:
    *   Directly calls the geometry kernel to parse solid topology, extracting volume, surface area, Euler characteristic, center of mass, 3×3 inertia matrix, and maximum orthogonal projection areas. These serve as tabular feature inputs for downstream AutoML models.
*   **Soft Label Heatmaps & 2D Rendering**:
    *   Provides multiple modes for generating soft labels for gate contact areas (global linear, Gaussian decay, sigmoid curve, etc.) to match the physical characteristics of gradient casting contacts.
    *   Supports 2D depth map extraction and hybrid Point Cloud/STL rendering, featuring a built-in "spotlight mode" to highlight specific geometric features while darkening the surroundings.

---

## Environment & Dependencies

This module is orchestrated via the main program (`main.py`). On the first run, it will **automatically create** the following sub-environments:
*   **FreeCAD Environment**: Handles parametric modeling, feature attribute calculation, and basic spatial transformations.
*   **OCC Environment (PythonOCC)**: Executes low-level boolean operations, deep topology healing, and geometric feature exploration.
*   **PcSkeletor / PyVista Environment**: Handles point cloud skeletonization and mesh operations.

**Base Environment Dependencies**:
```bash
pip install open3d numpy pandas h5py trimesh matplotlib scipy scikit-learn
Usage
The module is driven by a Command Line Interface (CLI) and a JSON configuration file. It supports both single-file and batch folder processing, making it easy to integrate into automated CI/CD pipelines.

Execution Command

bash
python main.py --config config.json
Configuration Example (config.json)

json
{
    "processing_pipeline": [
        {
            "task_name": "Assembly Topology Repair and Feature Extraction",
            "type": "single",
            "enabled": true,
            "parameters": {
                "operation": "transform_Step_OCC",
                "in_path": "C:\\CAD_Files\\assembly_raw.step",
                "out_put": "C:\\CAD_Files\\assembly_fixed.step"
            }
        },
        {
            "task_name": "Batch Point Cloud Conversion and Soft Label Generation",
            "type": "batch",
            "enabled": true,
            "parameters": {
                "operation": "process_assembly_data_gen",
                "input_dir": "C:\\CAD_Files\\Mesh",
                "output_dir": "C:\\CAD_Files\\PointCloud_Dataset",
                "contact_threshold": 1.5,
                "label_mode": "global_linear",
                "output_format": ".npz"
            }
        }
    ]
}
Output Data Formats
Tabular Features (.h5, .csv): Contains multi-dimensional macro parameters of the solids.

Standard Point Clouds (.npz, .ply): N×3 or N×6 point cloud tensors aligned to a standard orientation.

Semantic Segmentation Datasets (.npz): Shape (N, 7), containing [x, y, z, nx, ny, nz, contact_intensity], specifically formatted for deep learning networks like PointNeXt.

Rendered Images (.png): Multi-view 2D depth maps and heatmap renderings.

Exit Status
Exit Code 0 (status: success): All enabled conversion and processing tasks completed successfully.

Exit Code 1 (status: error): Configuration syntax error, corrupted CAD files, or a subprocess crashed during execution.

Citation
If this tool is helpful to your research, please cite the following thesis:

HSU, W.-H. (2026). A Study on the Classification and Process Prediction of Gating Systems for Investment Casting of A356 Aluminum Alloy (Master's thesis). National Changhua University of Education, Department of Electrical and Mechanical Technology, Changhua City. Retrieved from https://hdl.handle.net/11296/32a644

text

You can directly replace your existing `README.md` with the above content. If you would like any further adjustments, such as a different placement of the citation or additional details, just let me know.
