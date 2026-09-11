import subprocess
import sys
import os
from pathlib import Path

class pyvistaEnvCreate:
    
    def __init__(self, 
                 venv_path,
                 python_version="3.10",
                 packages_to_install=[
                     "numpy", 
                     "trimesh", 
                     "pyvista",
                     "scipy",
                     "networkx"
                 ]):
        self.venv_path = str(Path(venv_path).resolve())
        self.python_version = python_version
        self.packages_to_install = packages_to_install
        self._python_executable = None

    def create(self):
        print(f"--- Starting PyVista conda env creation process at: {self.venv_path} ---")
        
        # 步驟 1: 建立 conda 環境
        self.create_conda_env()
        
        # 步驟 2: 安裝 Pip 套件 (numpy, trimesh, pyvista)
        self.install_pip_packages()
        
        print(f"--- Successfully created and configured conda env at: {self.venv_path} ---")

    def create_conda_env(self):
        """
        使用 'conda' 建立指定 Python 版本的虛擬環境。
        """
        print(f"Checking conda environment at: {self.venv_path}")
        py_exe_path = self.get_python_path_for_check() 

        if not py_exe_path.is_file():
            print(f"Environment not found, creating using 'conda' with Python {self.python_version}...")
            
            # 使用 -p (prefix) 在指定路徑建立環境
            command = [
                "conda", "create", "-p", self.venv_path, f"python={self.python_version}", "-y"
            ]
            
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
            在此 conda 環境中安裝必要的 pip 套件。
            """
            print("Installing pip packages into conda environment...")
            
            # 1. 取得此環境的 Python 解譯器路徑
            python_exe = self.get_python_executable()
            
            # 2. 準備環境變數 (保持 UTF-8 設定以防 Windows 編碼問題)
            env = os.environ.copy()
            env["PYTHONUTF8"] = "1"
            
            if not self.packages_to_install:
                print("No pip packages specified for installation.")
                return

            print(f"Packages to install: {', '.join(self.packages_to_install)}")

            # 3. 逐一執行 pip install
            for package_name in self.packages_to_install:
                print(f"Installing {package_name}...")
                
                # 基本安裝指令
                command = [
                    python_exe, "-m", "pip", "install", 
                    "--no-cache-dir",
                    package_name
                ]

                # 執行指令
                result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', env=env)
                
                if result.returncode != 0:
                    print(f"ERROR: Failed to install package: {package_name}")
                    print("STDOUT:", result.stdout)
                    print("STDERR:", result.stderr)
                    raise RuntimeError(f"Failed to install {package_name}")
                else:
                    print(f"Successfully installed {package_name}.")

            print("All pip packages installed successfully.")

    # 內部輔助函式，僅供 create_conda_env 檢查用
    def get_python_path_for_check(self):
        if sys.platform == "win32":
            return Path(self.venv_path) / "python.exe"
        else:
            return Path(self.venv_path) / "bin" / "python"

    def get_python_executable(self):
        """取得此 conda 環境中的 Python 解譯器路徑"""
        if self._python_executable:
            return self._python_executable

        if sys.platform == "win32":
            py_path = Path(self.venv_path) / "python.exe"
        else:
            py_path = Path(self.venv_path) / "bin" / "python"
        
        if not py_path.is_file():
            raise FileNotFoundError(f"Python executable not found in conda env: {py_path}")

        self._python_executable = str(py_path.resolve())
        return self._python_executable