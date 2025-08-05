@echo off
REM deploy_windows.bat - Script triển khai hoàn chỉnh cho Windows

echo ================================================
echo      PHOTOBOOTH APP DEPLOYMENT (Windows)
echo ================================================
echo.

REM Kích hoạt virtual environment nếu có
if exist "photobooth_env" (
    echo 🔧 Activating virtual environment...
    call photobooth_env\Scripts\activate.bat
)

REM Kiểm tra Python
echo 1️⃣ Checking Python environment...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ Python not found. Please run fresh_install_windows.bat first.
    pause
    exit /b 1
)

pip --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ pip not found. Please run fresh_install_windows.bat first.
    pause
    exit /b 1
)

REM Cài đặt dependencies
echo.
echo 2️⃣ Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller

REM Build executable
echo.
echo 3️⃣ Building executable...
call build_exe_windows.bat

if %errorLevel% equ 0 (
    echo.
    echo 4️⃣ Setting up auto-start...
    call install_autostart_windows.bat
    
    if %errorLevel% equ 0 (
        echo.
        echo ================================================
        echo           DEPLOYMENT SUCCESSFUL
        echo ================================================
        echo.
        echo ✅ Executable created: dist\PhotoboothApp.exe
        echo ✅ Auto-start configured
        echo ✅ App will start automatically on login
        echo.
        echo 🌐 Access your app at: http://localhost:5000
        echo.
        echo 📋 Management commands:
        echo    Start manually: dist\PhotoboothApp.exe
        echo    Stop auto-start: uninstall_autostart_windows.bat
        echo    Rebuild: build_exe_windows.bat
        echo.
        
        REM Hỏi có muốn chạy app ngay không
        set /p choice="🤔 Do you want to start the app now? (y/n): "
        if /i "%choice%"=="y" (
            echo Starting PhotoboothApp...
            start "" "dist\PhotoboothApp.exe"
            echo App started! Access at http://localhost:5000
        )
    ) else (
        echo ❌ Auto-start setup failed
        pause
        exit /b 1
    )
) else (
    echo ❌ Build failed
    pause
    exit /b 1
)

pause
