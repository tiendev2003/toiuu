@echo off
REM run_installer_windows.bat - Chạy GUI installer cho Windows

echo 🚀 Starting PhotoboothApp GUI Installer for Windows...

REM Kiểm tra Python
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ Python not found!
    echo.
    echo Installing Python automatically...
    echo Please wait while we install Python via winget...
    
    REM Thử cài Python qua winget
    winget install Python.Python.3.11 >nul 2>&1
    if %errorLevel% neq 0 (
        echo ❌ Failed to install Python automatically
        echo.
        echo Please install Python manually:
        echo 1. Go to https://python.org/downloads/
        echo 2. Download Python 3.11
        echo 3. Install with "Add to PATH" option checked
        echo 4. Run this script again
        pause
        exit /b 1
    )
    
    echo ✅ Python installed successfully
    echo Please restart this script
    pause
    exit /b 0
)

REM Kiểm tra tkinter
python -c "import tkinter" 2>nul
if %errorLevel% neq 0 (
    echo ❌ tkinter not found!
    echo tkinter should come with Python by default
    echo Please reinstall Python with tkinter support
    pause
    exit /b 1
)

REM Chạy GUI installer
echo 🎯 Launching GUI installer...
python gui_installer_windows.py

if %errorLevel% neq 0 (
    echo.
    echo ❌ GUI installer failed to start
    echo Trying alternative installation method...
    echo.
    
    REM Fallback to batch script
    set /p choice="Would you like to try the command-line installer instead? (y/n): "
    if /i "%choice%"=="y" (
        call quick_setup_windows.bat
    )
)

pause
