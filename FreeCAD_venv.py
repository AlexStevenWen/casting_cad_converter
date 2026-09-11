import subprocess
import os
import glob

class FreeCADvenvCreate():
    def __init__(self, 
                 FREECAD_BASE_PATH = r"C:\Program Files", 
                 VENV_PATH = r"C:\Users\User\Desktop\Research\AI Model\Casting Model\FreeCADvenv",
                 REQUIRED_PACKAGE =["numpy", "pandas","matplotlib"],
                 PREFERRED_VERSION_STR = None): # <-- 新增參數
        
        self.FREECAD_BASE_PATH = FREECAD_BASE_PATH
        self.VENV_PATH = VENV_PATH
        self.REQUIRED_PACKAGE = REQUIRED_PACKAGE
        self.PREFERRED_VERSION_STR = PREFERRED_VERSION_STR # <-- 新增屬性

        # 尋找 FreeCAD 版本目錄
        self.FREECAD_DIR = self.find_freecad_directory()
        if not self.FREECAD_DIR:
             raise FileNotFoundError(f"No suitable FreeCAD installation found in {self.FREECAD_BASE_PATH}")

        print(f"--- Using FreeCAD installation: {self.FREECAD_DIR} ---")
        
        # 找尋 FreeCAD 的 Python 是否存在
        self.FREECAD_PYTHON = self.get_freecad_python()
        # 檢查或創造虛擬環如果不存在
        self.create_virtual_environment()
        # 激活虛擬環境 (註：你的 activate_virtual_environment 其實沒有真的 'activate'，
        # 只是設定了 venv_python 的路徑，這在 install_required_packages 中是正確的)
        self.activate_virtual_environment() 
        # 檢查並安裝package
        self.install_required_packages()

    def find_freecad_directory(self):
        search_pattern = os.path.join(self.FREECAD_BASE_PATH, "FreeCAD*")
        freecad_dirs = glob.glob(search_pattern)
        
        if not freecad_dirs:
            return None # 找不到任何 FreeCAD

        # 1. 檢查是否有指定偏好的版本
        if self.PREFERRED_VERSION_STR:
            # 嘗試尋找名稱完全符合的資料夾
            preferred_path_exact = os.path.join(self.FREECAD_BASE_PATH, self.PREFERRED_VERSION_STR)
            if preferred_path_exact in freecad_dirs:
                print(f"Found preferred exact match: {preferred_path_exact}")
                return preferred_path_exact
            
            # 嘗試尋找資料夾名稱包含偏好字串的
            for path in freecad_dirs:
                # os.path.basename(path) 會取得資料夾名稱 (例如 "FreeCAD 0.21")
                if self.PREFERRED_VERSION_STR in os.path.basename(path):
                    print(f"Found preferred partial match: {path}")
                    return path
            
            # 如果指定了偏好版本但沒找到，發出警告並繼續執行下一步
            print(f"Warning: Preferred version '{self.PREFERRED_VERSION_STR}' not found. Falling back to latest.")

        # 2. 如果沒有指定偏好，或偏好的沒找到，則回傳排序後的"最新"版本
        # 透過 sort() 排序，"FreeCAD 0.21" 會在 "FreeCAD 0.20" 之後
        freecad_dirs.sort()
        latest_version_path = freecad_dirs[-1] # 取最後一個
        print(f"No preferred version specified or found. Using latest version: {latest_version_path}")
        return latest_version_path

    def get_freecad_python(self):
        # ... (以下不變) ...
        freecad_python = os.path.join(self.FREECAD_DIR, "bin", "python.exe")
        if not os.path.exists(freecad_python):
            raise FileNotFoundError(f"FreeCAD Python not found at {freecad_python}!")
        return freecad_python

    def create_virtual_environment(self):
        if not os.path.exists(self.VENV_PATH):
            print("Creating virtual environment...")
            result = subprocess.run([self.FREECAD_PYTHON, "-m", "venv", self.VENV_PATH], capture_output=True,
                                    text=True)
            if result.returncode != 0:
                print("Error Output:", result.stderr)
                raise RuntimeError("Failed to create virtual environment!")
        else:
            print("Virtual environment already exists.")

    def activate_virtual_environment(self):
        self.activate_script = os.path.join(self.VENV_PATH, "Scripts", "python.exe")
        print(f"Virtual environment Python executable: {self.activate_script}")
        if not os.path.exists(self.activate_script):
            print("Virtual environment activation script not found!")
            exit(1)


    def install_required_packages(self):
        venv_python = os.path.join(self.VENV_PATH, "Scripts", "python.exe")
        for package in self.REQUIRED_PACKAGE:
            result = subprocess.run([venv_python, "-m", "pip", "show", package], capture_output=True, text=True)
            if result.returncode != 0:  # 如果包未安装
                print(f"Installing package {package}...")
                result = subprocess.run([venv_python, "-m", "pip", "install", package], capture_output=True,
                                        text=True)
                if result.returncode != 0:
                    print(f"Failed to install package {package}!")
                    print(result.stderr)
                    exit(1)
            else:
                print(f"Package {package} is already installed.")