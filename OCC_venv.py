import subprocess
import sys
import os
from pathlib import Path

class OCCHybridEnvCreate:
    def __init__(self, venv_path, 
                 python_version="3.10", 
                 conda_packages=["pythonocc-core=7.8.1.1",  "numpy"],
                 pip_packages=["open3d"]):
        
        self.venv_path = str(Path(venv_path).resolve())
        self.python_version = python_version
        self.conda_packages = conda_packages
        self.pip_packages = pip_packages
        self._python_executable = None

    def setup(self):
        """執行完整的環境設定"""
        self.create_conda_environment()
        self.install_conda_packages()
        self.install_pip_packages() # 新增 pip 安裝步驟

    def create_conda_environment(self):
        """建立 Conda 環境 (與您原始腳本相同)"""
        print(f"檢查 Conda 環境於: {self.venv_path}")
        if not os.path.isdir(self.venv_path):
            print(f"環境不存在，開始建立...")
            command = [
                "conda", "create", "--prefix", self.venv_path,
                f"python={self.python_version}", "-y"
            ]
            result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
            if result.returncode != 0:
                print("錯誤：建立 Conda 環境失敗！")
                print(result.stderr)
                raise RuntimeError("Failed to create conda environment!")
            print("Conda 環境建立成功。")
        else:
            print(f"Conda 環境已存在。")

    def install_conda_packages(self):
        """使用 Conda 安裝指定的套件"""
        for package in self.conda_packages:
            package_name = package.split("=")[0]
            list_command = ["conda", "list", "--prefix", self.venv_path]
            result = subprocess.run(list_command, capture_output=True, text=True, encoding='utf-8')
            
            if package_name not in result.stdout:
                print(f"正在使用 Conda 安裝套件 {package}...")
                install_command = [
                    "conda", "install", "--prefix", self.venv_path,
                    "-c", "conda-forge", package, "-y"
                ]
                result = subprocess.run(install_command, capture_output=True, text=True, encoding='utf-8')
                if result.returncode != 0:
                    print(f"錯誤：Conda 安裝套件 {package} 失敗！")
                    print(result.stderr)
                    sys.exit(1)
            else:
                print(f"Conda 套件 {package_name} 已安裝。")

    def install_pip_packages(self):
        """
        使用環境中的 Pip 來安裝額外的套件
        """
        python_exe = self.get_python_executable()

        # 首先，升級 Pip
        print("正在升級 Pip...")
        upgrade_command = [python_exe, "-m", "pip", "install", "--upgrade", "pip"]
        result = subprocess.run(upgrade_command, capture_output=True, text=True, encoding='utf-8')
        if result.returncode != 0:
            print("警告：升級 Pip 失敗，但仍會繼續嘗試安裝套件。")
            print(result.stderr)

        # 然後，安裝 Pip 套件
        for package in self.pip_packages:
            # 這裡使用 pip list 來檢查
            list_command = [python_exe, "-m", "pip", "list"]
            result = subprocess.run(list_command, capture_output=True, text=True, encoding='utf-8')
            
            # 稍微改進檢查方式，避免 "numpy" 匹配到 "minumpy" 等
            # 檢查 "package_name==" 或 "package_name "
            package_name_check = package.split("=")[0].lower()
            is_installed = any(
                line.lower().startswith(package_name_check + " ") or \
                line.lower().startswith(package_name_check + "=") \
                for line in result.stdout.splitlines()
            )

            if not is_installed:
                print(f"正在使用 Pip 安裝套件 {package}...")
                
                # --- 這就是關鍵的修正 ---
                # 加入 --no-build-isolation 參數
                # 解決 "ModuleNotFoundError: No module named 'numpy'" 的問題
                install_command = [
                    python_exe, "-m", "pip", "install",
                    "--no-build-isolation",  # 保留這個，解決 numpy 問題
                    package
                ]

                # --- 這是關鍵的修正 ---
                # 取得當前的環境變數
                env = os.environ.copy()
                # 設定 PYTHONUTF8=1 來強制 Python 使用 UTF-8 編碼
                env["PYTHONUTF8"] = "1"
                # ------------------------

                result = subprocess.run(
                    install_command, 
                    capture_output=True, 
                    text=True, 
                    encoding='utf-8', # 這裡的 encoding 是用來解讀 stdout/stderr
                    env=env             # 這裡的 env 才是傳給子進程的環境
                )
                
                if result.returncode != 0:
                    print(f"錯誤：Pip 安裝套件 {package} 失敗！")
                    print(result.stderr)
                    sys.exit(1)
                else:
                    print(f"Pip 套件 {package} 安裝成功。")
            else:
                print(f"Pip 套件 {package} 已安裝。")
    def get_python_executable(self):
        """取得此 Conda 環境中的 Python 解譯器路徑 (與您原始腳本相同)"""
        if self._python_executable:
            return self._python_executable

        if sys.platform == "win32":
            py_path = Path(self.venv_path) / "python.exe"
        else:
            py_path = Path(self.venv_path) / "bin" / "python"
        
        if not py_path.is_file():
            # 再次檢查，因為 Conda 有時會延遲建立
            if (Path(self.venv_path) / "Scripts" / "python.exe").is_file():
                 py_path = Path(self.venv_path) / "Scripts" / "python.exe"
            else:
                 raise FileNotFoundError(f"在環境中找不到 Python 解譯器: {py_path}")

        self._python_executable = str(py_path)
        return self._python_executable
"""
# --- 如何使用 ---
if __name__ == "__main__":
    # 建立一個名為 "my_occ_env" 的 Conda 環境
    env_manager = OCCHybridEnvCreate("./my_occ_env")
    
    try:
        env_manager.setup()
        print("\n混合環境設定完成！")
        
        python_path = env_manager.get_python_executable()
        print(f"Python 解譯器位於: {python_path}")
        
    except (RuntimeError, FileNotFoundError
"""