# cad_converter (3D CAD & Point Cloud Processing Pipeline)

**cad_converter** is a highly integrated 3D geometry preprocessing module designed for precision investment casting prediction systems. This module is responsible for transforming raw engineering CAD files (STEP) with high geometric noise into standardized feature vectors and multi-modal point cloud data. These outputs can be directly consumed by downstream machine learning and deep learning models (e.g., Auto-sklearn, PointNeXt, UprightRL).

To resolve dependency conflicts among different underlying geometry engines, this module features a built-in **hybrid environment scheduler**. It automatically isolates and invokes multiple virtual environments, including FreeCAD, PythonOCC, Open3D, and PcSkeletor, for dedicated computations.

---

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
Bash
python main.py --config config.json
Configuration Example (config.json)
JSON
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
