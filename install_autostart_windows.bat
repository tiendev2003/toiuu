@echo off
REM install_autostart_windows.bat - Thiết lập auto-start cho Windows

echo ===============================================
echo   Setting up Auto-Start for Photobooth App
echo ===============================================

set APP_NAME=PhotoboothApp
set CURRENT_DIR=%cd%
set EXE_PATH=%CURRENT_DIR%\dist\%APP_NAME%.exe

REM Kiểm tra file exe có tồn tại không
if not exist "%EXE_PATH%" (
    echo ❌ Executable not found at: %EXE_PATH%
    echo Please run build_exe_windows.bat first to create the executable
    pause
    exit /b 1
)

echo ✅ Found executable: %EXE_PATH%

REM Tạo Windows Task Scheduler entry cho auto-start
echo Creating Windows Task Scheduler entry...

REM Xóa task cũ nếu có
schtasks /delete /tn "PhotoboothApp AutoStart" /f >nul 2>&1

REM Tạo task mới
schtasks /create /tn "PhotoboothApp AutoStart" ^
    /tr "\"%EXE_PATH%\"" ^
    /sc onlogon ^
    /rl highest ^
    /f

if %errorLevel% equ 0 (
    echo ✅ Auto-start setup successful!
    echo The app will now start automatically when you log in
    echo.
    echo Task Name: PhotoboothApp AutoStart
    echo Executable: %EXE_PATH%
    echo.
    echo To manually control the service:
    echo   Enable:  schtasks /change /tn "PhotoboothApp AutoStart" /enable
    echo   Disable: schtasks /change /tn "PhotoboothApp AutoStart" /disable
    echo   Delete:  schtasks /delete /tn "PhotoboothApp AutoStart" /f
    echo   Check:   schtasks /query /tn "PhotoboothApp AutoStart"
) else (
    echo ❌ Failed to setup auto-start
    echo Please make sure you're running as Administrator
    pause
    exit /b 1
)

REM Thêm registry entry để chạy khi Windows khởi động (backup method)
echo Adding registry entry for backup auto-start...
reg add "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run" ^
    /v "PhotoboothApp" ^
    /t REG_SZ ^
    /d "\"%EXE_PATH%\"" ^
    /f >nul

if %errorLevel% equ 0 (
    echo ✅ Registry backup entry added
) else (
    echo ⚠️ Registry entry failed (not critical)
)

echo.
echo ================================================
echo           AUTO-START SETUP COMPLETED
echo ================================================
echo.
echo 🎯 PhotoboothApp will now start automatically when:
echo    - You log into Windows
echo    - Windows starts up
echo.
echo 🌐 After startup, access your app at: http://localhost:5000
echo.
pause
