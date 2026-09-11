import subprocess
import os
from OCC_venv import OCCHybridEnvCreate
from FreeCAD_venv import FreeCADvenvCreate
from PcSkeletor_env import PcSkeletorEnvCreate
from stlmerge_env import pyvistaEnvCreate
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import json
import open3d as o3d
import numpy as np
from SySPath import FreeCADexe

from pathlib import Path
#import torch
import pandas as pd
import h5py
import transform_Depth_2D
import transform_Cloud_2D
import transform_Cloud_STL_2D
import sys
import tempfile
import shutil
import stltovoxel
import transform_meshcskeletor

from transform_Cloud_STL_2D import Render_Hybrid_Cloud_STL
from transform_Cloud_STL_2D_light import Render_Hybrid_Cloud_STL_li
root_path = Path(__file__).parent.resolve()
print(f"腳本確定的根目錄 (Project Root): {root_path}") # 加上這行方便你除錯
# 检查是否找到 FreeCAD 目录
SCRIPT_PATH_transform_FreeCAD = r"{}\transform_FreeCAD.py".format(root_path)
SCRIPT_PATH_Parameter_FreeCAD = r"{}\Parameter_FreeCAD.py".format(root_path)
SCRIPT_PATH_PointCloud_FreeCAD = r"{}\PointCloud_FreeCAD.py".format(root_path)
SCRIPT_PATH_transform_OCC = r"{}\transform_OCC.py".format(root_path)
SCRIPT_PATH_transform_OCCseg = r"{}\transform_OCCseg.py".format(root_path)
SCRIPT_PATH_transform_OCCstl = r"{}\transform_OCCstl.py".format(root_path)
SCRIPT_PATH_test_FreeCAD = r"{}\test_FreeCAD.py".format(root_path)
SCRIPT_PATH_transform_moving = r"{}\transform_moving.py".format(root_path)
SCRIPT_PATH_transform_step_cloud = r"{}\transform_moving_pointcloud.py".format(root_path)
SCRIPT_PATH_transform_OCCsegre = r"{}\transform_OCCsegre.py".format(root_path)
SCRIPT_PATH_pcskeletor = r"{}\transform_pcskeletor.py".format(root_path)
SCRIPT_PATH_pcskeletor_visualize = r"{}\transform_pcskeletor_visualize.py".format(root_path)
SCRIPT_PATH_transform_stlmerge = r"{}\transform_stlmerge.py".format(root_path)
SCRIPT_PATH_transform_Step_2D = r"{}\transform_Step_2D.py".format(root_path)
# FreeCAD 相關路徑
VENV_PATH_FREECAD = root_path / "FreeCADvenv"

# 【關鍵修改】定義 OCC 虛擬環境在根目錄的路徑
VENV_PATH_OCC = root_path / "OCC_venv"

VENV_PATH_PCSKL = root_path / "PcSkeletor_venv"
VENV_PATH_pyvista  = root_path / "pyvista_venv"
# 检查路径是否存在
def check_path(path):
    if os.path.isfile(path):
        print(f"文件 {path} 存在。")
    else:
        print(f"文件 {path} 不存在。")

# 這個函式現在專門用於 FreeCAD 環境的建立
def check_and_setup_freecad_venv(path):
    if os.path.isdir(path):
        print(f"目錄 {path} 存在。")
    else:
        print(f"目錄 {path} 不存在，開始建立 FreeCAD 環境...")
        try:
            # --- 以下是您原有的 FreeCAD 環境建立邏輯 ---
            from SySPath import FreeCADexe
            FreeCADparent = os.path.dirname(FreeCADexe())
            # 確保 FreeCADvenvCreate 的呼叫方式是正確的
            freecad_creator = FreeCADvenvCreate(FREECAD_BASE_PATH=FreeCADparent, VENV_PATH=str(path),PREFERRED_VERSION_STR = "1.0")
            #freecad_creator.create() # 假設有一個 create() 方法
            print("FreeCAD 環境建立完成。")
        except Exception as e:
            print(f"建立 FreeCAD 環境時發生錯誤: {e}")
            sys.exit(1)

# --- 【新函式】用於設定 OCC 環境 ---
def setup_occ_environment_and_get_python(venv_path):
    """
    在指定的 venv_path 檢查、建立 OCC Conda 虛擬環境，並返回 python 解譯器路徑。
    此版本與使用 --prefix 的 VenvCreate 類別相容。
    
    Args:
        venv_path (Path or str): Conda 虛擬環境的目標路徑。
    """
    print(f"--- 正在設定 OCC  環境於 '{venv_path}' ---")
    try:
        # 步驟 1: 初始化時就必須傳入路徑，建立操作物件
        occ_creator = OCCHybridEnvCreate(venv_path=venv_path)
        
        # 步驟 2: 呼叫 setup()。這個方法內部會自己處理 "是否存在" 的檢查，
        # 如果不存在才會建立，存在就會跳過，所以外層不需要再寫 if/else。
        occ_creator.setup()
        
        # 步驟 3: 從物件直接獲取 python 執行檔路徑 (不需要再傳參數)
        python_path = occ_creator.get_python_executable()
        
        print(f"--- OCC 環境設定完成 ---")
        return python_path

    except (RuntimeError, FileNotFoundError) as e:
        print(f"設定 OCC 環境時發生嚴重錯誤: {e}")
        sys.exit(1)
    except Exception as e:
        # 捕獲其他潛在的錯誤
        print(f"發生未知錯誤: {e}")
        sys.exit(1)

def check_and_setup_skeletor_venv(path):
    """
    檢查 PcSkeletor 環境是否存在，如果不存在則建立它。
    """
    # 將路徑轉換為絕對路徑
    venv_path = str(Path(path).resolve())
    
    if os.path.isdir(venv_path):
        print(f"目錄 {venv_path} 存在。")
        # 也可以在這裡加入邏輯，檢查套件是否都已安裝
        # ...
    else:
        print(f"目錄 {venv_path} 不存在，開始建立 PcSkeletor 環境...")
        try:
            # --- 以下是 PcSkeletor 的環境建立邏輯 ---
            
            # 1. 實例化管理器，傳入目標路徑
            skeletor_creator = PcSkeletorEnvCreate(venv_path=venv_path)
            
            # 2. 執行 create() 方法
            skeletor_creator.create()
            
            print("PcSkeletor 環境建立完成。")
            
        except Exception as e:
            print(f"建立 PcSkeletor 環境時發生錯誤: {e}")
            # 如果建立失敗，可能需要清理不完整的環境目錄
            # import shutil
            # if os.path.isdir(venv_path):
            #     print(f"正在清理失敗的環境目錄: {venv_path}")
            #     shutil.rmtree(venv_path)
            sys.exit(1)
def setup_skeletor_environment_and_get_python(venv_path):
    """
    在指定的 venv_path 檢查、建立 OCC Conda 虛擬環境，並返回 python 解譯器路徑。
    此版本與使用 --prefix 的 VenvCreate 類別相容。
    
    Args:
        venv_path (Path or str): Conda 虛擬環境的目標路徑。
    """
    print(f"--- 正在設定 pcskl  環境於 '{venv_path}' ---")
    try:
        # 步驟 1: 初始化時就必須傳入路徑，建立操作物件
        pcskl_creator =  PcSkeletorEnvCreate(venv_path=venv_path)
        
        # 步驟 2: 呼叫 setup()。這個方法內部會自己處理 "是否存在" 的檢查，
        # 如果不存在才會建立，存在就會跳過，所以外層不需要再寫 if/else。
        #pcskl_creator.setup()
        
        # 步驟 3: 從物件直接獲取 python 執行檔路徑 (不需要再傳參數)
        python_path = pcskl_creator.get_python_executable()
        
        print(f"--- PcSkeletor 環境設定完成 ---")
        return python_path

    except (RuntimeError, FileNotFoundError) as e:
        print(f"設定 PcSkeletor 環境時發生嚴重錯誤: {e}")
        sys.exit(1)
    except Exception as e:
        # 捕獲其他潛在的錯誤
        print(f"發生未知錯誤: {e}")
        sys.exit(1)
def check_and_setup_pyvista_venv(path):
    """
    檢查 pyvista3D 環境是否存在，如果不存在則建立它。
    """
    # 將路徑轉換為絕對路徑
    venv_path = str(Path(path).resolve())
    
    if os.path.isdir(venv_path):
        print(f"目錄 {venv_path} 存在。")
        # 如果需要更嚴謹，可以在這裡檢查 python.exe 是否真的存在
    else:
        print(f"目錄 {venv_path} 不存在，開始建立 pyvista3D 環境...")
        try:
            # --- pyvista3D 的環境建立邏輯 ---
            
            # 1. 實例化管理器，傳入目標路徑
            pyvista_creator = pyvistaEnvCreate(venv_path=venv_path)
            
            # 2. 執行 create() 方法
            pyvista_creator.create()
            
            print("pyvista3D 環境建立完成。")
            
        except Exception as e:
            print(f"建立 pyvista3D 環境時發生錯誤: {e}")
            sys.exit(1)
def setup_pyvista_environment_and_get_python(venv_path):
    """
    在指定的 venv_path 檢查、建立 pyvista3D Conda 虛擬環境，並返回 python 解譯器路徑。
    
    Args:
        venv_path (Path or str): Conda 虛擬環境的目標路徑。
    """
    print(f"--- 正在設定 pyvista3D 環境於 '{venv_path}' ---")
    try:
        # 步驟 1: 初始化，建立操作物件
        pyvista_creator = pyvistaEnvCreate(venv_path=venv_path)
        
        # 步驟 2: 執行 create()
        # 注意：pyvistaEnvCreate.create() 內部已經包含了 "檢查是否存在" 的邏輯
        # 如果環境已存在，它會跳過 Conda 建立步驟，僅確保 pip 套件安裝正確
        pyvista_creator.create()
        
        # 步驟 3: 從物件直接獲取 python 執行檔路徑
        python_path = pyvista_creator.get_python_executable()
        
        print(f"--- pyvista3D 環境設定完成 ---")
        return python_path

    except (RuntimeError, FileNotFoundError) as e:
        print(f"設定 pyvista3D 環境時發生嚴重錯誤: {e}")
        sys.exit(1)
    except Exception as e:
        # 捕獲其他潛在的錯誤
        print(f"發生未知錯誤: {e}")
        sys.exit(1)
# 1. 設定 FreeCAD 環境
print("--- 檢查 FreeCAD 環境 ---")
check_and_setup_freecad_venv(VENV_PATH_FREECAD)
freecad_python_exe = os.path.join(VENV_PATH_FREECAD, "Scripts", "python.exe")
print(f"FreeCAD Python 解譯器路徑: {freecad_python_exe}\n")
# 2. 設定 OCC 環境
print("--- 檢查 OCC 環境 ---")
# 【關鍵修改】將路徑 VENV_PATH_OCC 作為參數傳入函式
occ_python_exe = setup_occ_environment_and_get_python(VENV_PATH_OCC)


# --- 輸出結果 ---
print(f"\n主腳本成功獲取 OCC Python 路徑: {occ_python_exe}")
# 3. 檢查腳本路徑
print("--- 檢查  PcSkeletor 環境 ---")
check_and_setup_skeletor_venv(VENV_PATH_PCSKL)
pcskeletor_python_exe = setup_skeletor_environment_and_get_python(VENV_PATH_PCSKL)
print(f"pcskeletor Python 解譯器路徑: {VENV_PATH_PCSKL}\n")

print("--- 檢查  pyvista 環境 ---") 
# 1. 檢查並建立環境
check_and_setup_pyvista_venv(VENV_PATH_pyvista)

# 2. 獲取 Python 執行檔路徑
pyvista_python_exe = setup_pyvista_environment_and_get_python(VENV_PATH_pyvista)

# 3. 印出結果 (這裡修正為印出 python_exe 變數，而非資料夾路徑，這樣才符合「解譯器路徑」的描述)
print(f"pyvista3D Python 解譯器路徑: {pyvista_python_exe}\n")
print("--- 檢查腳本檔案 ---")
check_path(SCRIPT_PATH_transform_FreeCAD)
check_path(SCRIPT_PATH_transform_OCC)
check_path(SCRIPT_PATH_transform_FreeCAD)
check_path(SCRIPT_PATH_Parameter_FreeCAD)
check_path(SCRIPT_PATH_PointCloud_FreeCAD)
check_path(SCRIPT_PATH_transform_OCC)
print("---------------------\n")
class Parameter_DATA:
    def __init__(self, in_path, mode='step', Fvector=(0, 0, 0), Frotation=0):
        """
        初始化參數數據類別。

        :param in_path: 輸入文件的路徑
        :param mode: 輸入文件的格式，預設為 'step'
        :param Fvector: 旋轉軸向量，預設為 (0, 0, 0)
        :param Frotation: 旋轉角度，預設為 0
        """
        self.in_path = in_path
        self.mode = mode
        self.Fvector = Fvector
        self.Frotation = Frotation
        
        # 確保 Fvector 是字串格式
        Fvector_str = ",".join(map(str, Fvector))

        # 修正：移除了重複的 Fvector_str 和 str(self.Frotation)
        self.result = subprocess.run(
        [
            freecad_python_exe, SCRIPT_PATH_Parameter_FreeCAD, 
            self.in_path, self.mode, 
            Fvector_str, str(self.Frotation)
        ],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8',
            errors='ignore' 
        )
        
        self.parameters = json.loads(self.result.stdout) if self.result.stdout else {}

    def Volume(self):
        return self.parameters[0]['Volume']
    def Area(self):
        return self.parameters[1]['Area']
    def CenterOfMass(self):
        return self.parameters[2]['CenterOfMass']
    def BoundBox(self):
        return self.parameters[3]['BoundBox']
    def EdgesNumber(self):
        return self.parameters[4]['EdgesNumber']
    def FaceNumber(self):
        return self.parameters[5]['FaceNumber']
    def VertexesNumber(self):
        return self.parameters[6]["VertexesNumber"]
    def MatrixOfInertia(self):
        return self.parameters[7]["MatrixOfInertia"]
    def MaxArea(self):
        return self.parameters[8]["MaxArea"]
    def EulerCharacteristic(self):
        return self.parameters[9]["EulerCharacteristic"]
    def PrincipalMoments(self):
        return self.parameters[10]["PrincipalMoments"]

    def __str__(self):
        return (f"Volume:{self.Volume()}\nArea:{self.Area()}\nCenterOfMass:{self.CenterOfMass()}\n"
                f"BoundBox:{self.BoundBox()}\nEdgesNumber:{self.EdgesNumber()}\nFaceNumber:{self.FaceNumber()}\n"
                f"VertexesNumber:{self.VertexesNumber()}\nMatrixOfInertia:{self.MatrixOfInertia()}\n"
                f"MaxArea:{self.MaxArea()}\nEulerCharacteristic:{self.EulerCharacteristic()}\n"
                f"PrincipalMoments:{self.PrincipalMoments()}")

    def to_hdf5(self, hdf5_path, mode='w'):
        """
        將參數寫入 HDF5 檔案，先用 ASCII 臨時檔名儲存，再重新命名，並支援中文路徑。

        :param hdf5_path: 要輸出的 .h5 路徑，可以包含中文
        :param mode: HDF5 開檔模式，預設 'w'
        """
        # 1. 確保父資料夾存在
        p = Path(hdf5_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        
        # 2. 生成一個臨時 ASCII 檔名
        with tempfile.NamedTemporaryFile(delete=False, suffix='.h5') as tmp_file:
            temp_path = tmp_file.name
            
        """將數據儲存到 HDF5 檔案"""
        data_dict = {
            "Volume": [self.Volume()],
            "Area": [self.Area()],
            "CenterOfMass": [self.CenterOfMass()],
            "BoundBox": [self.BoundBox()],
            "EdgesNumber": [self.EdgesNumber()],
            "FaceNumber": [self.FaceNumber()],
            "VertexesNumber": [self.VertexesNumber()],
            "MatrixOfInertia": [self.MatrixOfInertia()],
            "MaxArea": [self.MaxArea()],
            "EulerCharacteristic": [self.EulerCharacteristic()],
            "PrincipalMoments": [self.PrincipalMoments()],
        }
        df = pd.DataFrame(data_dict)
        df.to_hdf(temp_path, key='parameters', mode=mode)
        
        # 4. 將臨時檔案重新命名為最終的檔名
        shutil.move(temp_path, hdf5_path)
        print(f"Data saved to {hdf5_path}")
        
        # 直接呼叫 __str__ 回傳，避免重複寫長字串
        return self.__str__()
    
class ParameterExtractor:
    def __init__(self, hdf5_path):
        """
        初始化：讀取 HDF5 檔案中的參數資訊

        :param hdf5_path: HDF5 檔案的完整路徑
        """
        self.hdf5_path = hdf5_path
        try:
            self.df = pd.read_hdf(hdf5_path, key='parameters')
        except Exception as e:
            raise ValueError(f"Failed to read HDF5 file: {e}")
        
        if self.df.empty:
            raise ValueError("The HDF5 file is empty or the key is incorrect.")

    def Volume(self):
        return self.df["Volume"].iloc[0]

    def Area(self):
        return self.df["Area"].iloc[0]

    def CenterOfMass(self):
        return self.df["CenterOfMass"].iloc[0]

    def BoundBox(self):
        return self.df["BoundBox"].iloc[0]

    def EdgesNumber(self):
        return self.df["EdgesNumber"].iloc[0]

    def FaceNumber(self):
        return self.df["FaceNumber"].iloc[0]

    def VertexesNumber(self):
        return self.df["VertexesNumber"].iloc[0]

    def MatrixOfInertia(self):
        return self.df["MatrixOfInertia"].iloc[0]

    def MaxArea(self):
        return self.df["MaxArea"].iloc[0]

    def EulerCharacteristic(self):
        return self.df["EulerCharacteristic"].iloc[0]

    def PrincipalMoments(self):
        return self.df["PrincipalMoments"].iloc[0]

    def __str__(self):
        return (
            f"Volume: {self.Volume()}\n"
            f"Area: {self.Area()}\n"
            f"CenterOfMass: {self.CenterOfMass()}\n"
            f"BoundBox: {self.BoundBox()}\n"
            f"EdgesNumber: {self.EdgesNumber()}\n"
            f"FaceNumber: {self.FaceNumber()}\n"
            f"VertexesNumber: {self.VertexesNumber()}\n"
            f"MatrixOfInertia: {self.MatrixOfInertia()}\n"
            f"MaxArea: {self.MaxArea()}\n"
            f"EulerCharacteristic: {self.EulerCharacteristic()}\n"
            f"PrincipalMoments: {self.PrincipalMoments()}"
        )
class STL_DATA:
    def __init__(self,in_path = None,out_path = None):
        self.in_path = in_path
        self.out_path =out_path
    #網格
    def STLtoMesh(self):
        import trimesh


        # 載入 STL 檔案
        mesh = trimesh.load(self.in_path)
        vertices = mesh.vertices
        faces = mesh.faces

        # 如果有指定 out_path，自動根據副檔名處理儲存
        if self.out_path:
            ext = os.path.splitext(self.out_path)[1].lower()
            out_dir = os.path.dirname(self.out_path)
            os.makedirs(out_dir, exist_ok=True)

            import tempfile

            # 建立英文暫存檔
            fd, tmp_path = tempfile.mkstemp(prefix="mesh_", suffix=ext)
            os.close(fd)

            if ext == '.npz':
                np.savez(tmp_path, vertices=vertices, faces=faces)

            elif ext in ['.ply', '.obj']:
                mesh.export(tmp_path, file_type=ext[1:])  # 去掉點再傳進去，比如 'ply' or 'obj'

            elif ext == '.h5':
                import h5py
                with h5py.File(tmp_path, 'w') as hf:
                    hf.create_dataset('vertices', data=vertices)
                    hf.create_dataset('faces', data=faces)

            else:
                os.remove(tmp_path)
                raise ValueError(f"Unsupported file extension for export: {ext}")

            # 寫完再搬到 self.out_path（包含中文路徑也OK）
            os.replace(tmp_path, self.out_path)

        return np.array(vertices), np.array(faces)
    def MeshtoSTL(self,vertices_array, faces_array):
        import trimesh
        new_mesh = trimesh.Trimesh(vertices=vertices_array, faces=faces_array)
        return new_mesh.export(self.out_path)
    def LoadMesh(self):
        """
        讀取網格檔案 (.npz, .h5, .ply, .obj, **.stl**)。

        - 對於 .npz 和 .h5，它假定檔案是 'STLtoMesh' 函數產生的。
        - 對於 .ply, .obj, .stl，它使用 trimesh 標準載入。

        參數:
        file_path (str): 指向 .npz, .h5, .ply, .obj 或 .stl 檔案的路徑。

        返回:
        tuple (np.ndarray, np.ndarray): (vertices, faces)
        """
        if not os.path.exists(self.in_path):
            raise FileNotFoundError(f"檔案不存在: {self.in_path}")

        ext = os.path.splitext(self.in_path)[1].lower()

        vertices = None
        faces = None
        
        try:
            if ext == '.npz':
                # --- 讀取 .npz 檔案 ---
                data = np.load(self.in_path)
                if 'vertices' not in data or 'faces' not in data:
                    raise KeyError(f"'.npz' 檔案中找不到 'vertices' 或 'faces'。")
                vertices = data['vertices']
                faces = data['faces']
                
            elif ext == '.h5':
                # --- 讀取 .h5 檔案 ---
                with h5py.File(self.in_path, 'r') as hf:
                    if 'vertices' not in hf or 'faces' not in hf:
                        raise KeyError(f"'.h5' 檔案中找不到 'vertices' 或 'faces'。")
                    vertices = np.array(hf['vertices'])
                    faces = np.array(hf['faces'])
                    
            # --- 👇 修正：在這裡加入了 .stl 👇 ---
            elif ext in ['.ply', '.obj', '.stl']: 
                # --- 讀取 .ply, .obj, 或 .stl 檔案 ---
                # trimesh 會自動處理這些標準網格格式
                import trimesh
                mesh = trimesh.load_mesh(self.in_path)
                
                if not hasattr(mesh, 'vertices') or not hasattr(mesh, 'faces'):
                    raise ValueError(f"讀取的 '{ext}' 檔案 '{self.in_path}' 不是一個有效的網格 (缺少頂點或面)。")
                    
                vertices = np.array(mesh.vertices)
                faces = np.array(mesh.faces)
                
            else:
                # --- 👇 修正：在錯誤訊息中也加入 .stl 👇 ---
                raise ValueError(f"不支援的檔案格式: '{ext}'。僅支援 .npz, .h5, .ply, .obj, .stl")

        except Exception as e:
            print(f"讀取網格檔案 '{self.in_path}' 時發生錯誤: {e}")
            raise

        return vertices, faces
    def PlottoMesh(self, vertices, faces, mode='open3D', vertex_colors=None, line_colors=None):
        if mode == 'plt':
            # --- plt 模式 (未變動) ---
            fig = plt.figure()
            ax = fig.add_subplot(111, projection='3d')

            # Create a 3D polygon collection
            # 注意：Poly3DCollection 需要的 vertices 格式是 (n_faces, 3, 3)
            # 您的 vertices 陣列是 (n_points, 3)
            # vertices[faces] 會正確地索引它，變成 (n_faces, 3, 3)
            mesh_collection = Poly3DCollection(vertices[faces], alpha=0.5, edgecolor='k')

            # Add the collection to the plot
            ax.add_collection3d(mesh_collection)

            # Set plot limits
            ax.set_xlim(vertices[:, 0].min(), vertices[:, 0].max())
            ax.set_ylim(vertices[:, 1].min(), vertices[:, 1].max())
            ax.set_zlim(vertices[:, 2].min(), vertices[:, 2].max())

            plt.show()
            
        elif mode == 'open3D':
            # --- open3D 模式 (已修改) ---
            mesh = o3d.geometry.TriangleMesh()
            mesh.vertices = o3d.utility.Vector3dVector(vertices)
            mesh.triangles = o3d.utility.Vector3iVector(faces)

            # --- 👇 1. 新增：計算光照法向量 👇 ---
            # 這會讓網格在 3D 視窗中看起來更平滑、有正確的光影
            mesh.compute_vertex_normals()

            if vertex_colors is not None:
                mesh.vertex_colors = o3d.utility.Vector3dVector(vertex_colors)
            else:
                # 默认颜色（例如，灰色）
                mesh.paint_uniform_color([0.5, 0.5, 0.5])

            # --- 您的線框 (LineSet) 邏輯 (未變動) ---
            lines = []
            for face in faces:
                lines.append([face[0], face[1]])
                lines.append([face[1], face[2]])
                lines.append([face[2], face[0]])
            line_set = o3d.geometry.LineSet()
            line_set.points = o3d.utility.Vector3dVector(vertices)
            line_set.lines = o3d.utility.Vector2iVector(lines)

            if line_colors is not None:
                line_set.colors = o3d.utility.Vector3dVector(line_colors)
            else:
                # 默认颜色（例如，黑色）
                line_set.colors = o3d.utility.Vector3dVector([[0.0, 0.0, 0.0]] * len(lines))
            
            # --- 👇 2. 新增：建立世界座標軸 👇 ---
            aabb = mesh.get_axis_aligned_bounding_box()
            axis_size = aabb.get_max_extent() / 10.0
            if axis_size < 0.01: 
                axis_size = 1.0 
                
            world_coordinate_frame = o3d.geometry.TriangleMesh.create_coordinate_frame(
                size=axis_size, 
                origin=[0, 0, 0]
            )

            # --- 👇 3. 修改：將座標軸加入視覺化列表 👇 ---
            print("顯示網格、線框和世界座標軸 (紅=X, 綠=Y, 藍=Z)")
            o3d.visualization.draw_geometries(
                [mesh, line_set, world_coordinate_frame] # <-- 在列表中加入 world_coordinate_frame
            )
    #體素專用(公差 為 voxel_size，實體並非單表面)
    def STLtoVoxel(self,voxel_size=4.0):
        
        stltovoxel.convert_file(self.in_path, 'AutoV.xyz',voxel_size=voxel_size)
        points = []
        with open('AutoV.xyz', 'r') as file:
            for line in file:
                # 將每一行數據轉為浮點數
                point = list(map(float, line.strip().split()))
                points.append(point)
        point_cloud = o3d.geometry.PointCloud()

        point_cloud.points = o3d.utility.Vector3dVector(points)


        voxel_grid = o3d.geometry.VoxelGrid.create_from_point_cloud(point_cloud, voxel_size=voxel_size)

        # 3. 获取体素网格的范围
        bbox = voxel_grid.get_axis_aligned_bounding_box()
        min_bound = bbox.min_bound
        max_bound = bbox.max_bound

        # 计算体素网格的尺寸
        dims = np.ceil((max_bound - min_bound) / voxel_size).astype(int)

        # 4. 初始化体素数组
        voxel_array = np.zeros(dims, dtype=np.uint8)
        for voxel in voxel_grid.get_voxels():
            # 计算体素索引
            idx = np.floor((np.array(voxel.grid_index) * voxel_size + min_bound - min_bound) / voxel_size).astype(int)
            if np.any(idx < 0) or np.any(idx >= dims):
                print(f"Skipping out of bounds voxel: {voxel.grid_index}, {idx}, {dims}")
                continue
            voxel_array[tuple(idx)] = 1
        """
        mesh = o3d.io.read_triangle_mesh(self.in_path)

        # 2. Convert mesh to voxel grid
        voxel_grid = o3d.geometry.VoxelGrid.create_from_triangle_mesh_within_bounds(
            input=mesh,
            voxel_size=voxel_size,
            min_bound=mesh.get_min_bound() - 0.1,
            max_bound=mesh.get_max_bound() + 0.1
        )

        # 3. Get voxel grid bounds and dimensions
        bbox = voxel_grid.get_axis_aligned_bounding_box()
        min_bound = bbox.min_bound
        max_bound = bbox.max_bound
        dims = np.ceil((max_bound - min_bound) / voxel_size).astype(int)

        # 4. Initialize TensorFlow tensor
        voxel_tensor = tf.zeros(dims.tolist(), dtype=tf.uint8)

        # 5. Convert voxel grid to tensor
        indices = []
        updates = []
        for voxel in voxel_grid.get_voxels():
            idx = np.floor((np.array(voxel.grid_index) * voxel_size + min_bound - min_bound) / voxel_size).astype(int)
            if np.any(idx < 0) or np.any(idx >= dims):
                print(f"Skipping out of bounds voxel: {voxel.grid_index}, {idx}, {dims}")
                continue
            indices.append(idx)
            updates.append(1)

        # Create a tensor from the indices and updates
        indices = tf.convert_to_tensor(indices, dtype=tf.int64)
        updates = tf.convert_to_tensor(updates, dtype=tf.uint8)

        voxel_tensor = tf.tensor_scatter_nd_update(voxel_tensor, indices, updates)

        # 6. Return tensor, min_bound, and voxel_size
        return voxel_tensor.numpy(), min_bound, voxel_size

        """
        """
        import  trimesh
        mesh = trimesh.load(self.in_path)

        if not mesh.faces.any() or not mesh.vertices.any():
            raise ValueError("Mesh must have faces and vertices.")

            # 1. Compute voxel grid bounds and dimensions
        min_bound = mesh.bounds[0]
        max_bound = mesh.bounds[1]
        dims = np.ceil((max_bound - min_bound) / voxel_size).astype(int)

        # Initialize voxel grid
        voxel_grid = np.zeros(dims, dtype=np.uint8)

        # Convert mesh vertices to voxel grid indices
        vertices = mesh.vertices
        faces = mesh.faces

        # Compute voxel grid indices for each vertex
        voxel_indices = np.floor((vertices - min_bound) / voxel_size).astype(int)

        # Update voxel grid for each face
        for face in faces:
            v0, v1, v2 = voxel_indices[face]
            x_min, y_min, z_min = np.min([v0, v1, v2], axis=0)
            x_max, y_max, z_max = np.max([v0, v1, v2], axis=0)
            voxel_grid[x_min:x_max + 1, y_min:y_max + 1, z_min:z_max + 1] = 1

        # Convert voxel grid to PyTorch tensor
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        voxel_tensor = torch.tensor(voxel_grid, dtype=torch.uint8, device=device)

        # Return tensor, min_bound, and voxel_size
        return voxel_tensor.cpu().numpy(), min_bound, voxel_size
        """
        """
        import trimesh
        # 1. 读取三角网格模型
        mesh = o3d.io.read_triangle_mesh(self.in_path)

        # 2. 将网格转换成体素网格
        voxel_grid = o3d.geometry.VoxelGrid.create_from_triangle_mesh_within_bounds(
            input=mesh,
            voxel_size=voxel_size,
            min_bound=mesh.get_min_bound() - 0.1,
            max_bound=mesh.get_max_bound() + 0.1
        )

        # 3. 获取体素网格的范围
        bbox = voxel_grid.get_axis_aligned_bounding_box()
        min_bound = bbox.min_bound
        max_bound = bbox.max_bound

        # 计算体素网格的尺寸
        dims = np.ceil((max_bound - min_bound) / voxel_size).astype(int)

        # 4. 初始化体素数组
        voxel_array = np.zeros(dims, dtype=np.uint8)

        # 5. 将体素网格转换为数值数组
        for voxel in voxel_grid.get_voxels():
            # 计算体素索引
            idx = np.floor((np.array(voxel.grid_index) * voxel_size + min_bound - min_bound) / voxel_size).astype(int)
            if np.any(idx < 0) or np.any(idx >= dims):
                print(f"Skipping out of bounds voxel: {voxel.grid_index}, {idx}, {dims}")
                continue
            voxel_array[tuple(idx)] = 1

        # 6. 填充体素内部
        # 确定所有被填充的体素的位置
        filled_positions = np.argwhere(voxel_array == 1)

        # 获取每个维度的最小和最大范围
        min_coords = filled_positions.min(axis=0)
        max_coords = filled_positions.max(axis=0)

        # 填满体素网格的内部区域
        voxel_array[min_coords[0]:max_coords[0] + 1,
        min_coords[1]:max_coords[1] + 1,
        min_coords[2]:max_coords[2] + 1] = 1
        """
        # 7. 返回填满的体素数组、最小边界和体素大小
        if self.out_path:
            import os
            import tempfile
            import shutil

            ext = os.path.splitext(self.out_path)[1].lower()
            out_dir = os.path.dirname(self.out_path)
            os.makedirs(out_dir, exist_ok=True)

            # 生成 ASCII-only 的暫存檔名（在全英文的系統 temp 資料夾）
            fd, tmp_path = tempfile.mkstemp(prefix="voxel_", suffix=ext)
            os.close(fd)

            try:
                if ext == ".npz":
                    # 儲存多個陣列到 npz
                    np.savez(tmp_path,
                            voxel_array=voxel_array,
                            min_bound=min_bound,
                            voxel_size=voxel_size)

                elif ext == ".h5":
                    import h5py
                    # 儲存到 HDF5
                    with h5py.File(tmp_path, 'w') as hf:
                        hf.create_dataset('voxel_array', data=voxel_array)
                        hf.create_dataset('min_bound',    data=min_bound)
                        hf.create_dataset('voxel_size',   data=voxel_size)

                else:
                    raise ValueError(f"Unsupported file extension for voxel export: {ext}")

                # 全部寫完後，再搬到最終的 self.out_path（跨磁碟也 OK）
                shutil.copyfile(tmp_path, self.out_path)

            finally:
                # 不論成功或失敗，都清理暫存檔
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

        return voxel_array, min_bound, voxel_size
    def LoadVoxel(self):
        """
        讀取由 STLtoVoxel 函數產生的體素檔案 (.npz 或 .h5)。

        這個函數是 STLtoVoxel 儲存邏輯的「反向」操作。

        參數:
        self.in_path (str): 指向 .npz 或 .h5 檔案的路徑。

        返回:
        tuple: (voxel_array, min_bound, voxel_size)
            - voxel_array (np.ndarray): 體素數據 (D, H, W)
            - min_bound (np.ndarray): 體素網格的最小邊界 (3,)
            - voxel_size (float): 體素的大小 (純量)
        
        可能引發的錯誤:
        FileNotFoundError: 如果檔案不存在。
        KeyError: 如果 .npz 或 .h5 檔案中缺少必要的鍵/數據集。
        ValueError: 如果是無法識別或不支援的檔案格式。
        """
        if not os.path.exists(self.in_path):
            raise FileNotFoundError(f"檔案不存在: {self.in_path}")

        # 獲取檔案副檔名（並轉為小寫以確保一致性）
        ext = os.path.splitext(self.in_path)[1].lower()

        voxel_array = None
        min_bound = None
        voxel_size = None
        
        try:
            if ext == '.npz':
                # --- 讀取 .npz 檔案 ---
                # 產生器使用: np.savez(..., voxel_array=va, min_bound=mb, voxel_size=vs)
                data = np.load(self.in_path)
                
                # 檢查必要的 keys 是否都存在
                required_keys = ['voxel_array', 'min_bound', 'voxel_size']
                if not all(key in data for key in required_keys):
                    raise KeyError(f"'.npz' 檔案中缺少必要的 key。應包含 {required_keys}，"
                                f"但只找到: {list(data.keys())}")
                
                voxel_array = data['voxel_array']
                min_bound = data['min_bound']
                # .item() 將 0 維陣列 (array(4.0)) 轉換回純量 (4.0)
                voxel_size = data['voxel_size'].item()
                
            elif ext == '.h5':
                # --- 讀取 .h5 檔案 ---
                # 產生器使用: hf.create_dataset('voxel_array', ...), etc.
                with h5py.File(self.in_path, 'r') as hf:
                    
                    # 檢查必要的 datasets 是否都存在
                    required_keys = ['voxel_array', 'min_bound', 'voxel_size']
                    if not all(key in hf for key in required_keys):
                        raise KeyError(f"'.h5' 檔案中缺少必要的 dataset。應包含 {required_keys}"
                                    f"但只找到: {list(hf.keys())}")
                    
                    voxel_array = np.array(hf['voxel_array'])
                    min_bound = np.array(hf['min_bound'])
                    # [()] 是從 h5py 讀取純量 (scalar) 的標準方法
                    voxel_size = hf['voxel_size'][()]
                    
            else:
                raise ValueError(f"不支援的檔案格式: '{ext}'。僅支援 .npz 和 .h5")

        except Exception as e:
            # 捕捉所有可能的讀取錯誤（例如檔案損壞）並提供更多上下文
            print(f"讀取體素檔案 '{self.in_path}' 時發生錯誤: {e}")
            raise  # 重新拋出錯誤

        return voxel_array, min_bound, voxel_size

    def PlottoVoxel(self,voxel_array, min_vals, voxel_size,Voxel_color = [1,1,1],wireframe_color = np.array([0, 0, 0]) ):
        points = []

        # 2. 将数值数组中的 1 转换为点
        for index, value in np.ndenumerate(voxel_array):
            if value == 1:
                point = np.array(index) * voxel_size + min_vals + voxel_size / 2
                points.append(point)

        # 3. 创建点云对象
        point_cloud = o3d.geometry.PointCloud()
        point_cloud.points = o3d.utility.Vector3dVector(points)

        # 设置点云颜色
        colors = np.tile(Voxel_color, (len(points), 1))
        point_cloud.colors = o3d.utility.Vector3dVector(colors)

        # 4. 从点云创建体素网格
        voxel_grid = o3d.geometry.VoxelGrid.create_from_point_cloud(point_cloud, voxel_size)

        # 设定体素颜色
        for voxel in voxel_grid.get_voxels():
            voxel.color = Voxel_color
        # 创建线框
        lines = []
        for voxel in voxel_grid.get_voxels():
            x, y, z = voxel.grid_index
            v0 = np.array([x, y, z]) * voxel_size + min_vals
            v1 = v0 + [voxel_size, 0, 0]
            v2 = v0 + [0, voxel_size, 0]
            v3 = v0 + [0, 0, voxel_size]
            v4 = v0 + [voxel_size, voxel_size, 0]
            v5 = v0 + [voxel_size, 0, voxel_size]
            v6 = v0 + [0, voxel_size, voxel_size]
            v7 = v0 + [voxel_size, voxel_size, voxel_size]
            lines.extend([
                [v0, v1], [v0, v2], [v0, v3], [v1, v4], [v1, v5], [v2, v4], [v2, v6],
                [v3, v5], [v3, v6], [v4, v7], [v5, v7], [v6, v7]
            ])

        # 创建 LineSet 对象
        line_set = o3d.geometry.LineSet()
        line_set.points = o3d.utility.Vector3dVector(
            np.array([line[0] for line in lines] + [line[1] for line in lines]))
        line_set.lines = o3d.utility.Vector2iVector(np.array([[i, i + len(lines)] for i in range(len(lines))]))
        line_set.colors = o3d.utility.Vector3dVector(np.tile(wireframe_color, (len(lines), 1)))

        # --- 👇 4. 新增：計算座標軸大小 (從點雲 AABB) 👇 ---
        # 我們從點雲獲取邊界框，以決定座標軸的合適大小
        aabb = point_cloud.get_axis_aligned_bounding_box()
        axis_size = aabb.get_max_extent() / 10.0
        if axis_size < 0.01:
            axis_size = 1.0
            
        # 建立世界座標軸
        world_coordinate_frame = o3d.geometry.TriangleMesh.create_coordinate_frame(
            size=axis_size,
            origin=[0, 0, 0] # 座標軸放在世界原點
        )
        # --- 👇 7. 修改：將座標軸加入視覺化列表 👇 ---
        print("顯示 Voxel Grid、線框和世界座標軸 (紅=X, 藍=Z)")
        o3d.visualization.draw_geometries(
            [voxel_grid, line_set, world_coordinate_frame],
            point_show_normal=False # Voxel 和 LineSet 不需要顯示法向量
        )
    #點雲圖
    def STLtoCloud(self, mode='random', number_of_points=65536, voxel_size=1.0):
        import trimesh
        import h5py
        import tempfile

        mesh = trimesh.load_mesh(self.in_path)

        if mode == 'random':
            # 隨機採樣
            pcd, _ = trimesh.sample.sample_surface(mesh, number_of_points)
        elif mode == 'fps':
            # 2. 最遠點採樣 (小樣本推薦，6萬點會很慢)
            # 先過度採樣 2 倍作為候選池
            pool, _ = trimesh.sample.sample_surface(mesh, number_of_points * 2)
            
            # FPS 邏輯
            n = len(pool)
            fps_idx = np.zeros(number_of_points, dtype=int)
            fps_idx[0] = np.random.randint(n)
            distances = np.linalg.norm(pool - pool[fps_idx[0]], axis=1)
            for i in range(1, number_of_points):
                idx = np.argmax(distances)
                fps_idx[i] = idx
                new_dist = np.linalg.norm(pool - pool[idx], axis=1)
                distances = np.minimum(distances, new_dist)
            pcd = pool[fps_idx]

        elif mode == 'surface_uniform':
            # 3. 表面均勻採樣 (利用 Voxel Grid 概念避免 remove_close 報錯)
            pool, _ = trimesh.sample.sample_surface(mesh, number_of_points * 5)
            # 自動計算間距：sqrt(總面積 / 點數)
            spacing = np.sqrt(mesh.area / number_of_points) * 0.9
            
            # 透過將座標「整數化」到格子中來達成均勻化
            coords = (pool / spacing).astype(int)
            _, kept_idx = np.unique(coords, axis=0, return_index=True)
            pcd = pool[kept_idx]

            # 強制對齊點數
            if len(pcd) > number_of_points:
                pcd = pcd[np.random.choice(len(pcd), number_of_points, replace=False)]
            elif len(pcd) < number_of_points:
                needed = number_of_points - len(pcd)
                extra, _ = trimesh.sample.sample_surface(mesh, needed)
                pcd = np.concatenate([pcd, extra], axis=0)
        elif mode == 'uniform':
            # 均勻採樣（體素化）
            voxel_grid = trimesh.voxel.VoxelGrid(mesh, voxel_size)
            pcd = voxel_grid.points

        # === 4. 實體均勻網格 (Solid Uniform / Grid) ===
        elif mode == 'solid_uniform':
            # A. 估算理想的網格間距 (Pitch)
            # 嘗試取得體積 (若模型有破洞，體積計算可能會不準，改用 Bounding Box 估算)
            try:
                vol = mesh.volume
            except:
                vol = mesh.bounding_box.volume * 0.5 # 假設填充率 50%
            
            if vol <= 0: vol = mesh.bounding_box.volume * 0.5

            # 公式：間距 = (體積 / 目標點數)^(1/3)
            # 稍微縮小間距 (0.95) 以確保產生的點比需求多一點，方便後續削減
            estimated_pitch = (vol / number_of_points) ** (1/3) * 0.95
            
            # B. 建立 3D 網格點
            bounds = mesh.bounds
            x = np.arange(bounds[0][0], bounds[1][0], estimated_pitch)
            y = np.arange(bounds[0][1], bounds[1][1], estimated_pitch)
            z = np.arange(bounds[0][2], bounds[1][2], estimated_pitch)
            
            grid_x, grid_y, grid_z = np.meshgrid(x, y, z, indexing='ij')
            # 攤平成 (N, 3) 陣列
            candidates = np.stack((grid_x.flatten(), grid_y.flatten(), grid_z.flatten()), axis=1)
            
            # C. 過濾內部點
            inside_mask = mesh.contains(candidates)
            pcd = candidates[inside_mask]

            # D. 強制數量對齊 (因為網格無法剛好命中數量)
            if len(pcd) > number_of_points:
                # 點太多：隨機削減 (不重複)
                indices = np.random.choice(len(pcd), number_of_points, replace=False)
                pcd = pcd[indices]
            elif len(pcd) < number_of_points:
                # 點太少：隨機補點 (重複採樣)
                # 或是您可以選擇在這裡拋出錯誤，要求縮小 voxel_size
                needed = number_of_points - len(pcd)
                if len(pcd) > 0:
                    indices = np.random.choice(len(pcd), needed, replace=True)
                    pcd = np.concatenate([pcd, pcd[indices]], axis=0)
                else:
                    # 極端情況：間距太大導致一個點都沒選到，回退到 random
                    pcd, _ = trimesh.sample.sample_surface(mesh, number_of_points)
        else:
            raise ValueError(f"Unknown mode: {mode}")
        
        import shutil

        if self.out_path:
            ext = os.path.splitext(self.out_path)[1].lower()
            out_dir = os.path.dirname(self.out_path)
            os.makedirs(out_dir, exist_ok=True)

            # 生成 ASCII-only 的暫存檔名（在全英文的系統 temp 資料夾）
            fd, tmp_path = tempfile.mkstemp(prefix="cloud_", suffix=ext)
            os.close(fd)

            if ext == '.npz':
                np.savez(tmp_path, point_cloud=pcd)
            elif ext == '.h5':
                with h5py.File(tmp_path, 'w') as hf:
                    hf.create_dataset('point_cloud', data=pcd)
            elif ext == '.ply':
                cloud_mesh = trimesh.points.PointCloud(pcd)
                cloud_mesh.export(tmp_path, file_type='ply')
            else:
                os.remove(tmp_path)
                raise ValueError(f"Unsupported file extension for export: {ext}")

            # ⚡ 改成 copy + delete（跨磁碟也 OK）
            shutil.copyfile(tmp_path, self.out_path)
            os.remove(tmp_path)

        return np.array(pcd)
    def LoadCloud(self, datasetname = 'point_cloud' ):
        """
        讀取由 STLtoCloud 函數產生的點雲檔案 (.npz, .h5, .ply)。

        這個函數是 STLtoCloud 儲存邏輯的「反向」操作。

        參數:
        file_path (str): 指向 .npz, .h5, 或 .ply 檔案的路徑。

        返回:
        numpy.ndarray: 點雲數據 (N, 3)。
        
        可能引發的錯誤:
        FileNotFoundError: 如果檔案不存在。
        KeyError: 如果 .npz 或 .h5 檔案中缺少 'point_cloud' 鍵/數據集。
        ValueError: 如果是無法識別或不支援的檔案格式。
        """
        if not os.path.exists(self.in_path):
            raise FileNotFoundError(f"檔案不存在: {self.in_path}")

        # 獲取檔案副檔名（並轉為小寫以確保一致性）
        ext = os.path.splitext(self.in_path)[1].lower()

        pcd = None
        
        try:
            if ext == '.npz':
                # --- 讀取 .npz 檔案 ---
                # 產生器使用: np.savez(..., point_cloud=pcd)
                # 讀取器使用: np.load(...)['point_cloud']
                data = np.load(self.in_path)
                if datasetname not in data:
                    raise KeyError(f"'.npz' 檔案中找不到 'point_cloud' 這個 key。可用的 keys: {list(data.keys())}")
                pcd = data[datasetname]
                
            elif ext == '.h5':
                # --- 讀取 .h5 檔案 ---
                # 產生器使用: hf.create_dataset('point_cloud', data=pcd)
                # 讀取器使用: h5py.File(...)['point_cloud']
                with h5py.File(self.in_path, 'r') as hf:
                    if datasetname not in hf:
                        raise KeyError(f"'.h5' 檔案中找不到 'point_cloud' 這個 dataset。可用的 datasets: {list(hf.keys())}")
                    # 使用 [()] 或 np.array() 將 h5 dataset 讀取到記憶體中
                    pcd = np.array(hf[datasetname])
                    
            elif ext == '.ply':
                # --- 讀取 .ply 檔案 ---
                # 產生器使用: cloud_mesh.export(..., file_type='ply')
                # 讀取器使用: trimesh.load_mesh(...)
                # trimesh 會將 PLY 檔案（即使只有點）作為一個 mesh 物件載入
                import trimesh
                mesh = trimesh.load_mesh(self.in_path)
                
                # 點的座標儲存在 .vertices 屬性中
                if not hasattr(mesh, 'vertices') or len(mesh.vertices) == 0:
                    raise ValueError("讀取的 .ply 檔案不包含任何頂點 (vertices)。")
                pcd = np.array(mesh.vertices)
                
            else:
                raise ValueError(f"不支援的檔案格式: '{ext}'。僅支援 .npz, .h5, .ply")

        except Exception as e:
            # 捕捉所有可能的讀取錯誤（例如檔案損壞）並提供更多上下文
            print(f"讀取檔案 '{self.in_path}' 時發生錯誤: {e}")
            raise  # 重新拋出錯誤，讓呼叫者知道發生了問題

        return pcd
    def STLtoNormalCloud(self, mode='random', number_of_points=65536, voxel_size=1.0):
        import trimesh
        import h5py
        import tempfile
        mesh = trimesh.load_mesh(self.in_path)
       

        if mode == 'random':
            # 隨機表面點採樣 + 法向量
            points, face_idx = trimesh.sample.sample_surface(mesh, number_of_points)
            normals = mesh.face_normals[face_idx]
        elif mode == 'fps':
            # --- Farthest Point Sampling ---
            # 1. 先從表面過度採樣 (Oversampling) 作為候選池，通常採樣 2-4 倍
            pool_size = number_of_points * 2 
            pool_points, pool_face_idx = trimesh.sample.sample_surface(mesh, pool_size)
            
            # 2. 執行 FPS 取得索引 (注意：6萬點在 Python 跑 FPS 會非常慢)
            # 如果點數太多，建議改用 surface_uniform 模式
            print(f"Running FPS for {number_of_points} points... (this may take a while)")

            def farthest_point_sampling_indices(pts, k):
                """
                pts: (N, 3) 點雲池
                k: 目標數量
                return: 選中點的索引 (k,)
                """
                n = len(pts)
                if n <= k: return np.arange(n)

                selected_indices = np.zeros(k, dtype=int)
                # 隨機選一個點作為起點
                selected_indices[0] = np.random.randint(n)
                distances = np.linalg.norm(pts - pts[selected_indices[0]], axis=1)

                for i in range(1, k):
                    idx = np.argmax(distances)
                    selected_indices[i] = idx
                    # 更新最短距離
                    new_dist = np.linalg.norm(pts - pts[idx], axis=1)
                    distances = np.minimum(distances, new_dist)
                    
                return selected_indices
            fps_idx = farthest_point_sampling_indices(pool_points, number_of_points)
            
            points = pool_points[fps_idx]
            normals = mesh.face_normals[pool_face_idx[fps_idx]]
        elif mode == 'surface_uniform':
            # --- 表面均勻採樣 (Voxel-based Thinning) ---
            # 1. 過度採樣
            pool_size = number_of_points * 5
            pool_points, pool_face_idx = trimesh.sample.sample_surface(mesh, pool_size)
            
            # 2. 計算合適的體素間距 (Voxel size)
            # 根據面積估算點與點之間的理論距離
            area = mesh.area
            spacing = np.sqrt(area / number_of_points) * 0.9 
            
            # 3. 執行體素下採樣以取得索引
            # 將座標除以間距後取整數，重複的點代表落在同一個格子裡
            coords = (pool_points / spacing).astype(int)
            _, kept_idx = np.unique(coords, axis=0, return_index=True)
            
            points = pool_points[kept_idx]
            face_idx = pool_face_idx[kept_idx]

            # 4. 強制對齊點數 (確保輸出剛好是 number_of_points)
            if len(points) > number_of_points:
                # 均勻後隨機選，依然保持均勻性
                final_idx = np.random.choice(len(points), number_of_points, replace=False)
                points = points[final_idx]
                face_idx = face_idx[final_idx]
            elif len(points) < number_of_points:
                # 點數不夠則補隨機點
                needed = number_of_points - len(points)
                extra_p, extra_f = trimesh.sample.sample_surface(mesh, needed)
                points = np.concatenate([points, extra_p], axis=0)
                face_idx = np.concatenate([face_idx, extra_f], axis=0)
            
            normals = mesh.face_normals[face_idx]
        elif mode == 'uniform':
            # 均勻體素採樣
            voxel_grid = mesh.voxelized(pitch=voxel_size)
            pcd = voxel_grid.points
            points = pcd
            # 無法提供正確法向量，填零
            normals = np.zeros_like(points)
        # === 3. 實體隨機 (Solid Random) - 內部填滿，法向為 0 ===
        elif mode == 'solid_random':
            min_bound, max_bound = mesh.bounds
            collected_points = []
            current_count = 0
            batch_size = number_of_points * 2
            
            # 循環撒點直到數量足夠
            while current_count < number_of_points:
                random_points = np.random.uniform(min_bound, max_bound, (batch_size, 3))
                inside_mask = mesh.contains(random_points)
                valid_points = random_points[inside_mask]
                
                if len(valid_points) > 0:
                    collected_points.append(valid_points)
                    current_count += len(valid_points)
            
            # 合併並裁切
            points = np.concatenate(collected_points, axis=0)
            points = points[:number_of_points]
            # 內部點法向設為 0
            normals = np.zeros_like(points)

        # === 4. 實體均勻網格 (Solid Uniform) - 內部填滿，法向為 0 ===
        elif mode == 'solid_uniform':
            # A. 估算間距
            try:
                vol = mesh.volume
            except:
                vol = mesh.bounding_box.volume * 0.5
            
            if vol <= 0: vol = mesh.bounding_box.volume * 0.5
            
            # 計算 Pitch，係數 0.95 是為了稍微多採一點點備用
            estimated_pitch = (vol / number_of_points) ** (1/3) * 0.95
            
            # B. 建立網格
            bounds = mesh.bounds
            x = np.arange(bounds[0][0], bounds[1][0], estimated_pitch)
            y = np.arange(bounds[0][1], bounds[1][1], estimated_pitch)
            z = np.arange(bounds[0][2], bounds[1][2], estimated_pitch)
            grid_x, grid_y, grid_z = np.meshgrid(x, y, z, indexing='ij')
            candidates = np.stack((grid_x.flatten(), grid_y.flatten(), grid_z.flatten()), axis=1)
            
            # C. 過濾
            inside_mask = mesh.contains(candidates)
            points = candidates[inside_mask]

            # D. 強制數量對齊 (多退少補)
            if len(points) > number_of_points:
                indices = np.random.choice(len(points), number_of_points, replace=False)
                points = points[indices]
            elif len(points) < number_of_points:
                needed = number_of_points - len(points)
                if len(points) > 0:
                    indices = np.random.choice(len(points), needed, replace=True)
                    points = np.concatenate([points, points[indices]], axis=0)
                else:
                    # 極端失敗情況回退
                    points, _ = trimesh.sample.sample_surface(mesh, number_of_points)

            # 內部點法向設為 0
            normals = np.zeros_like(points)
        else:
            raise ValueError(f"Unknown mode: {mode}")

        # 存檔（若指定）
        if self.out_path:
            ext = os.path.splitext(self.out_path)[1].lower()
            out_dir = os.path.dirname(self.out_path)
            os.makedirs(out_dir, exist_ok=True)

            fd, tmp_path = tempfile.mkstemp(prefix="cloud_", suffix=ext)
            os.close(fd)

            if ext == '.npz':
                np.savez(tmp_path, point_cloud=points, normals=normals)
            elif ext == '.h5':
                with h5py.File(tmp_path, 'w') as hf:
                    hf.create_dataset('point_cloud', data=points)
                    hf.create_dataset('normals', data=normals)
            elif ext == '.ply':
                cloud_mesh = trimesh.points.PointCloud(points, normals=normals)
                cloud_mesh.export(tmp_path, file_type='ply')
            else:
                os.remove(tmp_path)
                raise ValueError(f"Unsupported file extension for export: {ext}")

            shutil.copyfile(tmp_path, self.out_path)
            os.remove(tmp_path)

        return np.hstack([points, normals])  # 與 ModelNet40 相容的格式：Nx6
        """
        mesh = o3d.io.read_triangle_mesh(self.in_path)

        if mode == 'random':
            # 2. 生成点云 (随机采样)
            pcd = mesh.sample_points_poisson_disk(number_of_points=number_of_points)
            # 返回点云坐标
            return np.asarray(pcd.points)

        elif mode == 'uniform':
            # 2. 体素化点云 (均匀采样)
            mesh.compute_vertex_normals()

            # 3. 创建体素网格
            voxel_grid = o3d.geometry.VoxelGrid.create_from_triangle_mesh_within_bounds(
                input=mesh,
                voxel_size=voxel_size,
                min_bound=mesh.get_min_bound(),
                max_bound=mesh.get_max_bound()
            )

            # 4. 将体素网格转换为点云
            points = voxel_grid.get_voxels()
            point_cloud_coords = np.array([voxel.grid_index * voxel_grid.voxel_size for voxel in points])

            # 5. 使用 TensorFlow 加速处理
            point_cloud_coords = tf.convert_to_tensor(point_cloud_coords, dtype=tf.float32)

            # 如果需要进一步处理或加速计算，你可以继续使用 TensorFlow 进行操作
            # 比如进行归一化或其他转换
            # point_cloud_coords = tf.math.divide(point_cloud_coords, tf.reduce_max(point_cloud_coords))

            # 6. 返回点云坐标
            return point_cloud_coords.numpy()
        """
        """mesh = o3d.io.read_triangle_mesh(self.in_path)
        if mode == 'random':
            # 生成点云
            pcd = mesh.sample_points_poisson_disk(number_of_points=number_of_points)
            #o3d.visualization.draw_geometries([pcd])
            return np.asarray(pcd.points)
        elif mode == 'uniform':
            # 体素化点云
            mesh.compute_vertex_normals()
            # 创建一个三维的体素网格
            voxel_grid = o3d.geometry.VoxelGrid.create_from_triangle_mesh_within_bounds(
                input=mesh,
                voxel_size=voxel_size,
                min_bound=mesh.get_min_bound(),
                max_bound=mesh.get_max_bound()
            )

            # 将体素网格转换为点云
            points = voxel_grid.get_voxels()
            point_cloud = o3d.geometry.PointCloud()
            point_cloud.points = o3d.utility.Vector3dVector([voxel.grid_index * voxel_grid.voxel_size for voxel in points])

            # 获取点云坐标
            point_cloud_coords = np.asarray(point_cloud.points)
            #o3d.visualization.draw_geometries([point_cloud])
            # 可视化体素化后的点云
            return point_cloud_coords """
    def LoadNormalCloud(self, dataset_points_key='point_cloud', dataset_normals_key='normals'):
        """
        讀取由 STLtoNormalCloud 產生的點雲檔案 (.npz, .h5, .ply)。
        
        修正重點：
        1. 同步讀取 'point_cloud' (座標) 與 'normals' (法向量)。
        2. 將兩者合併 (hstack)，還原成 Nx6 格式，以符合訓練需求。

        參數:
        dataset_points_key (str): 儲存點座標的鍵值名稱 (預設: 'point_cloud')
        dataset_normals_key (str): 儲存法向量的鍵值名稱 (預設: 'normals')

        返回:
        numpy.ndarray: 點雲數據，形狀為 (N, 6)。前三欄為 XYZ，後三欄為 Nx Ny Nz。
        """
        import os
        import numpy as np
        import h5py
        import trimesh

        if not os.path.exists(self.in_path):
            raise FileNotFoundError(f"檔案不存在: {self.in_path}")

        ext = os.path.splitext(self.in_path)[1].lower()
        points = None
        normals = None

        try:
            # --- 讀取 .npz 檔案 ---
            if ext == '.npz':
                with np.load(self.in_path) as data:
                    if dataset_points_key not in data:
                        raise KeyError(f"'.npz' 缺座標鍵值: {dataset_points_key}。現有: {list(data.keys())}")
                    
                    points = data[dataset_points_key]
                    
                    # 嘗試讀取法向量，若無則補零 (保持程式強健性)
                    if dataset_normals_key in data:
                        normals = data[dataset_normals_key]
                    else:
                        print(f"警告: .npz 檔中找不到 '{dataset_normals_key}'，將以零填充法向量。")
                        normals = np.zeros_like(points)

            # --- 讀取 .h5 檔案 ---
            elif ext == '.h5':
                with h5py.File(self.in_path, 'r') as hf:
                    if dataset_points_key not in hf:
                        raise KeyError(f"'.h5' 缺座標 Dataset: {dataset_points_key}。現有: {list(hf.keys())}")
                    
                    points = np.array(hf[dataset_points_key])
                    
                    if dataset_normals_key in hf:
                        normals = np.array(hf[dataset_normals_key])
                    else:
                        print(f"警告: .h5 檔中找不到 '{dataset_normals_key}'，將以零填充法向量。")
                        normals = np.zeros_like(points)

            # --- 讀取 .ply 檔案 ---
            elif ext == '.ply':
                # trimesh 載入 PLY 時，會自動解析 properties
                mesh = trimesh.load(self.in_path)
                
                # 確保有點資料
                if hasattr(mesh, 'vertices'):
                    points = np.array(mesh.vertices)
                else:
                    raise ValueError("讀取的 .ply 檔案不包含頂點 (vertices)。")

                # 處理法向量 (ply 載入後可能存在 vertex_normals 或需要計算)
                if hasattr(mesh, 'vertex_normals') and mesh.vertex_normals.shape == points.shape:
                    normals = np.array(mesh.vertex_normals)
                else:
                    # 如果 PLY 只有點沒有法向，trimesh 有時不會自動生成
                    print("警告: .ply 檔中無法解析出法向量，將以零填充。")
                    normals = np.zeros_like(points)

            else:
                raise ValueError(f"不支援的檔案格式: '{ext}'。僅支援 .npz, .h5, .ply")

        except Exception as e:
            print(f"讀取檔案 '{self.in_path}' 時發生錯誤: {e}")
            raise

        # --- 關鍵步驟：資料合併 ---
        # 檢查點與法向量數量是否一致
        if points.shape[0] != normals.shape[0]:
            raise ValueError(f"資料不匹配: 點數 ({points.shape[0]}) 與 法向量數 ({normals.shape[0]}) 不同。")

        # 合併成 (N, 6)
        # columns 0-2: x, y, z
        # columns 3-5: nx, ny, nz
        return np.hstack([points, normals])
    def PlottoCloud(self,coords,mode = 'open3D'):
        if mode == 'plt':
            fig = plt.figure()
            ax = fig.add_subplot(111, projection='3d')

            # 从坐标数组中提取 x, y, z
            x = coords[:, 0]
            y = coords[:, 1]
            z = coords[:, 2]

            # 绘制散点图
            ax.scatter(x, y, z, c='b', marker='o')

            # 设置标签
            ax.set_xlabel('X Label')
            ax.set_ylabel('Y Label')
            ax.set_zlabel('Z Label')

            plt.show()
        elif mode == 'open3D':
            pcd = o3d.geometry.PointCloud()
            # 将坐标数据设置为点云对象的点
            pcd.points = o3d.utility.Vector3dVector(coords)
            aabb = pcd.get_axis_aligned_bounding_box()
            axis_size = aabb.get_max_extent() / 10.0 # 座標軸大小 = 物件最大邊長的 1/10
            if axis_size < 0.01: # 避免點雲太小或只有一個點導致座標軸為 0
                axis_size = 1.0
            world_coordinate_frame = o3d.geometry.TriangleMesh.create_coordinate_frame(
                size=axis_size,  # 使用動態計算的大小
                origin=[0, 0, 0] # 將座標軸放在世界原點 (0,0,0)
            )
            o3d.visualization.draw_geometries([pcd,world_coordinate_frame],point_show_normal=True)
    def PlottoNormalCloud(self, data, mode='open3D'):
        """
        視覺化點雲資料。支援 Nx3 (僅座標) 或 Nx6 (座標+法向量) 格式。

        參數:
        data (numpy.ndarray): 點雲數據，形狀為 (N, 3) 或 (N, 6)。
                              如果是 (N, 6)，前三欄為 XYZ，後三欄為法向量 Nx Ny Nz。
        mode (str): 'plt' (Matplotlib) 或 'open3D' (Open3D)。
        """
        import numpy as np
        
        # --- 資料前處理：拆分座標與法向量 ---
        if data.shape[1] == 6:
            points = data[:, :3]
            normals = data[:, 3:]
            has_normals = True
        elif data.shape[1] == 3:
            points = data
            normals = None
            has_normals = False
        else:
            raise ValueError(f"不支援的資料形狀: {data.shape}。僅支援 Nx3 或 Nx6。")

        if mode == 'plt':
            import matplotlib.pyplot as plt
            
            fig = plt.figure()
            ax = fig.add_subplot(111, projection='3d')

            # 從座標陣列中提取 x, y, z
            x = points[:, 0]
            y = points[:, 1]
            z = points[:, 2]

            # 繪製散點圖
            ax.scatter(x, y, z, c='b', marker='.', s=1) # s=1 讓點小一點，看細節比較清楚

            # 若有法向量且點數不會太多，可選擇性繪製法向量 (這裡示範抽樣繪製，避免畫面太亂)
            # if has_normals:
            #     # 每 100 個點畫一條法線
            #     skip = 100 
            #     ax.quiver(x[::skip], y[::skip], z[::skip], 
            #               normals[::skip, 0], normals[::skip, 1], normals[::skip, 2], 
            #               length=0.1, color='r')

            # 設置標籤
            ax.set_xlabel('X')
            ax.set_ylabel('Y')
            ax.set_zlabel('Z')
            
            # 讓比例尺一致 (Matplotlib 預設 3D 比例尺通常會跑掉，這行很重要)
            try:
                ax.set_box_aspect([np.ptp(x), np.ptp(y), np.ptp(z)])
            except:
                pass # 舊版 matplotlib 可能不支援

            plt.show()

        elif mode == 'open3D':
            import open3d as o3d
            
            pcd = o3d.geometry.PointCloud()
            
            # 1. 設定點座標 (必須是 Nx3)
            pcd.points = o3d.utility.Vector3dVector(points)
            
            # 2. 設定法向量 (如果有 Nx6 資料)
            if has_normals:
                pcd.normals = o3d.utility.Vector3dVector(normals)
                # 確保法向量正規化 (Open3D 渲染需要)
                pcd.normalize_normals()
            
            # --- 視覺化設定 ---
            # 計算座標軸大小，避免太突兀
            aabb = pcd.get_axis_aligned_bounding_box()
            max_extent = aabb.get_max_extent()
            axis_size = max_extent / 10.0 if max_extent > 0 else 1.0
            if axis_size < 0.01: axis_size = 1.0
            
            world_coordinate_frame = o3d.geometry.TriangleMesh.create_coordinate_frame(
                size=axis_size, 
                origin=[0, 0, 0]
            )
            
            print(f"正在顯示點雲: {len(points)} 點" + (f", 含法向量" if has_normals else ""))
            print("提示: 按下 'N' 鍵可切換顯示/隱藏法向量，按下 'Ctrl + 9' 可切換視角。")
            
            # 顯示
            o3d.visualization.draw_geometries(
                [pcd, world_coordinate_frame],
                window_name="Normal Cloud Viewer",
                width=800,
                height=600,
                left=50,
                top=50,
                point_show_normal=has_normals # 只有在真的有法向量時才開啟
            )
    def STLtoDeep(self, camera_angles_list, image_width, image_height, radius, depth_range):
        """
        處理多組尤拉角並將所有深度圖儲存在一個手動指定的子資料夾中。
        
        :param camera_angles_list: 二維陣列，包含多組尤拉角 [[yaw1, pitch1, roll1], ...]
        :param image_width: 影像寬度
        :param image_height: 影像高度
        :param radius: 鏡頭與中心點距離
        :param depth_range: 深度值範圍
        :param subfolder_name: 要儲存這組深度圖的子資料夾名稱
        """
        
        # 1. 直接使用傳入的名稱組合出新的完整路徑
        sub_folder_path = self.out_path
        
        # 2. 確保該資料夾存在，如果不存在則建立它
        os.makedirs(sub_folder_path, exist_ok=True)
        print(f"所有檔案將儲存於: {sub_folder_path}")

        for idx, angles in enumerate(camera_angles_list):
            output_filename = f"depth_map_y{angles[0]}_p{angles[1]}_r{angles[2]}.png"
            output_path = os.path.join(sub_folder_path, output_filename)
            
            # 呼叫原始的深度轉換函數
            transform_Depth_2D.STL_Depth(
                self.in_path,
                output_path,
                angles,
                image_width,
                image_height,
                radius,
                depth_range
            )
            print(f"已生成深度圖: {output_filename}")
    def Cloudto2D(self, camera_angles_list, image_width, image_height, radius, depth_range):
            """
            處理多組尤拉角並將所有點雲視圖儲存在一個手動指定的子資料夾中。
            
            :param camera_angles_list: 二維陣列 [[yaw1, pitch1, roll1], ...]
            :param depth_range: 這裡作為 [min_intensity, max_intensity] 用於著色
            """
            
            # 1. 組合路徑
            sub_folder_path = self.out_path
            
            # 2. 確保該資料夾存在
            os.makedirs(sub_folder_path, exist_ok=True)
            print(f"所有檔案將儲存於: {sub_folder_path}")

            for idx, angles in enumerate(camera_angles_list):
                output_filename = f"view_y{angles[0]}_p{angles[1]}_r{angles[2]}.png"
                output_path = os.path.join(sub_folder_path, output_filename)
                
                # 呼叫上面的核心函式
                transform_Cloud_2D.Cloud_Heatmap_Render(
                    self.in_path,    # 支援 .npz, .ply, .pcd...
                    output_path,
                    angles,
                    image_width,
                    image_height,
                    radius,
                    depth_range
                )
                print(f"已生成視圖: {output_filename}")
class transform_Cloud_STL_2D:
    def __init__(self, cloud_path, stl_path, out_path):
        """
        初始化路徑設定
        :param cloud_path: 點雲檔案路徑 (.npz, .h5, .ply...)
        :param stl_path: STL 模型檔案路徑 (.stl)
        :param out_path: 圖片輸出的資料夾路徑
        """
        self.cloud_path = cloud_path  # 舊程式的 self.in_path 改名為此較明確
        self.stl_path = stl_path      # 新增 STL 路徑
        self.out_path = out_path

    def Cloudto2D(self, camera_angles_list, image_width, image_height, radius, depth_range):
        """
        處理多組尤拉角並將所有「點雲 + STL」混合視圖儲存在指定資料夾中。
        
        :param camera_angles_list: 二維陣列 [[yaw, pitch, roll], ...] (單位：度)
        :param depth_range: 點雲強度的熱力圖範圍 [min, max]
        """
        
        # 1. 組合與建立輸出資料夾
        sub_folder_path = self.out_path
        os.makedirs(sub_folder_path, exist_ok=True)
        print(f"所有檔案將儲存於: {sub_folder_path}")

        # 2. 批次渲染迴圈
        for idx, angles in enumerate(camera_angles_list):
            # 檔名包含角度資訊，方便辨識
            # 格式: view_y{Yaw}_p{Pitch}_r{Roll}.png
            output_filename = f"view_y{angles[0]}_p{angles[1]}_r{angles[2]}.png"
            output_fullpath = os.path.join(sub_folder_path, output_filename)
            
            print(f"正在處理 ({idx+1}/{len(camera_angles_list)}): {output_filename} ...")

            # 3. 呼叫核心混合渲染函式
            try:
                Render_Hybrid_Cloud_STL(
                    cloud_file=self.cloud_path,
                    stl_file=self.stl_path,
                    output_png=output_fullpath,
                    camera_angles=angles,
                    image_width=image_width,
                    image_height=image_height,
                    radius=radius,
                    depth_range=depth_range
                )
            except Exception as e:
                print(f" [Error] 生成 {output_filename} 失敗: {e}")

        print("批次轉換完成。")
class transform_Cloud_STL_2D_light:
    def __init__(self, cloud_path, stl_path, out_path):
        """
        初始化路徑設定
        :param cloud_path: 點雲檔案路徑 (.npz, .h5, .ply...)
        :param stl_path: STL 模型檔案路徑 (.stl)
        :param out_path: 圖片輸出的資料夾路徑
        """
        self.cloud_path = cloud_path  # 舊程式的 self.in_path 改名為此較明確
        self.stl_path = stl_path      # 新增 STL 路徑
        self.out_path = out_path

    def Cloudto2D(self, camera_angles_list, image_width, image_height, radius, depth_range):
        """
        處理多組尤拉角並將所有「點雲 + STL」混合視圖儲存在指定資料夾中。
        
        :param camera_angles_list: 二維陣列 [[yaw, pitch, roll], ...] (單位：度)
        :param depth_range: 點雲強度的熱力圖範圍 [min, max]
        """
        
        # 1. 組合與建立輸出資料夾
        sub_folder_path = self.out_path
        os.makedirs(sub_folder_path, exist_ok=True)
        print(f"所有檔案將儲存於: {sub_folder_path}")

        # 2. 批次渲染迴圈
        for idx, angles in enumerate(camera_angles_list):
            # 檔名包含角度資訊，方便辨識
            # 格式: view_y{Yaw}_p{Pitch}_r{Roll}.png
            output_filename = f"view_y{angles[0]}_p{angles[1]}_r{angles[2]}.png"
            output_fullpath = os.path.join(sub_folder_path, output_filename)
            
            print(f"正在處理 ({idx+1}/{len(camera_angles_list)}): {output_filename} ...")

            # 3. 呼叫核心混合渲染函式
            try:
                Render_Hybrid_Cloud_STL_li(
                    cloud_file=self.cloud_path,
                    stl_file=self.stl_path,
                    output_png=output_fullpath,
                    camera_angles=angles,
                    image_width=image_width,
                    image_height=image_height,
                    radius=radius,
                    depth_range=depth_range
                )
            except Exception as e:
                print(f" [Error] 生成 {output_filename} 失敗: {e}")

        print("批次轉換完成。")
class STL_Simplified:
    def __init__(self, in_path=None, out_path=None):
        self.in_path = in_path
        self.out_path = out_path

    # --- 核心工具：格式轉換 Helper ---
    def _numpy_to_o3d(self, vertices, faces):
        """將 numpy 陣列轉換為 Open3D TriangleMesh"""
        mesh = o3d.geometry.TriangleMesh()
        mesh.vertices = o3d.utility.Vector3dVector(vertices)
        mesh.triangles = o3d.utility.Vector3iVector(faces)
        mesh.compute_vertex_normals()
        return mesh

    def _o3d_to_numpy(self, mesh):
        """將 Open3D TriangleMesh 轉換回 numpy 陣列"""
        return np.array(mesh.vertices), np.array(mesh.triangles)

    def _numpy_to_trimesh(self, vertices, faces):
        """將 numpy 陣列轉換為 Trimesh 物件"""
        import trimesh
        return trimesh.Trimesh(vertices=vertices, faces=faces)

    # --- 1. 網格簡化 (LOD - Level of Detail) ---
    def simplify_mesh(self, vertices, faces, target_count=None, ratio=0.5):
        """
        使用二次誤差度量 (Quadric Decimation) 簡化網格。
        :param target_count: 目標面數 (int)，若設定則忽略 ratio。
        :param ratio: 縮減比例 (float, 0.0~1.0)，例如 0.1 代表剩下 10% 的面數。
        """
        print(f"--- 開始網格簡化 (LOD) --- 原面數: {len(faces)}")
        mesh_o3d = self._numpy_to_o3d(vertices, faces)
        
        if target_count is None:
            target_count = int(len(faces) * ratio)
            
        # 使用 Open3D 的簡化算法
        mesh_s = mesh_o3d.simplify_quadric_decimation(target_number_of_triangles=target_count)
        
        # 移除未參照的頂點與退化三角形
        mesh_s.remove_unreferenced_vertices()
        mesh_s.remove_degenerate_triangles()
        
        print(f"--- 簡化完成 --- 新面數: {len(mesh_s.triangles)}")
        return self._o3d_to_numpy(mesh_s)

    # --- 2. 拉普拉斯平滑 (Laplacian Smoothing) ---
    def smooth_mesh(self, vertices, faces, iterations=5, lambda_filter=0.5):
        """
        拉普拉斯平滑，用於去除噪聲並讓網格更圓滑。
        :param iterations: 迭代次數。
        :param lambda_filter: 平滑強度 (0~1)。
        """
        print(f"--- 開始拉普拉斯平滑 --- 迭代: {iterations}")
        mesh_o3d = self._numpy_to_o3d(vertices, faces)
        
        # filter_smooth_laplacian: 每個頂點移動到鄰居的平均位置
        mesh_smooth = mesh_o3d.filter_smooth_laplacian(number_of_iterations=iterations, lambda_filter=lambda_filter)
        mesh_smooth.compute_vertex_normals()
        
        return self._o3d_to_numpy(mesh_smooth)

    # --- 3. Alpha Shapes (包絡/緊密凸包) [修正版] ---
    def compute_alpha_shape(self, vertices, alpha=None):
        """
        [最強穩定版] 改用 alphashape 套件。
        解決 Open3D "invalid tetra" 崩潰問題。
        """
        import alphashape
        import trimesh
        import random
        
        print(f"--- [Alphashape Lib] 開始計算 (點數: {len(vertices)}) ---")

        # 1. 降採樣 (Downsample) - 這是加速的關鍵
        # alphashape 套件如果點數超過 10,000 會變慢
        # 我們隨機採樣 5000~10000 點來算輪廓就非常夠了，
        # 算出來的 Mesh 還是會包住整體，不用擔心
        if len(vertices) > 100000:
            indices = np.random.choice(len(vertices), 10000, replace=False)
            calc_vertices = vertices[indices]
        else:
            calc_vertices = vertices

        # 2. 自動決定 Alpha 值
        # 警告：千萬不要讓 alphashape.alphashape(points) 不帶參數自己算，那樣會算到天荒地老。
        if alpha is None:
            # 簡單估算：取 Bounding Box 對角線的 1/20 或 1/30
            # 或者用之前的「平均鄰近距離」
            bbox_min = np.min(calc_vertices, axis=0)
            bbox_max = np.max(calc_vertices, axis=0)
            diagonal = np.linalg.norm(bbox_max - bbox_min)
            
            # 經驗法則：對於鑄件，對角線的 3% ~ 5% 通常能包得很好
            # 值越小越貼合(易破)，值越大越像凸包
            alpha_value = 2.0 * (1.0 / (diagonal * 0.05)) 
            # alphashape 庫的 alpha 定義是 1/R (曲率)，所以要取倒數
            # 這裡我們簡化：直接嘗試傳入 0 (凸包) 到 N 的值
            # 為了避免混淆，我們這裡採用該套件建議的 "Alpha Parameter"
            # 若 alpha=0 為凸包。我們希望稍微緊一點。
            # 實測發現：直接給 0 (凸包) 速度最快，若要有凹陷特徵，需要調整
            
            # 【策略調整】為了這批次能跑完，我們先給一個寬鬆值
            # 如果你有具體的 alpha (例如 0.5)，請直接傳入
            # 這裡我們先給 0，讓他先跑出凸包，確保流程會過
            use_alpha = 0.0 
        else:
            # alphashape 套件的 alpha 值定義通常是 Open3D 的倒數或不同量級
            # 如果你傳入的是 Open3D 的 alpha (例如 3.0)，在這裡可能需要調整
            use_alpha = alpha

        try:
            # 3. 執行運算
            # 這裡回傳的是 trimesh 物件
            alpha_mesh = alphashape.alphashape(calc_vertices, use_alpha)
            
            # 檢查回傳類型 (有時候會回傳空的或 PointCloud)
            if isinstance(alpha_mesh, trimesh.Trimesh):
                # 成功生成網格
                if len(alpha_mesh.faces) > 0:
                    return alpha_mesh.vertices, alpha_mesh.faces
            
            print("[警告] Alphashape 生成失敗或面數為 0，退回 Convex Hull")
            # 失敗退回 Trimesh 內建凸包 (極快)
            mesh = trimesh.Trimesh(vertices=vertices)
            hull = mesh.convex_hull
            return hull.vertices, hull.faces

        except Exception as e:
            print(f"[錯誤] Alphashape 套件報錯: {e}，使用 Convex Hull 救援")
            try:
                mesh = trimesh.Trimesh(vertices=vertices)
                hull = mesh.convex_hull
                return hull.vertices, hull.faces
            except:
                return vertices, []
    # --- 4. V-HACD / 凸包 (結構塊) ---
    def compute_vhacd(self, vertices, faces, use_simple_hull=False):
        """
        計算 V-HACD (近似凸分解) 或 簡單凸包 (Convex Hull)。
        V-HACD 需要 trimesh 且系統需安裝 V-HACD 執行檔。
        :param use_simple_hull: 若為 True，僅計算單一凸包 (速度快)。
        """
        print("--- 計算結構塊 (Convex Decomposition/Hull) ---")
        mesh_tri = self._numpy_to_trimesh(vertices, faces)
        
        try:
            if use_simple_hull:
                # 簡單凸包 (Convex Hull)
                hull = mesh_tri.convex_hull
                return hull.vertices, hull.faces
            else:
                # V-HACD (將模型切分成多個凸塊)
                # 注意：這可能需要一段時間運算
                try:
                    import trimesh
                    decomposed = trimesh.decomposition.convex_decomposition(mesh_tri)
                    # decomposed 是一個 Scene 或 list of Trimesh
                    if isinstance(decomposed, trimesh.Scene):
                        # 如果是 Scene，將所有凸塊合併成一個網格回傳以供視覺化
                        combined = trimesh.util.concatenate(decomposed.dump())
                        return combined.vertices, combined.faces
                    elif isinstance(decomposed, list):
                        combined = trimesh.util.concatenate(decomposed)
                        return combined.vertices, combined.faces
                    else:
                        return decomposed.vertices, decomposed.faces
                except Exception as e:
                    print(f"V-HACD 執行失敗 (可能未安裝 backend): {e}")
                    print("退回使用簡單凸包 (Convex Hull)...")
                    hull = mesh_tri.convex_hull
                    return hull.vertices, hull.faces

        except Exception as e:
            print(f"結構塊計算錯誤: {e}")
            return vertices, faces

    # --- 原有功能 (保持不變或微調) ---
    def STLtoMesh(self):
        import trimesh
        mesh = trimesh.load(self.in_path)
        # 處理 Scene (如果載入的是多個物件的組合)
        if isinstance(mesh, trimesh.Scene):
             mesh = trimesh.util.concatenate(mesh.dump())
             
        vertices = mesh.vertices
        faces = mesh.faces

        if self.out_path:
            ext = os.path.splitext(self.out_path)[1].lower()
            out_dir = os.path.dirname(self.out_path)
            if out_dir: os.makedirs(out_dir, exist_ok=True) # 修正：若 out_dir 為空字串不報錯

            import tempfile
            fd, tmp_path = tempfile.mkstemp(prefix="mesh_", suffix=ext)
            os.close(fd)

            if ext == '.npz':
                np.savez(tmp_path, vertices=vertices, faces=faces)
            elif ext in ['.ply', '.obj']:
                mesh.export(tmp_path, file_type=ext[1:])
            elif ext == '.h5':
                with h5py.File(tmp_path, 'w') as hf:
                    hf.create_dataset('vertices', data=vertices)
                    hf.create_dataset('faces', data=faces)
            else:
                os.remove(tmp_path)
                raise ValueError(f"Unsupported file extension: {ext}")
            os.replace(tmp_path, self.out_path)

        return np.array(vertices), np.array(faces)

    def MeshtoSTL(self, vertices_array, faces_array):
        import trimesh
        new_mesh = trimesh.Trimesh(vertices=vertices_array, faces=faces_array)
        return new_mesh.export(self.out_path)

    def LoadMesh(self):
        if not os.path.exists(self.in_path):
            raise FileNotFoundError(f"檔案不存在: {self.in_path}")
        ext = os.path.splitext(self.in_path)[1].lower()
        vertices, faces = None, None
        
        try:
            if ext == '.npz':
                data = np.load(self.in_path)
                vertices, faces = data['vertices'], data['faces']
            elif ext == '.h5':
                with h5py.File(self.in_path, 'r') as hf:
                    vertices, faces = np.array(hf['vertices']), np.array(hf['faces'])
            elif ext in ['.ply', '.obj', '.stl']:
                import trimesh
                mesh = trimesh.load_mesh(self.in_path)
                if isinstance(mesh, trimesh.Scene): # 處理 Scene
                    mesh = trimesh.util.concatenate(mesh.dump())
                vertices, faces = np.array(mesh.vertices), np.array(mesh.faces)
            else:
                raise ValueError(f"不支援格式: {ext}")
        except Exception as e:
            print(f"讀取錯誤: {e}")
            raise
        return vertices, faces

    def PlottoMesh(self, vertices, faces, mode='open3D', vertex_colors=None, line_colors=None, window_name="Mesh Viewer"):
        if mode == 'plt':
            fig = plt.figure()
            ax = fig.add_subplot(111, projection='3d')
            mesh_collection = Poly3DCollection(vertices[faces], alpha=0.5, edgecolor='k')
            ax.add_collection3d(mesh_collection)
            ax.set_xlim(vertices[:, 0].min(), vertices[:, 0].max())
            ax.set_ylim(vertices[:, 1].min(), vertices[:, 1].max())
            ax.set_zlim(vertices[:, 2].min(), vertices[:, 2].max())
            plt.show()
            
        elif mode == 'open3D':
            mesh = o3d.geometry.TriangleMesh()
            mesh.vertices = o3d.utility.Vector3dVector(vertices)
            mesh.triangles = o3d.utility.Vector3iVector(faces)
            mesh.compute_vertex_normals()

            if vertex_colors is not None:
                mesh.vertex_colors = o3d.utility.Vector3dVector(vertex_colors)
            else:
                mesh.paint_uniform_color([0.7, 0.7, 0.7]) # 淺灰色

            lines = []
            for face in faces:
                lines.append([face[0], face[1]])
                lines.append([face[1], face[2]])
                lines.append([face[2], face[0]])
            line_set = o3d.geometry.LineSet()
            line_set.points = o3d.utility.Vector3dVector(vertices)
            line_set.lines = o3d.utility.Vector2iVector(lines)
            
            if line_colors is not None:
                line_set.colors = o3d.utility.Vector3dVector(line_colors)
            else:
                line_set.colors = o3d.utility.Vector3dVector([[0.0, 0.0, 0.0]] * len(lines))

            aabb = mesh.get_axis_aligned_bounding_box()
            axis_size = aabb.get_max_extent() / 10.0
            if axis_size < 0.01: axis_size = 1.0
            
            coord_frame = o3d.geometry.TriangleMesh.create_coordinate_frame(size=axis_size, origin=[0, 0, 0])
            
            print(f"顯示視窗: {window_name}")
            o3d.visualization.draw_geometries([mesh, line_set, coord_frame], window_name=window_name)

def voxel_grid_to_open3d(voxel_grid, min_vals, voxel_size):
    # 取得體素網格中的所有非零點
    coords = np.array(np.nonzero(voxel_grid)).T
    points = coords * voxel_size + min_vals

    # 創建點雲
    point_cloud = o3d.geometry.PointCloud()
    point_cloud.points = o3d.utility.Vector3dVector(points)

    # 使用 Open3D 進行體素化
    voxel_size = voxel_size
    voxel_grid_o3d = o3d.geometry.VoxelGrid.create_from_point_cloud(point_cloud, voxel_size)
    o3d.visualization.draw_geometries([voxel_grid_o3d])
def PonintCloud_FreeCAD(in_path,out_put = "out_put.stl"):
    result = subprocess.run([freecad_python_exe, SCRIPT_PATH_PointCloud_FreeCAD, in_path, out_put], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    #print(result.stdout)
    return json.loads(result.stdout)

def transform_Step_OCC(in_path, out_put):
    occ_result = subprocess.run(
        [
            occ_python_exe, SCRIPT_PATH_transform_OCC, 
            in_path, out_put
        ],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='cp950',  # 強制指定讀取繁體中文
    errors='replace'   # 讀不懂的字就跳過，不要報錯
    )

    print(occ_result.stdout)
    print(occ_result.stderr)
def transform_Step_OCCseg(in_path, out_put):
    occ_result = subprocess.run(
        [
            occ_python_exe, SCRIPT_PATH_transform_OCCseg, 
            in_path, out_put
        ],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8'
    )

    print(occ_result.stdout)
    print(occ_result.stderr)
def transform_Step_OCCsegre(in_path, in_out,out_put):
    occ_result = subprocess.run(
        [
            occ_python_exe, SCRIPT_PATH_transform_OCCsegre, 
            in_path, in_out,out_put
        ],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace'
    )

    print(occ_result.stdout)
    print(occ_result.stderr)
def transform_OCCstl(in_path, out_path, lin_deflection=0.1, ang_deflection=0.5):
    print(f"呼叫 OCC 轉檔: {in_path} -> {out_path}")
    
    occ_result = subprocess.run(
        [
            occ_python_exe, 
            SCRIPT_PATH_transform_OCCstl, 
            in_path, 
            out_path,
            str(lin_deflection), 
            str(ang_deflection)
        ],
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE, 
        text=True, 
        # ---------------------------------------------------------
        # 修改重點：Windows 繁體中文環境請改用 cp950
        # 加上 errors='replace' 確保就算遇到亂碼也不會讓程式崩潰
        # ---------------------------------------------------------
        encoding='cp950',   
        errors='replace'
    )

    print("--- 子程序輸出 ---")
    print(occ_result.stdout)
    if occ_result.stderr:
        print("--- 子程序錯誤/警告 ---")
        print(occ_result.stderr)

def transform_stlmerge(in_path,out_path):
    print(f"呼叫 OCC 轉檔: {in_path} -> {out_path}")
    
    occ_result = subprocess.run(
        [
            pyvista_python_exe, 
            SCRIPT_PATH_transform_stlmerge, 
            in_path, 
            out_path,
        ],
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE, 
        text=True, 
        # ---------------------------------------------------------
        # 修改重點：Windows 繁體中文環境請改用 cp950
        # 加上 errors='replace' 確保就算遇到亂碼也不會讓程式崩潰
        # ---------------------------------------------------------
        encoding='cp950',   
        errors='replace'
    )

    print("--- 子程序輸出 ---")
    print(occ_result.stdout)
    if occ_result.stderr:
        print("--- 子程序錯誤/警告 ---")
        print(occ_result.stderr)

def transform_3D(in_path, out_put="out_put.stl", Fvector=(0, 0, 0), Frotation=0, Fmoving=(0,0,0), tolerance=0.1, tessellate_value=0.1, do_align=False, align_target=(0,0,0)):
    
    # 假設這些環境變數定義在外部
    global freecad_python_exe, SCRIPT_PATH_transform_FreeCAD

    mode = os.path.splitext(out_put)[1].lower().lstrip('.')
    filename_without_extension = os.path.splitext(out_put)[0]

    Fvector_str = ",".join(map(str, Fvector))
    Fmoving_str = ",".join(map(str, Fmoving))
    
    # 確保新參數也轉成字串格式以供 subprocess 調用
    align_target_str = ",".join(map(str, align_target))
    do_align_str = str(do_align)

    result = subprocess.run(
        [
            freecad_python_exe, SCRIPT_PATH_transform_FreeCAD, 
            in_path, filename_without_extension, mode, 
            Fvector_str, str(Frotation), Fmoving_str, str(tolerance), str(tessellate_value),
            do_align_str, align_target_str # 加入對正參數
        ],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8'
    )

    print(result.stdout)
    if result.stderr:
        print(result.stderr)
def CloudtoSkl(in_path, out_folder, down_sample=0.01):
    """

    :param in_path: 輸入的點雲檔案 (ply, npz, h5 等)
    :param out_folder: 儲存骨架的資料夾
    :param down_sample: LBC 下採樣體素大小
    """

    # 確保 out_folder 存在 (雖然腳本內也有, 但提早建立是好習慣)
    os.makedirs(out_folder, exist_ok=True)

    # **關鍵**: 建立傳遞給 command line 的參數列表
    # 格式必須符合 skeletonize_pcd.py 的 main() 函數要求：
    # [python_exe, script_path, in_path, out_folder, down_sample]
    
    # 確保所有參數都是字串
    args = [
        pcskeletor_python_exe,
        SCRIPT_PATH_pcskeletor,
        in_path,
        out_folder,
        str(down_sample)  # 數字必須轉成字串
    ]

    print(f"  命令: {' '.join(args)}")

    # **修正**: 執行 subprocess
    result = subprocess.run(
        args,
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE, 
        text=True, 
        encoding='utf-8' # 保持與您一致的編碼設定
    )

    # --- 印出外部腳本的執行結果 ---
    print("--- 外部腳本 STDOUT ---")
    print(result.stdout)
    
    print("--- 外部腳本 STDERR ---")
    if result.stderr:
        print("偵測到錯誤:")
    print(result.stderr)
    
    return result
def Plot_to_pc_Skl(orig_path =None, skel_path =None, topo_path =None):
    """
    呼叫外部 Open3D 視覺化腳本。
    參數可以是路徑字串，若不顯示該項目則傳入 None。
    """
    
    # 1. 參數處理：確保 None 被轉換為字串 'None' 以保持參數順序位置
    # 邏輯：如果有路徑就用路徑，沒有(None或空字串)就填 'None'
    arg_orig = str(orig_path) if orig_path else 'None'
    arg_skel = str(skel_path) if skel_path else 'None'
    arg_topo = str(topo_path) if topo_path else 'None'

    # 2. 建立指令列表
    # 對應外部腳本順序: [Script] [Original] [Skeleton] [Topology]
    args = [
        pcskeletor_python_exe,
        SCRIPT_PATH_pcskeletor_visualize,
        arg_orig,
        arg_skel,
        arg_topo
    ]

    print(f"執行指令: {' '.join(args)}")

    # 3. 執行 subprocess
    try:
        result = subprocess.run(
            args,
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            encoding='utf-8'
        )

        # --- 印出外部腳本的執行結果 ---
        if result.stdout and result.stdout.strip():
            print("--- 外部腳本 STDOUT ---")
            print(result.stdout)
        
        if result.stderr and result.stderr.strip():
            print("--- 外部腳本 STDERR ---")
            print("偵測到錯誤或警告:")
            print(result.stderr)
        
    except Exception as e:
        print(f"執行 subprocess 時發生異常: {e}")

def MeshtoSkl(in_path, out_folder, contrast_factor=0.1,auto_simplify = False):
    transform_meshcskeletor.skeletonize_mesh(in_path, out_folder, contrast_factor,auto_simplify=auto_simplify)
def Plot_to_stl_Skl(mesh_path, swc_path):
    # 假設您將 visualize.py 命名為 transform_meshcskeletor_visualize.py
    import transform_meshcskeletor_visualize 
    
    # 錯誤的行 (刪除這行):
    # transform_meshcskeletor_visualize.main(mesh_path=mesh_path, swc_path=swc_path) 
    
    # 正確的行 (使用這行):
    # 呼叫我們剛剛在 visualize.py 中建立的新函數
    transform_meshcskeletor_visualize.visualize_files(mesh_path, swc_path)

def transform_moving_step(in_path_assembly, in_path_merged, out_path_assembly="out_assembly", out_path_merged="out_merged",
                           mode="step", Fvector=(0, 0, 1), Frotation=0):
    
    # **修正 1**: 確保 Fvector 是字串格式
    Fvector_str = ",".join(map(str, Fvector))
    #print(in_path_assembly)
    #print(in_path_merged)
    #print(out_path_assembly)
    #print(out_path_merged)
    # **修正 2**: 確保所有數值都是字串
    result = subprocess.run(
        [
            freecad_python_exe, SCRIPT_PATH_transform_moving, 
            in_path_assembly, in_path_merged, out_path_assembly, out_path_merged,
            mode, Fvector_str, str(Frotation)
        ],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8',errors='ignore'
    )

    print(result.stdout)
    print(result.stderr)
def transform_step_cloud(in_step, in_cloud, out_step, out_cloud,
                                Fvector=(0, 0, 1), Frotation=0, align_target=(0, 0, 0)):
    """
    呼叫外部 FreeCAD 腳本，執行單一 STEP 與 單一 Point Cloud 的同步變換。
    
    參數:
    - in_step: 輸入 STEP 檔案路徑
    - in_cloud: 輸入 點雲檔案路徑 (.npz, .ply...)
    - out_step: 輸出 STEP 檔案路徑
    - out_cloud: 輸出 點雲檔案路徑
    - Fvector: 旋轉軸 (tuple/list), 例如 (0, 0, 1)
    - Frotation: 旋轉角度 (float/int), 例如 90
    - align_target: 對正目標點 (tuple/list), 例如 (0, 0, 0)
    """

    # 1. 參數格式化：將 tuple/list 轉為 "x,y,z" 字串，數值轉為 str
    Fvector_str = ",".join(map(str, Fvector))
    align_target_str = ",".join(map(str, align_target))
    Frotation_str = str(Frotation)

    # 2. 構建命令列表
    # 順序必須嚴格對應 FreeCAD 腳本中 sys.argv 的順序：
    # argv[1]=in_step, argv[2]=in_cloud, argv[3]=out_step, argv[4]=out_cloud
    # argv[5]=Fvector, argv[6]=Frotation, argv[7]=align_target
    cmd = [
        freecad_python_exe,           # FreeCAD 的 Python 直譯器路徑
        SCRIPT_PATH_transform_step_cloud, # 你的 FreeCAD 腳本路徑 (.py)
        in_step,
        in_cloud,
        out_step,
        out_cloud,
        Fvector_str,
        Frotation_str,
        align_target_str
    ]

    print(f"--- Calling FreeCAD Script ---")
    print(f"Command: {' '.join(cmd)}") # 印出指令方便除錯

    # 3. 執行 Subprocess
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            # 改用 'cp950' (Windows 常見) 或增加 errors='replace' 防止崩潰
            encoding='cp950', 
            errors='replace', 
            check=True 
        )
        
        # 4. 輸出執行結果
        print("--- FreeCAD Output ---")
        print(result.stdout)
        
        if result.stderr:
            print("--- FreeCAD Warnings/Errors ---")
            print(result.stderr)
            
    except subprocess.CalledProcessError as e:
        print("!!! Error executing FreeCAD script !!!")
        print(f"Return Code: {e.returncode}")

        print("----- STDOUT -----")
        print(e.stdout)

        print("----- STDERR -----")
        print(e.stderr)

        raise

def PLYtoSTL(in_path,out_path):
        point_cloud = o3d.io.read_point_cloud(in_path)
        # 點雲預處理：下採樣
        point_cloud = point_cloud.voxel_down_sample(voxel_size=0.02)
        # 法線估計
        point_cloud.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30))
        # 进行泊松重建（Poisson reconstruction）
        mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(point_cloud, depth=9)
        # 去除低密度的部分
        vertices_to_remove = densities < np.quantile(densities, 0.01)
        mesh.remove_vertices_by_mask(vertices_to_remove)
        # 儲存重建的網格
        o3d.io.write_triangle_mesh(out_path, mesh)
        # 可視化重建的網格
        o3d.visualization.draw_geometries([mesh])
def read_ply(filename):
    pcd = o3d.io.read_point_cloud(filename)
    points = np.asarray(pcd.points)
    return points

def test_FreeCAD(in_put,out_put = "out_put",mode  = "stl"):
    result = subprocess.run([freecad_python_exe, SCRIPT_PATH_test_FreeCAD, in_put, out_put,mode], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,encoding='utf-8')
    print(result.stdout)
    print(result.stderr)

def reconstruct_and_save_ply(points, output_filename):
    # 創建 PointCloud 對象
    pcd_new = o3d.geometry.PointCloud()

    # 設置點雲坐標
    pcd_new.points = o3d.utility.Vector3dVector(points)

    # 保存為 ply 文件
    o3d.io.write_point_cloud(output_filename, pcd_new)

def STEPto2D(
    step_file,        
    output_folder,   
    camera_angles,   
    image_width,
    image_height,
    zoom_factor=0.8
):
    if not os.path.exists(step_file):
        return

    # 1. 準備參數
    angles_str_list = [f"{ang[0]},{ang[1]},{ang[2]}" for ang in camera_angles]
    final_angles_arg = ";".join(angles_str_list)

    cmd = [
        freecad_python_exe, 
        SCRIPT_PATH_transform_Step_2D,
        step_file,
        output_folder, 
        str(image_width),
        str(image_height),
        str(zoom_factor),
        final_angles_arg
    ]

    # 【修正】保留 STARTUPINFO 設定 (雙重保險)
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE

    # 【新增】最強力的隱藏參數
    # 0x08000000 是 CREATE_NO_WINDOW 的代碼
    CREATE_NO_WINDOW = 0x08000000

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            encoding='cp950', 
            errors='replace',
            startupinfo=startupinfo,    # 方法 1
            creationflags=CREATE_NO_WINDOW, # 方法 2 (最強)
            check=False 
        )
        
        if result.returncode != 0:
            print(f"[FreeCAD Error] {os.path.basename(step_file)}:\n{result.stderr}")

    except Exception as e:
        print(f"呼叫失敗: {e}")
"""

stl_data = STL_DATA('10712448 assembly2.stl')
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
#o = STL_DATA('./test_file/10712448 assembly2.stl',"./test_file/10712448 assembly2").STLtoDeep(six_views,1024,1024,128,[0.2,1024] )

#transform_3D("10730888 assembly.step","10730888 assembly m.stl",Fvector=(0, 0, 0), Frotation=0,Fmoving = (0,0,0), tolerance=0.1, tessellate_value=0.1)
#transform_3D("10730888 assembly.step","10730888 assembly.stl",Fvector=(0,0,1),Frotation=180)
#transform_3D("10730888 assembly m.step","10730888 assembly m.stl",Fvector=(0,0,1),Frotation=180)
#transform_Step_OCC("20446701D assembly.step","20446701D assembly m.step")
#transform_moving_step("10730888 assembly.step","10730888 assembly m.step","10730888 assembly test.step","10730888 assenbly m test.step")
#a , c = STL_DATA("10712448 assembly.stl").STLtoMesh()
#s, n , k  = STL_DATA("10712448 assembly.stl").STLtoVoxel()
#print(a,c)
#STL_DATA().PlotMesh(a,c)
#STL_DATA().PlottoVoxel(s,n,k)

# 检查返回码

#網格簡化 (LOD)
#V-HACD 結構塊 
#Alpha Shapes 包絡(凸包)
#拉普拉絲平滑