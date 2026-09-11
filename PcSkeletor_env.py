import subprocess
import sys
import os
from pathlib import Path

class PcSkeletorEnvCreate:
    
    # 1. __init__ (已修改：加入 python_version)
    def __init__(self, 
                 venv_path,
                 python_version="3.10",
                 # ⭐️ 修改這裡：新增 imageio, shapely, trimesh
                 pre_install_packages=[
                     "open3d", "h5py", "scipy", "networkx", 
                     "tqdm", "numpy", "matplotlib", "scikit-learn",
                     "robust_laplacian", "pot", 
                     "imageio", "shapely", "trimesh"
                 ],
                 mistree_package="mistree>=2.0",
                 main_package="pc-skeletor"
                ):
        self.venv_path = str(Path(venv_path).resolve())
        self.python_version = python_version
        self.pre_install_packages = pre_install_packages
        self.mistree_package = mistree_package
        self.main_package = main_package
        self._python_executable = None
        # 不再需要 self.base_python

    def create(self):
        print(f"--- Starting pc-skeletor conda env creation process at: {self.venv_path} ---")
        
        # 步驟 1: 建立 conda 環境
        self.create_conda_env() # ⭐️ 已改名
        
        # 步驟 2: 安裝 Pip 套件
        self.install_pip_packages()
        
        print(f"--- Successfully created and configured conda env at: {self.venv_path} ---")


    # 2. (輔助函式) create_conda_env (已修改：使用 conda)
    def create_conda_env(self):
        """
        使用 'conda' 建立指定 Python 版本的虛擬環境。
        """
        print(f"Checking conda environment at: {self.venv_path}")
        # ⭐️ 檢查 conda env 是否存在的更可靠方法是檢查 python.exe
        py_exe_path = self.get_python_path_for_check() 

        if not py_exe_path.is_file():
            print(f"Environment not found, creating using 'conda' with Python {self.python_version}...")
            
            # 使用 -p (prefix) 在指定路徑建立環境
            command = [
                "conda", "create", "-p", self.venv_path, f"python={self.python_version}", "-y"
            ]
            
            # 注意：執行 conda 指令可能需要 shell=True
            result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', shell=True)
            if result.returncode != 0:
                print("ERROR: Failed to create conda environment!")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                raise RuntimeError("Failed to create conda environment!")
            print("Conda environment created successfully.")
        
        else:
            print(f"Conda environment already exists.")


    def install_pip_packages(self):
            """
            在此 conda 環境中安裝所有必要的 pip 套件。
            (已修正：加入 PYTHONUTF8 環境變數，並針對 pc-skeletor 使用 --no-deps)
            """
            print("Installing pip packages into conda environment...")
            
            # 1. 取得此環境的 Python 解譯器路徑
            python_exe = self.get_python_executable()
            
            # 2. 準備環境變數
            env = os.environ.copy()
            # ⭐️ 修正 1: 強制 Python 使用 UTF-8 模式，解決 Windows 讀取 setup.py 的編碼錯誤
            env["PYTHONUTF8"] = "1"
            
            # 3. 組合所有要安裝的套件
            packages_to_install = []
            
            if self.pre_install_packages:
                packages_to_install.extend(self.pre_install_packages)
                
            if self.mistree_package:
                packages_to_install.append(self.mistree_package)
                
            if self.main_package:
                packages_to_install.append(self.main_package)

            if not packages_to_install:
                print("No pip packages specified for installation.")
                return

            print(f"Packages to install: {', '.join(packages_to_install)}")

            # 4. 逐一執行 pip install
            for package_name in packages_to_install:
                print(f"Installing {package_name}...")
                
                command = [
                    python_exe, "-m", "pip", "install", 
                    "--no-cache-dir"
                ]

                # ⭐️ 修正 2: 針對 'pc-skeletor' 加入 --no-deps
                # 原因：pc-skeletor 強制要求舊版 mistree==1.2.0，會導致編碼錯誤且覆蓋我們已裝好的新版。
                # 加上此參數後，pip 會忽略依賴檢查，直接使用我們已經裝好的 mistree >= 2.0。
                if "pc-skeletor" in package_name:
                    print(f"Note: Installing {package_name} with --no-deps to avoid dependency conflicts.")
                    command.append("--no-deps")

                command.append(package_name)
                
                # 執行指令
                result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', env=env)
                
                if result.returncode != 0:
                    print(f"ERROR: Failed to install package: {package_name}")
                    print("STDOUT:", result.stdout)
                    print("STDERR:", result.stderr)
                    # 這裡建議讓它報錯停止，以免後續執行出問題
                    raise RuntimeError(f"Failed to install {package_name}")
                else:
                    print(f"Successfully installed {package_name}.")

            print("All pip packages installed successfully.")

    # ⭐️ 內部輔助函式，僅供 create_conda_env 檢查用
    def get_python_path_for_check(self):
        if sys.platform == "win32":
            return Path(self.venv_path) / "python.exe"
        else:
            return Path(self.venv_path) / "bin" / "python"


    # 3. get_python_executable (已修改：Conda 路徑)
    def get_python_executable(self):
        """取得此 conda 環境中的 Python 解譯器路徑"""
        if self._python_executable:
            return self._python_executable

        # ⭐️ Conda 的路徑結構更簡單
        if sys.platform == "win32":
            py_path = Path(self.venv_path) / "python.exe"
        else:
            py_path = Path(self.venv_path) / "bin" / "python"
        
        if not py_path.is_file():
            raise FileNotFoundError(f"Python executable not found in conda env: {py_path}")

        self._python_executable = str(py_path.resolve())
        print(f"Conda environment Python executable: {self._python_executable}")
        return self._python_executable

