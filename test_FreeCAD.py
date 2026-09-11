import sys
import os
sys.path.append('C:/Program Files/FreeCAD 0.21/bin')
import FreeCAD
import Mesh
import Import
import Part
import pandas as pd
import numpy as np
import io
class transform_FreeCAD:
    def __init__(self, in_path,out_path = "out_path", mode ='stl'):
        self.in_path = in_path
        self.out_path  = out_path
        self.ex_in = os.path.splitext(in_path)[1].lower()
        self.mode = '.' + mode
    def transfromFreeCAD(self):
        print(self.mode)
        if self.mode == '.stl':
            if self.ex_in == '.step' or self.ex_in == '.stp' or self.ex_in == '.igs':
                #讀取step文件
                Import.open(self.in_path)  # 使用 Import.open() 方法打開 STEP 文件
                doc = FreeCAD.ActiveDocument  # 獲取當前文檔
                # 假设 STEP 文件中只有一个对象，获取第一个对象
                part = doc.Objects[0]
                # 保存为 STL 文件
                __objs__ = [part]
                Part.export(__objs__, "{}{}".format(self.out_path,self.mode))
                print(part)

                # 关闭文档
                FreeCAD.closeDocument(doc.Name)
        elif self.mode == ".step" or self.mode == '.stp' or self.mode == '.igs':
            if self.ex_in == '.stl':
                mesh = Mesh.Mesh(self.in_path)
                reduction_ratio = 0.9
                tolerance = 0.1
                mesh.decimate(tolerance, reduction_ratio)
                # 将 Mesh 转换为 Shape
                shape = Part.Shape()

                shape.makeShapeFromMesh(mesh.Topology, 0.01)  # 0.1 表示容差

                # 将 Shape 转换为 Solid
                solid = Part.makeSolid(shape)

                # 创建一个新的文档
                doc = FreeCAD.newDocument("STL_to_STEP_Conversion")

                # 将 Solid 添加到文档中
                part_obj = doc.addObject("Part::Feature", "ConvertedSolid")
                part_obj.Shape = solid

                # 保存为 STEP 文件
                Part.export([part_obj], "{}{}".format(self.out_path,self.mode))

                # 完成后关闭文档
                FreeCAD.closeDocument(doc.Name)
        else:
            print("file type not supported")


def convert_file_encoding(input_file_path, output_file_path, from_encoding='cp950', to_encoding='utf-8'):
    try:
        # 读取文件内容
        with open(input_file_path, 'r', encoding=from_encoding) as file:
            content = file.read()

        # 将内容写入新文件，使用目标编码
        with open(output_file_path, 'w', encoding=to_encoding) as file:
            file.write(content)

        print(f"File converted from {from_encoding} to {to_encoding} successfully.")

    except UnicodeDecodeError as e:
        print(f"Error decoding file: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")


def shape_to_dataframe(step_file_path):
    doc = FreeCAD.newDocument()
    shape = Part.Shape()
    shape.read(step_file_path)

    vertices_data = []
    edges_data = []

    # 遍历形状中的所有子形状
    for i, sub_shape in enumerate(shape.SubShapes):
        for j, vertex in enumerate(sub_shape.Vertexes):
            point = vertex.Point
            vertices_data.append({'SubShape': i + 1, 'Vertex': j + 1, 'x': point.x, 'y': point.y, 'z': point.z})

        for j, edge in enumerate(sub_shape.Edges):
            start_point = edge.Vertexes[0].Point
            end_point = edge.Vertexes[1].Point
            edges_data.append({'SubShape': i + 1, 'Edge': j + 1, 'Start_x': start_point.x, 'Start_y': start_point.y,
                               'Start_z': start_point.z,
                               'End_x': end_point.x, 'End_y': end_point.y, 'End_z': end_point.z,
                               'Curve_Type': type(edge.Curve).__name__ if edge.Curve else None})

    # 保存文档以确保资源释放
    FreeCAD.closeDocument(doc.Name)

    vertices_df = pd.DataFrame(vertices_data)
    edges_df = pd.DataFrame(edges_data)

    return vertices_df, edges_df


def dataframe_to_shape(vertices_df, edges_df, output_step_file_path):
    doc = FreeCAD.newDocument()

    edges = []

    # Create edges from dataframe
    for _, row in edges_df.iterrows():
        start_point = FreeCAD.Vector(row['Start_x'], row['Start_y'], row['Start_z'])
        end_point = FreeCAD.Vector(row['End_x'], row['End_y'], row['End_z'])
        edge = Part.Edge(Part.LineSegment(start_point, end_point))
        edges.append(edge)

    # Check if edges form closed wires or multiple wires
    wires = []
    while edges:
        wire_edges = [edges.pop(0)]
        i = 0
        while i < len(edges):
            for edge in wire_edges:
                if edges[i].Vertexes[0].Point.isEqual(edge.Vertexes[0].Point, 1e-7) or edges[i].Vertexes[
                    0].Point.isEqual(edge.Vertexes[1].Point, 1e-7) or \
                        edges[i].Vertexes[1].Point.isEqual(edge.Vertexes[0].Point, 1e-7) or edges[i].Vertexes[
                    1].Point.isEqual(edge.Vertexes[1].Point, 1e-7):
                    wire_edges.append(edges.pop(i))
                    break
            else:
                i += 1
        wires.append(Part.Wire(wire_edges))

    # Create a compound from the wires
    compound = Part.Compound(wires)

    # Save the shape to a new STEP file
    compound.exportStep(output_step_file_path)

    # 保存文档以确保资源释放
    FreeCAD.closeDocument(doc.Name)





def main(in_path,out_path = "out_path",mode = "stl"):
    # 这里是你的主要逻辑
    #mesh = FreeCAD.Mesh.Mesh('3Dtest.stl')
    #polt_3D_mesh(mesh)
    a = transform_FreeCAD(in_path,out_path,mode=mode)
    v , e = shape_to_dataframe(in_path)
    dataframe_to_shape(v,e,out_path)

    print(v)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python transform_FreeCAD.py <in_path> [mode]")
    else:
        in_path = sys.argv[1]
        out_path = sys.argv[2] if len(sys.argv) > 2 else "out_path"
        mode = sys.argv[3] if len(sys.argv) > 3 else "stl"
        #print(in_path,out_path,mode)
        main(in_path,out_path,mode)



