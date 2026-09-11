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



# transform_3D_batch.batch_transform_Step_to_3D(processed_CAD_root +  "\step_upright_z_merge",
#                                                processed_CAD_root +  "\stl_upright_z_merge",
#                                                mode=".stl",Fvector=(0,0,0),Frotation= 0)

# transform_3D_batch.batch_transform_Step_to_3D(processed_CAD_root +  "\step_upright_z_components",
#                                                processed_CAD_root +  "\stl_upright_z_components",
#                                                mode=".stl",Fvector=(0,0,0),Frotation= 0)

# transform_3D_batch.batch_transform_Step_to_3D(processed_CAD_root +  "\step_upright_z_parts",
#                                                processed_CAD_root +  "\stl_upright_z_parts",
#                                                mode=".stl",Fvector=(0,0,0),Frotation= 0)
csv_identify_dir = os.path.join(processed_CAD_root, "csv_identify_parts")
transform_3D_batch.batch_rename_and_copy_by_mode(
    csv_identify_dir,
    processed_CAD_root +  r"\stl_upright_z_parts\tree",
    processed_CAD_root +  r"\stl_upright_z_parts_id",mode='.stl'
)