
import time 
import  transform_3D 
import  transform_3D_batch 
import  pc_surface_detection
# transform_3D.transform_moving_step("./report_use/2990001G assembly raw.step",
#                                    "./report_use/2990001G assembly mer.step",
#                                    "./report_use/2990001G assembly raw_cg.step",
#                                    "./report_use/2990001G assenbly mer_cg.step")

# transform_3D.transform_3D(in_path="./report_use/2990001G assenbly mer_cg.step",
#                           out_put="./report_use/2990001G assenbly stl_mer_cg.stl")
# a, f = transform_3D.STL_DATA("./report_use/2990001G assenbly stl_mer_cg.stl").LoadMesh()
# transform_3D.STL_DATA().PlottoMesh(a,f)

# transform_3D.STL_DATA(in_path="./report_use/2990001G assenbly stl_mer_cg.stl",
#                       out_path="./report_use/2990001G assenbly pc_mer_cg.h5").STLtoCloud(number_of_points=2048)
# p = transform_3D.STL_DATA("./report_use//2990001G assenbly pc_mer_cg.h5").LoadCloud()
# transform_3D.STL_DATA().PlottoCloud(p)

# transform_3D.transform_moving_step("./report_use/2990001G assembly raw_cg.step",
#                                    "./report_use/2990001G assenbly mer_cg.step",
#                                    "./report_use/2990001G assembly raw_cg_z.step",
#                                    "./report_use/2990001G assenbly mer_cg_z.step",Fvector=(1,0,0),Frotation=90)

#transform_3D.transform_Step_OCCseg("./report_use/2990001G assembly raw_cg_z.step","./report_use/2990001G assembly raw_cg_z_parts")
#transform_3D.transform_Step_OCCsegre("./report_use/2990001G.step","./report_use/2990001G assembly raw_cg_z_parts/parts","./report_use/2990001G assenbly raw_cg_z_parts_nameout.csv")


# transform_3D_batch.batch_transform_Step_to_3D("./report_use/2990001G assembly raw_cg_z_parts","./report_use/2990001G assembly stl_raw_cg_z_parts")
# transform_3D_batch.batch_transform_Stl_to_cloud("./report_use/2990001G assembly stl_raw_cg_z_parts","./report_use/2990001G assembly pc_raw_cg_z_parts",point_num=4096)
# pc_surface_detection.process_assembly_folder("./report_use/2990001G assembly pc_raw_cg_z_parts","./report_use/2990001G assembly pc_raw_cg_z_parts_det",contact_threshold = 1)
#pc_surface_detection.visualize_tool("./report_use/2990001G assembly pc_raw_cg_z_parts_det")
# pc_surface_detection.visualize_tool("./report_use/2990001G assembly pc_raw_cg_z_parts_det/parts/part_001.h5")
# pc_surface_detection.visualize_tool("./report_use/2990001G assembly pc_raw_cg_z_parts_det/parts/part_002.h5")
# pc_surface_detection.visualize_tool("./report_use/2990001G assembly pc_raw_cg_z_parts_det/parts/part_014.h5")

"""
p = transform_3D.STL_DATA("./report_use/2990001G assembly pc_raw_cg_z_parts/parts/part_014.h5").LoadCloud()
p = transform_3D.STL_DATA().PlottoCloud(p)
"""