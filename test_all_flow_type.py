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
six_views_45 = [[45, 0, 0],    # Front
     [225, 0, 0],    # Back
     [135,  0, 0],    # Left
     [-45, 0, 0],    # Right
     [45,  90, 0],    # Top
     [45, -90, 0]     # Bottom
 ]
transform_3D_batch.batch_transform_STEP_to_2D("D:\ChynWangData\D模頭",
                                               "D:\ChynWangData\D模頭_2D",
                                               camera_angles_list= six_views_45)