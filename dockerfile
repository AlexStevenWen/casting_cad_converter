# Dockerfile for Windows Containers (Final Version)

# 1. 選擇一個功能更完整的 Windows 基礎映像檔。
# 這會包含大部分系統 DLL，能更好地支援複雜的函式庫。
FROM mcr.microsoft.com/windows/server:ltsc2022

# 2. (仍然建議) 安裝最新的 VC++ Redistributable，以確保執行時期版本正確。
SHELL ["powershell", "-Command", "$ErrorActionPreference = 'Stop';"]
ADD https://aka.ms/vs/17/release/vc_redist.x64.exe /vc_redist.x64.exe
RUN Start-Process -FilePath C:\\vc_redist.x64.exe -ArgumentList '/install', '/passive', '/norestart' -Wait; ` \
    Remove-Item C:\\vc_redist.x64.exe

# 3. 設定工作目錄並切換到 PowerShell。
WORKDIR C:\\app
SHELL ["powershell", "-Command", "$ErrorActionPreference = 'Stop'; $ProgressPreference = 'SilentlyContinue';"]

# 4. 安裝 Miniconda。
RUN Invoke-WebRequest -Uri https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe -OutFile Miniconda3.exe; \
    Start-Process -FilePath Miniconda3.exe -ArgumentList '/S', '/D=C:\Miniconda3' -Wait; \
    Remove-Item Miniconda3.exe

# 5. 將 Miniconda 的路徑加入到環境變數 PATH 中。
RUN $newPath = ('C:\Miniconda3\Scripts', 'C:\Miniconda3\Library\bin', [Environment]::GetEnvironmentVariable('PATH', 'Machine')) -join ';'; \
    [Environment]::SetEnvironmentVariable('PATH', $newPath, 'Machine');

# 6. 接受 Anaconda 的服務條款 (ToS)。
RUN conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main; \
    conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r; \
    conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/msys2

# 7. 複製您的 Conda 環境定義檔。
COPY cad_converter_env.yml .

# 8. 根據 yml 檔案建立 Conda 環境。
RUN conda env create -f cad_converter_env.yml

# 9. 將您的專案程式碼複製到工作目錄中。
COPY . .

# 10. 設定 ENTRYPOINT，確保所有命令都在正確的 Conda 環境中執行。
ENTRYPOINT ["conda", "run", "-n", "cad_converter", "--no-capture-output"]