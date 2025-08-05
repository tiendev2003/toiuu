@echo off
REM build_exe_windows.bat - Build executable cho Windows

echo ===============================================
echo    Building Photobooth App to EXE (Windows)
echo ===============================================

REM Kích hoạt virtual environment nếu có
if exist "photobooth_env" (
    echo Activating virtual environment...
    call photobooth_env\Scripts\activate.bat
)

REM Kiểm tra Python
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ Python not found. Please run fresh_install_windows.bat first
    pause
    exit /b 1
)

REM Kiểm tra và cài đặt PyInstaller
echo Checking PyInstaller installation...
pip show pyinstaller >nul 2>&1
if %errorLevel% neq 0 (
    echo Installing PyInstaller...
    pip install pyinstaller
) else (
    echo ✅ PyInstaller already installed
)

REM Tạo thư mục build nếu chưa có
if not exist "build" mkdir build
if not exist "dist" mkdir dist

REM Dọn dẹp build cũ
echo Cleaning old build files...
if exist "build\*" del /q "build\*"
if exist "dist\*" del /q "dist\*"

REM Build exe bằng PyInstaller
echo Building executable with PyInstaller...
pyinstaller --onefile --console --name PhotoboothApp ^
    --add-data "templates;templates" ^
    --add-data "static;static" ^
    --hidden-import flask ^
    --hidden-import flask_cors ^
    --hidden-import PIL ^
    --hidden-import cv2 ^
    --hidden-import numpy ^
    --hidden-import requests ^
    --hidden-import qrcode ^
    --hidden-import utils.logging ^
    --hidden-import utils.file_handling ^
    --hidden-import utils.image_processing ^
    --hidden-import utils.video_processing ^
    --hidden-import utils.filters ^
    --hidden-import utils.performance ^
    --hidden-import utils.printer ^
    --hidden-import utils.upload ^
    --hidden-import config ^
    app.py

REM Kiểm tra kết quả build
if exist "dist\PhotoboothApp.exe" (
    echo ✅ Build successful!
    echo Executable file: dist\PhotoboothApp.exe
    
    REM Tạo thư mục cần thiết trong dist
    echo Creating required directories...
    if not exist "dist\uploads" mkdir dist\uploads
    if not exist "dist\outputs" mkdir dist\outputs
    if not exist "dist\logs" mkdir dist\logs
    
    REM Copy các file cấu hình cần thiết
    echo Copying configuration files...
    if exist "config.py" copy config.py dist\ >nul
    if exist "requirements.txt" copy requirements.txt dist\ >nul
    
    echo Build process completed!
    echo You can run the app with: dist\PhotoboothApp.exe
    echo.
) else (
    echo ❌ Build failed!
    echo Check the build logs above for errors
    pause
    exit /b 1
)

pause
