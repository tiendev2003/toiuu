@echo off
REM fresh_install_windows.bat - Cài đặt hoàn chỉnh cho Windows

echo ================================================
echo    PHOTOBOOTH APP - FRESH INSTALLATION
echo ================================================
echo This script will install everything needed for PhotoboothApp on Windows
echo.

REM Kiểm tra quyền admin
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ This script requires Administrator privileges
    echo Please run as Administrator
    pause
    exit /b 1
)

echo ✅ Running with Administrator privileges
echo.

REM Kiểm tra Windows version
echo 1️⃣ Checking Windows version...
for /f "tokens=4-5 delims=. " %%i in ('ver') do set VERSION=%%i.%%j
echo ✅ Windows version: %VERSION%
echo.

REM Cài đặt Chocolatey (package manager cho Windows)
echo 2️⃣ Installing Chocolatey (Windows Package Manager)...
where choco >nul 2>&1
if %errorLevel% neq 0 (
    echo Installing Chocolatey...
    powershell -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
    refreshenv
) else (
    echo ✅ Chocolatey already installed
)
echo.

REM Cài đặt Python
echo 3️⃣ Installing Python 3.11...
where python >nul 2>&1
if %errorLevel% neq 0 (
    echo Installing Python 3.11...
    choco install python311 -y
    refreshenv
) else (
    echo ✅ Python already installed
    python --version
)
echo.

REM Cài đặt Git
echo 4️⃣ Installing Git...
where git >nul 2>&1
if %errorLevel% neq 0 (
    echo Installing Git...
    choco install git -y
    refreshenv
) else (
    echo ✅ Git already installed
)
echo.

REM Cài đặt FFmpeg
echo 5️⃣ Installing FFmpeg...
where ffmpeg >nul 2>&1
if %errorLevel% neq 0 (
    echo Installing FFmpeg...
    choco install ffmpeg -y
    refreshenv
) else (
    echo ✅ FFmpeg already installed
)
echo.

REM Cài đặt Visual C++ Build Tools (cần cho một số Python packages)
echo 6️⃣ Installing Visual C++ Build Tools...
choco install visualcpp-build-tools -y
echo.

REM Cập nhật pip
echo 7️⃣ Updating pip...
python -m pip install --upgrade pip
echo.

REM Tạo virtual environment
echo 8️⃣ Creating Python virtual environment...
if exist "photobooth_env" (
    echo Virtual environment already exists
) else (
    python -m venv photobooth_env
    echo ✅ Virtual environment created
)

REM Kích hoạt virtual environment
echo Activating virtual environment...
call photobooth_env\Scripts\activate.bat
echo.

REM Cài đặt Python packages
echo 9️⃣ Installing Python packages...
if exist "requirements.txt" (
    echo Installing from requirements.txt...
    pip install -r requirements.txt
) else (
    echo requirements.txt not found, installing essential packages...
    pip install flask==3.1.0
    pip install flask-cors==3.0.10
    pip install werkzeug==3.1.3
    pip install Pillow==11.3.0
    pip install opencv-python==4.12.0.88
    pip install numpy==2.0.1
    pip install requests==2.32.4
    pip install qrcode==7.4.2
    pip install psutil
)

REM Cài đặt PyInstaller
echo Installing PyInstaller...
pip install pyinstaller
echo.

REM Tạo thư mục cần thiết
echo 🔟 Creating required directories...
if not exist "uploads" mkdir uploads
if not exist "outputs" mkdir outputs
if not exist "logs" mkdir logs
if not exist "static" mkdir static
if not exist "templates" mkdir templates
echo ✅ Directories created
echo.

REM Kiểm tra cài đặt
echo 1️⃣1️⃣ Verifying installation...
echo Checking Python...
python --version

echo Checking pip...
pip --version

echo Checking key packages...
python -c "import flask; print(f'Flask: {flask.__version__}')" 2>nul || echo ❌ Flask not installed properly
python -c "import PIL; print(f'Pillow: {PIL.__version__}')" 2>nul || echo ❌ Pillow not installed properly
python -c "import cv2; print(f'OpenCV: {cv2.__version__}')" 2>nul || echo ❌ OpenCV not installed properly
python -c "import numpy; print(f'NumPy: {numpy.__version__}')" 2>nul || echo ❌ NumPy not installed properly

echo.
echo ================================================
echo           INSTALLATION COMPLETED
echo ================================================
echo.
echo 📋 Next steps:
echo 1. Make sure your PhotoboothApp source code is in this directory
echo 2. Run: photobooth_env\Scripts\activate.bat (to activate virtual environment)
echo 3. Run: build_exe_windows.bat (to build executable)
echo 4. Run: install_autostart_windows.bat (to setup auto-start)
echo.
echo 💡 Virtual Environment:
echo    Activate: photobooth_env\Scripts\activate.bat
echo    Deactivate: photobooth_env\Scripts\deactivate.bat
echo.

REM Lưu thông tin cài đặt
echo PhotoboothApp Installation Information > installation_info.txt
echo ===================================== >> installation_info.txt
echo Date: %date% %time% >> installation_info.txt
echo Windows Version: %VERSION% >> installation_info.txt
python --version >> installation_info.txt 2>&1
pip --version >> installation_info.txt 2>&1
echo Virtual Environment: photobooth_env\ >> installation_info.txt
echo. >> installation_info.txt
echo Installation Status: >> installation_info.txt
echo - Chocolatey: Installed >> installation_info.txt
echo - Python 3: Installed >> installation_info.txt
echo - Virtual Environment: Created >> installation_info.txt
echo - System Dependencies: Installed >> installation_info.txt
echo - Python Packages: Installed >> installation_info.txt

echo 📄 Installation info saved to: installation_info.txt
echo.
pause
