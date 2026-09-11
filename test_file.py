
import time 
from transform_3D import STL_DATA , transform_Step_OCC ,transform_Step_OCCseg,transform_Step_OCCsegre,transform_3D,transform_moving_step,CloudtoSkl,MeshtoSkl,Plot_to_stl_Skl,Plot_to_pc_Skl,transform_OCCstl,transform_stlmerge,transform_step_cloud,ParameterExtractor,transform_Cloud_2D
from transform_3D_batch import batch_transform_Step_to_3D ,batch_transform_Stl_to_cloud
from pc_surface_detection import visualize_dataset ,process_assembly_data_gen
import os


transform_moving_step(r"D:\ChynWangProject\data\processed_CAD\step_raw_merge\blank\S4200220.step",r"D:\ChynWangProject\data\processed_CAD\step_raw_component\blank\S4200220.step","te.step","te m.step")
transform_moving_step(r"D:\ChynWangProject\data\processed_CAD\step_raw_merge\tree\6136B011LA-WG230907\6136B011LA assembly.step",r"D:\ChynWangProject\data\processed_CAD\step_raw_component\tree\6136B011LA-WG230907\6136B011LA assembly.step","te.step","te m.step")
"""
stl_data = STL_DATA('./test_file/10712448 assembly2.stl')
# 测量 STLtoVoxel 方法的执行时间
start_time = time.time()
a, b, c = stl_data.STLtoVoxel()
end_time = time.time()
stlto_voxel_time = end_time - start_time
print(f"STLtoVoxel 方法执行时间: {stlto_voxel_time:.4f} 秒")

# 测量 STLtoVoxelCUDA 方法的执行时间
start_time = time.time()
o = stl_data.STLtoCloud()
end_time = time.time()
stlto_voxel_cuda_time = end_time - start_time
print(f"STLtoVoxelCUDA 方法执行时间: {stlto_voxel_cuda_time:.4f} 秒")
"""

"""
# 测量 pl 方法的执行时间
start_time = time.time()
p = Parameter_DATA('10712448 assembly2.step').MaxArea()
end_time = time.time()
pt = end_time - start_time
print(f"STLtoVoxelCUDA 方法执行时间: {pt:.4f} 秒")
"""

"""
p , k = STL_DATA('./test_file/10712448 assembly2.stl').STLtoMesh()
p = np.array(p)
k = np.array(k)
STL_DATA().PlotMesh(p,k)


a,b,c = STL_DATA('./test_file/10712448 assembly2.stl').STLtoVoxel()
a = np.array(a)
b = np.array(b)
c = np.array(c)

STL_DATA().PlottoVoxel(a,b,c)

o = STL_DATA('./test_file/10712448 assembly2.stl').STLtoCloud()
o = np.array(o)
STL_DATA().PlottoCloud(o)
"""
six_views = [[0, 0, 0],    # Front
    [180, 0, 0],    # Back
    [90,  0, 0],    # Left
    [-90, 0, 0],    # Right
    [0,  90, 0],    # Top
    [0, -90, 0]     # Bottom
]
#o = STL_DATA('./test_file/10712448 assembly2.stl',"./test_file/10712448 assembly2").STLtoDeep(six_views,1024,1024,128,[0.2,1024] )

#transform_3D("10730888 assembly.step","10730888 assembly m.stl",Fvector=(0, 0, 0), Frotation=0,Fmoving = (0,0,0), tolerance=0.1, tessellate_value=0.1)
#transform_3D("10730888 assembly.step","10730888 assembly.stl",Fvector=(0,0,1),Frotation=180)
#transform_3D("10730888 assembly m.step","10730888 assembly m.stl",Fvector=(0,0,1),Frotation=180)




#transform_Step_OCC("103-200159 assembly.step","103-200159 assembly m.step")
#transform_Step_OCC("20478805B assembly.step", "20478805B assembly m.step")
"""
transform_Step_OCC("20928901.step","20928901 m.step")
transform_Step_OCC("FX750-38F.step","FX750-38F m.step")
transform_Step_OCC("KT YK04_ST_RL.step","KT YK04_ST_RL m.step")
"""
#transform_Step_OCC("2829401F assembly.STEP","2829401F assembly m.step")
#transform_Step_OCC("2990301A assembly.step","2990301A assembly m.step")

#transform_OCCstl("103-200159 assembly.step","103-200159 assembly.stl")

#transform_stlmerge("103-200159 assembly.stl", "103-200159 assembly m.stl")







#transform_moving_step("103-200159 assembly.step","103-200159 assembly m.step","103-200159 assemblyk.step","103-200159 assemblyk m.step",mode="step")


#transform_Step_OCCseg("./103-200159 assembly.step","103-200159 assembly test")
#transform_Step_OCCsegre("103-200159.step","./103-200159 assembly test/parts","103-200159 assembly testreout.csv")






#transform_Step_OCCseg("./test_CAD/103-200159 assembly.step","103-200159 assembly test")
#transform_Step_OCCsegre("103-200159 assembly testre","./103-200159 assembly test/parts","103-200159 assembly testreout")

#transform_Step_OCCseg("./test_CAD/2990001G assembly.step","2990001G assembly test")
#transform_Step_OCCsegre("2990001G assembly testre","./2990001G assembly test/parts","2990001G assembly testreout")


#transform_Step_OCCseg("./test_CAD/10717751 assembly.step","10717751 assembly test")
#transform_Step_OCCsegre(r"./10717751 assembly testre/10717751.step",r"./10717751 assembly test/parts","10717751 assembly testreout")

#print(transform_Step_OCC("./test_file/10712448 assembly2.step","20446701D assembly m.step"))
#transform_moving_step("10730888 assembly.step","10730888 assembly m.step","10730888 assembly test.step","10730888 assenbly m test.step")

"""
transform_moving_step("38489B assembly raw.step","38489B assembly mer.step","38489B assembly raw test.step","38489B assembly mer test.step")

transform_moving_step("38489B assembly raw test.step","38489B assembly mer test.step","38489B assembly raw testr.step","38489B assembly mer testr.step",Fvector=(1,0,0),Frotation=-90)

transform_3D("38489B assembly mer testr.step","38489B assembly2.stl",Fvector=(0,0,0),Frotation=0)
a , c = STL_DATA("38489B assembly2.stl").LoadMesh()
STL_DATA().PlottoMesh(a,c)
"""
#STL_DATA("./38489B assembly2.stl","./38489B assembly2 clo.h5").STLtoCloud(number_of_points=2048)

#CloudtoSkl("38489B assembly2 clo.h5","./38489B assembly2 clo/")
#a , c = STL_DATA("10712448 assembly.stl").STLtoMesh()
#s, n , k  = STL_DATA("10712448 assembly.stl").STLtoVoxel()
#print(a,c)
#STL_DATA().PlotMesh(a,c)
#STL_DATA().PlottoVoxel(s,n,k)

"""
o = STL_DATA("103-200159_aug_000.h5").LoadCloud(datasetname = 'data')
STL_DATA().PlottoCloud(o)

a , c = STL_DATA("103-200159 assembly.stl").LoadMesh()
STL_DATA().PlottoMesh(a,c)
"""
    # 检查返回码
"""
transform_3D("60710B assembly.step","60710B assembly.stl",Fvector=(0,0,0),Frotation=0)
a , c = STL_DATA("60710B assembly.stl").LoadMesh()
STL_DATA().PlottoMesh(a,c)
"""
"""
transform_3D("60710B assembly.step","60710B assembly2.stl",Fvector=(1,0,0),Frotation=-90)
a , c = STL_DATA("60710B assembly2.stl").LoadMesh()
STL_DATA().PlottoMesh(a,c)
"""

#transform_3D("60710B assembly.step","60710B assembly2.step",Fvector=(0,1,0),Frotation=45)
#batch_transform_Step_to_3D("2990001G assembly test","2990001G assembly test stl")
#batch_transform_Stl_to_cloud("test_file2/2990001G assembly test stl","test_file2/2990001G assembly test pc",point_num=100000)


# process_assembly_data_gen("test_file2/2990001G assembly test pc","test_file2/2990001G assembly test pcdet",contact_threshold = 2,label_mode="binary")
# transform_step_cloud("./test_file2/2990001G assembly test/parts/part_014.step","./test_file2/2990001G assembly test pcdet/parts/part_014.npz","test.step","test_binary.npz")
# visualize_dataset("test_binary.npz")

# process_assembly_data_gen("test_file2/2990001G assembly test pc","test_file2/2990001G assembly test pcdet",contact_threshold = 2,label_mode='signed_decay')
# transform_step_cloud("./test_file2/2990001G assembly test/parts/part_014.step","./test_file2/2990001G assembly test pcdet/parts/part_014.npz","test.step","test_signed_decay.npz")
# visualize_dataset("test_signed_decay.npz")


# process_assembly_data_gen("test_file2/2990001G assembly test pc","test_file2/2990001G assembly test pcdet",contact_threshold = 2,label_mode="global_gaussian")
# transform_step_cloud("./test_file2/2990001G assembly test/parts/part_014.step","./test_file2/2990001G assembly test pcdet/parts/part_014.npz","test.step","test_global_gaussian.npz")
# visualize_dataset("test_global_gaussian.npz")



"""
process_assembly_data_gen("test_file2/2990001G assembly test pc","test_file2/2990001G assembly test pcdet",contact_threshold = 2,label_mode="controlled_gaussian")
transform_step_cloud("./test_file2/2990001G assembly test/parts/part_014.step","./test_file2/2990001G assembly test pcdet/parts/part_014.npz","test.step","test_controlled_gaussian.npz")
visualize_dataset("test_controlled_gaussian.npz")
"""







#STL_DATA("10712448 assembly.stl","38489B assembly2 clo").STLtoMesh()

#CloudtoSkl("38489B assembly2 clo.h5","38489B assembly2 pcskl",down_sample=0.01)



"""

MeshtoSkl("38489B assembly2.stl","38489B assembly2 meshskl",contrast_factor=0.1,auto_simplify=False)
Plot_to_stl_Skl("38489B assembly2.stl","./38489B assembly2 meshskl/skeleton.swc")
"""
"""
STL_DATA("./38489B assembly2.stl","./38489B assembly2 noclo.h5").STLtoNormalCloud(number_of_points=131072)

#a  = STL_DATA("./38489B assembly2 noclo.h5").LoadNormalCloud()
#STL_DATA().PlottoNormalCloud(a)

CloudtoSkl("38489B assembly2 noclo.h5","38489B assembly2 pcskl",down_sample=0.01)
Plot_to_pc_Skl(orig_path="38489B assembly2 noclo.h5",skel_path="38489B assembly2 pcskl/skeleton.pcd",topo_path="38489B assembly2 pcskl/topology.ply")
"""


# STL_DATA("./38489B assembly2.stl","./38489B assembly2 noclo.h5").STLtoCloud(number_of_points=2048,mode='surface_uniform')

# a  = STL_DATA("./38489B assembly2 noclo.h5").LoadCloud()


six_views_45 = [[45, 0, 0],    # Front
    [225, 0, 0],    # Back
    [135,  0, 0],    # Left
    [-45, 0, 0],    # Right
    [45,  90, 0],    # Top
    [45, -90, 0]     # Bottom
]
STL_DATA(r"D:\ChynWangProject\data\processed_CAD\normalcloud_upright_z\normalcloud_upright_z_parts_random_binary_binary_2048\tree\A3-5161I12-DEV250401\A3-5161I12 assembly\parts\part_002.h5",r".\A3-5161I12").Cloudto2D(six_views_45,1024,1024,100,10)
# STL_DATA("./38489B assembly2.stl","./38489B assembly2 noclo.h5").STLtoNormalCloud(number_of_points=2048,mode='fps')

# a  = STL_DATA("./38489B assembly2 noclo.h5").LoadNormalCloud()
# STL_DATA().PlottoNormalCloud(a)

#print(ParameterExtractor(r"D:\ChynWangProject\data\processed_CAD\parameter_upright_z_merge_identify\tree\89S3-A1-08-S240717\89S3-A1-08 assembly.h5"))
