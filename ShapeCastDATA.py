from transform_3D import transform_3D,Parameter_DATA , STL_DATA
import os
import pandas as pd
pd.set_option('display.max_colwidth', 100000000)
import numpy as np
from SySPath import find_folder_in_program_files ,FreeCADexe ,ChynWangPojectpy
from FreeCAD_venv import FreeCADvenvCreate
import ast
import concurrent.futures
import json
import re
from transform_3D import STL_DATA
from transform_Depth_2D  import STL_Depth

# Convert strings to dictionaries
root_path = ChynWangPojectpy()
def process_shape_data(file_path):
    return Parameter_DATA(file_path)
def process_stl_data(stl_out_put):
    vertices_array, faces_array = STL_DATA(stl_out_put).STLtoMesh()
    voxel_array, voxel_min_bound, voxel_size = STL_DATA(stl_out_put).STLtoVoxel()
    cloud_coords = STL_DATA(stl_out_put).STLtoCloud()
    return np.array(vertices_array), np.array(faces_array), np.array(voxel_array), np.array(voxel_min_bound), np.array(voxel_size), np.array(cloud_coords)
def PdReadShape(file_path):
    directory = os.path.dirname(file_path)

    filename_with_extension = os.path.basename(file_path)
    filename_without_extension = os.path.splitext(filename_with_extension)[0]
    stl_filename = '{}.stl'.format(filename_without_extension)
    stl_out_put = directory + '/' +  stl_filename
    if os.path.exists(file_path):
        transform_3D(file_path,stl_out_put)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_shape_data = executor.submit(process_shape_data, file_path)
            future_stl_data = executor.submit(process_stl_data, stl_out_put)
            #print(future_shape_data.result())
            #print(future_stl_data.result())
            ShapeDATA = future_shape_data.result()
            VerticesArray, FacesArray ,VoxelArray, VoxelMinBound, VoxelSize ,CloudCoords= future_stl_data.result()
        np.set_printoptions(threshold=np.inf)
        CenterMass = np.array(list(ShapeDATA.CenterOfMass().values()))
        matrixofinertia = ShapeDATA.MatrixOfInertia()
        Inertia = np.array([
            [matrixofinertia['Ixx'], matrixofinertia['Ixy'], matrixofinertia['Ixz']],
            [matrixofinertia['Iyx'], matrixofinertia['Iyy'], matrixofinertia['Iyz']],
            [matrixofinertia['Izx'], matrixofinertia['Izy'], matrixofinertia['Izz']]
        ])
        #print(Inertia.shape)
        """CenterMass MatrixOfInertia	MaxArea	VerticesArray	FaceArra	VoxelArray	VoxelMinBound	VoxelSize	CloudCoords"""
        parameter_filename = '{}_parameter.h5'.format(filename_without_extension)
        mesh_filename = '{}_mesh.h5'.format(filename_without_extension)
        voxel_filename = '{}_voxel.h5'.format(filename_without_extension)
        cloud_filename = '{}_cloud.h5'.format(filename_without_extension)

        parameter_data = {
            'Product_Version': filename_without_extension,
            'Volume': ShapeDATA.Volume(),
            'Area': ShapeDATA.Area(),
            'CenterOfMass': CenterMass,
            'BoundBox_XMin': ShapeDATA.BoundBox()['XMin'],
            'BoundBox_XMax': ShapeDATA.BoundBox()['XMax'],
            'BoundBox_X':(ShapeDATA.BoundBox()['XMax'] -  ShapeDATA.BoundBox()['XMin']),
            'BoundBox_YMin': ShapeDATA.BoundBox()['YMin'],
            'BoundBox_YMax': ShapeDATA.BoundBox()['YMax'],
            'BoundBox_Y': (ShapeDATA.BoundBox()['YMax'] - ShapeDATA.BoundBox()['YMin']),
            'BoundBox_ZMin': ShapeDATA.BoundBox()['ZMin'],
            'BoundBox_ZMax': ShapeDATA.BoundBox()['ZMax'],
            'BoundBox_Z': (ShapeDATA.BoundBox()['ZMax'] - ShapeDATA.BoundBox()['ZMin']),
            'EdgesNumber': ShapeDATA.EdgesNumber(),
            'FaceNumber': ShapeDATA.FaceNumber(),
            'VertexesNumber': ShapeDATA.VertexesNumber(),
            'MatrixOfInertia': Inertia,
            'XYMaxArea': ShapeDATA.MaxArea()['XYMaxArea'],
            'XZMaxArea': ShapeDATA.MaxArea()['XZMaxArea'],
            'YZMaxArea': ShapeDATA.MaxArea()['YZMaxArea'],

        }
        mesh_data = {
            'Product_Version': filename_without_extension,
            'VerticesArray': VerticesArray,
            'FaceArray': FacesArray,
        }
        voxel_data = {
            'Product_Version': filename_without_extension,
            'VoxelArray': VoxelArray,
            'VoxelMinBound': VoxelMinBound,
            'VoxelSize': VoxelSize,
        }
        cloud_data = {
            'Product_Version':filename_without_extension,
            'CloudCoords': CloudCoords,
        }
        # 提取字典的值
        parameter_out_put = directory + '/' + parameter_filename
        mesh_out_put = directory + '/' + mesh_filename
        voxel_out_put = directory + '/' + voxel_filename
        cloud_out_put = directory + '/' + cloud_filename
        pd.DataFrame([parameter_data]).to_hdf(parameter_out_put, key='df', mode='w',index=False)
        pd.DataFrame([mesh_data]).to_hdf(mesh_out_put, key='df', mode='w', index=False)
        pd.DataFrame([voxel_data]).to_hdf(voxel_out_put, key='df', mode='w', index=False)
        pd.DataFrame([cloud_data]).to_hdf(cloud_out_put, key='df', mode='w', index=False)

        depth_filename = '{}_cloud.h5'.format(filename_without_extension)
        return pd.DataFrame([parameter_data])
        #print(ShapeDATA.MatrixOfInertia())
    else:
        data = {
            'Product_Version': filename_without_extension,
            'Volume': None,
            'Area': None,
            'CenterOfMass': None,
            'BoundBox': None,
            'EdgesNumber': None,
            'FaceNumber': None,
            'VertexesNumber': None,
            'MatrixOfInertia': None,
            'MaxArea': None,
            'VerticesArray': None,
            'FaceArray': None,
            'VoxelArray': None,
            'VoxelMinBound':None,
            'VoxelSize': None,
            'CloudCoords': None,
        }
        return pd.DataFrame([data])



def CastingShape():
    df1 = PdReadShape("D:\ChynWangProject\python_scripts/test_file/10712448 assembly.STEP")
    df2 = PdReadShape("D:\ChynWangProject\python_scripts/test_file/10712448 assembly2.STEP")
    dfresult = pd.concat([df1, df2], ignore_index=True)

    print(dfresult)
    dfresult.to_hdf('CastShape.h5', key='df', mode='w',index=False)
    dfresult.to_csv('CastShape.csv',index=False)

    #Openall
    #test hdf5

    #STL_DATA().PlotMesh()
def setData():
    df = pd.read_csv("AllDataNo3D.csv")


    df['Product_Version'] = df['Product_Version'].astype(str)

    # 找到主版本和子版本
    main_versions = df[~df['Product_Version'].str.contains('-')]
    sub_versions = df[df['Product_Version'].str.contains('-')]

    # 複製主版本的特定欄位資料到子版本
    for idx, sub_row in sub_versions.iterrows():
        sub_version = sub_row['Product_Version']
        main_version = sub_version.split('-')[0]  # 假設子版本是主版本的前綴

        # 找到對應的主版本
        if main_version in main_versions['Product_Version'].values:
            main_row = main_versions[main_versions['Product_Version'] == main_version].iloc[0]

            # 複製主版本中的資料到子版本
            for column in ['Volume', 'Area', 'CenterOfMass','FaceNumber', 'BoundBox','EdgesNumber','VertexesNumber','MatrixOfInertia','MaxArea','Path',]:
                df.loc[idx, column] = main_row[column]

    df = df.drop_duplicates(subset=['Product_Version'])




    # 显示结果
    df.to_csv("test.csv",index=False)
    df.to_excel("test.xlsx",index=False)


#CastingShape()
#setData()
#CastingShape()
"""
Mesh_h5 = pd.read_hdf('10712448 assembly2_mesh.h5', key='df')
Voxel_h5 = pd.read_hdf('10712448 assembly2_voxel.h5', key='df')
Point_h5 = pd.read_hdf('10712448 assembly2_cloud.h5', key='df')

STL_DATA().PlotMesh(np.vstack(Mesh_h5['VerticesArray'].values),np.vstack(Mesh_h5['FaceArray'].values))
STL_DATA().PlottoCloud(np.vstack(Point_h5['CloudCoords'].values))

print(np.vstack(Voxel_h5 ['VoxelArray'].values))
print(np.vstack(Voxel_h5['VoxelMinBound'].values)[0])
print(np.vstack(Voxel_h5['VoxelSize'].values)[0][0])

STL_DATA().PlottoVoxel(np.vstack(Voxel_h5 ['VoxelArray'].values),np.vstack(Voxel_h5['VoxelMinBound'].values)[0],np.vstack(Voxel_h5['VoxelSize'].values)[0][0])


def read_npz(file_path):
    # Load the .npz file with allow_pickle=True
    data = np.load(file_path, allow_pickle=True)
    print("Available keys:", data.files)
    loaded_columns_dict = {key: data[key] for key in data.files}
    return data
"""


""""def PdReadShape3D(file_path):
    directory = os.path.dirname(file_path)
    filename_with_extension = os.path.basename(file_path)
    filename_without_extension = os.path.splitext(filename_with_extension)[0]
    stl_filename = '{}.stl'.format(filename_without_extension)
    stl_out_put = directory + '/' +  stl_filename
    if os.path.exists(file_path):
        transform_3D(file_path,stl_out_put)
        ShapeDATA = Parameter_DATA(file_path)
        VerticesArray, FacesArray = STL_DATA(stl_out_put).STLtoMesh()
        VoxelArray, VoxelMinBound, VoxelSize = STL_DATA(stl_out_put).STLtoVoxel()
        CloudCoords = STL_DATA(stl_out_put).STLtoCloud()
        Inertia = np.array(list(ShapeDATA.MatrixOfInertia().values())).reshape(3,3)
        CenterMass  =  list(ShapeDATA.CenterOfMass().values())
        np.set_printoptions(threshold=np.inf)
        #print(VoxelArray)
        #print(Inertia)
        data = {
            'Product_Version':filename_without_extension,
            'Volume':ShapeDATA.Volume(),
            'Area':ShapeDATA.Area(),
            'CenterOfMass':CenterMass,
            'BoundBox':ShapeDATA.BoundBox(),
            'EdgesNumber':ShapeDATA.EdgesNumber(),
            'FaceNumber':ShapeDATA.FaceNumber(),
            'VertexesNumber':ShapeDATA.VertexesNumber(),
            'MatrixOfInertia': Inertia,
            'MaxArea': ShapeDATA.MaxArea(),
            'VerticesArray':VerticesArray,
            'FaceArra':FacesArray,
            'VoxelArray':VoxelArray,
            'VoxelMinBound':VoxelMinBound,
            'VoxelSize':VoxelSize,
            'CloudCoords':CloudCoords,

        }
        # 提取字典的值
        #print(ShapeDATA.MatrixOfInertia())
        a = pd.DataFrame([data])
        return a
    else:
        data = {
            'Product_Version': filename_without_extension,
            'Volume': None,
            'Area': None,
            'CenterOfMass': None,
            'BoundBox': None,
            'EdgesNumber': None,
            'FaceNumber': None,
            'VertexesNumber': None,
            'MatrixOfInertia': None,
            'MaxArea': None,
            'VerticesArray': None,
            'FaceArra': None,
            'VoxelArray': None,
            'VoxelMinBound':None,
            'VoxelSize': None,
            'CloudCoords': None,
        }
        a = pd.DataFrame([data])
        return a"""
"""
df = pd.read_hdf('CastShape.h5', key='df')
print(type(df['MatrixOfInertia']))
print(type(df['MatrixOfInertia'].values))
"""
#print(df['CloudCoords'].values)