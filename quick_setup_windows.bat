@echo off
REM quick_setup_windows.bat - Setup siêu nhanh cho Windows

echo ================================================
echo     PHOTOBOOTH APP - QUICK SETUP (Windows)
echo ================================================
echo This script will install everything and deploy the app in one go!
echo.

REM Kiểm tra quyền admin
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ This script requires Administrator privileges
    echo Please right-click and "Run as Administrator"
    pause
    exit /b 1
)

REM Kiểm tra nếu đã có cài đặt sẵn
if exist "dist\PhotoboothApp.exe" (
    schtasks /query /tn "PhotoboothApp AutoStart" >nul 2>&1
    if %errorLevel% equ 0 (
        echo 🎉 PhotoboothApp is already installed and configured!
        echo.
        set /p choice="Do you want to rebuild and redeploy? (y/n): "
        if /i not "%choice%"=="y" (
            echo Setup cancelled. Your existing installation is preserved.
            pause
            exit /b 0
        )
    )
)

REM Chạy fresh install
echo 🔧 Running fresh installation...
call fresh_install_windows.bat

if %errorLevel% neq 0 (
    echo ❌ Fresh installation failed
    pause
    exit /b 1
)

echo.
echo ⏳ Waiting 3 seconds before continuing...
timeout /t 3 /nobreak >nul

REM Kích hoạt virtual environment
if exist "photobooth_env" (
    echo 🔧 Activating virtual environment...
    call photobooth_env\Scripts\activate.bat
)

REM Chạy deployment
echo 🚀 Running deployment...
call deploy_windows.bat

if %errorLevel% equ 0 (
    echo.
    echo ================================================
    echo      QUICK SETUP COMPLETED SUCCESSFULLY
    echo ================================================
    echo.
    echo ✅ Everything is installed and configured!
    echo ✅ PhotoboothApp will start automatically on login
    echo ✅ You can access the app at: http://localhost:5000
    echo.
    echo 📱 Quick commands:
    echo    Check running processes: tasklist ^| findstr PhotoboothApp
    echo    Stop auto-start: uninstall_autostart_windows.bat
    echo    Start manually: dist\PhotoboothApp.exe
    echo    Rebuild: build_exe_windows.bat
    echo.
) else (
    echo ❌ Deployment failed
    pause
    exit /b 1
)

pause
