import os
import subprocess
def find_folder_in_program_files(foldername):
    # 定义搜索路径，只包括 D:\ 和 C:\Program Files
    directories = [
    'C:\\', os.path.join('C:', 'Program Files'),
    'D:\\', os.path.join('D:', 'Program Files'),
    'E:\\', os.path.join('E:', 'Program Files'),
    'F:\\', os.path.join('F:', 'Program Files'),
    'G:\\', os.path.join('G:', 'Program Files'),
    'H:\\', os.path.join('H:', 'Program Files'),
    'I:\\', os.path.join('I:', 'Program Files'),
    'J:\\', os.path.join('J:', 'Program Files'),
    'K:\\', os.path.join('K:', 'Program Files')
]
    for directory in directories:
        for root, dirs, files in os.walk(directory, topdown=True):
            for dir_name in dirs:
                full_path = os.path.join(root, dir_name)
                if dir_name == foldername:
                    return full_path
            # 如果在当前目录层级已经找到，则不再继续深入搜索
            #dirs.clear()
    return None
def FreeCADexe():
    freecad_versions = ["FreeCAD 1.0","FreeCAD 0.21"]
    for version in freecad_versions:
        file_path = find_folder_in_program_files(version)
        if file_path:
            print(f'找到資料夾: {file_path} 對應版本: {version}')
            # 如果找到一个版本就可以退出循环，如果只需找到一个版本
            return file_path
        else:
            print(f'未找到文件夹: {version}',"自動運行安裝")
            command = 'powershell Start-Process "FreeCAD_1.0.0-conda-Windows-x86_64-installer-1.exe" -ArgumentList "arg1", "arg2" -Verb RunAs'
            # 执行命令
            subprocess.run(command, shell=True)
def ChynWangPojectpy():
    file_path = find_folder_in_program_files("ChynWangProject")
    if file_path:
        #print(f'找到資料夾: {file_path}')
        return file_path
    else:
        print(f'未找到文件夹', "自動運行安裝")
#def ChynWangDatapy():
def ChynWangDatapy():
    file_path = find_folder_in_program_files("ChynWangData")
    if file_path:
        #print(f'找到資料夾: {file_path}')
        return file_path
    else:
        print(f'未找到文件夹', "自動運行安裝")
#def ChynWangDatapy():
