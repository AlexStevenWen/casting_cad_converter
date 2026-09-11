# 檔案：OCC_venv.py

import subprocess
import sys
import os
from pathlib import Path

class OCCVenvCreate:
    def __init__(self, venv_path, python_version="3.10", required_packages=["pythonocc-core=7.8.1.1","open3d","numpy"]):
        self.venv_path = str(Path(venv_path).resolve())
        self.python_version = python_version
        self.required_packages = required_packages
        self._python_executable = None

    def setup(self):
        self.create_conda_environment()
        self.install_required_packages()

    def create_conda_environment(self):
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

    def install_required_packages(self):
        for package in self.required_packages:
            package_name = package.split("=")[0]
            list_command = ["conda", "list", "--prefix", self.venv_path]
            result = subprocess.run(list_command, capture_output=True, text=True, encoding='utf-8')
            
            if package_name not in result.stdout:
                print(f"正在安裝套件 {package}...")
                install_command = [
                    "conda", "install", "--prefix", self.venv_path,
                    "-c", "conda-forge", package, "-y"
                ]
                result = subprocess.run(install_command, capture_output=True, text=True, encoding='utf-8')
                if result.returncode != 0:
                    print(f"錯誤：安裝套件 {package} 失敗！")
                    print(result.stderr)
                    sys.exit(1)
            else:
                print(f"套件 {package_name} 已安裝。")

    def get_python_executable(self):
        if self._python_executable:
            return self._python_executable

        if sys.platform == "win32":
            py_path = Path(self.venv_path) / "python.exe"
        else:
            py_path = Path(self.venv_path) / "bin" / "python"
        
        if not py_path.is_file():
            raise FileNotFoundError(f"在環境中找不到 Python 解譯器: {py_path}")

        self._python_executable = str(py_path)
        return self._python_executable