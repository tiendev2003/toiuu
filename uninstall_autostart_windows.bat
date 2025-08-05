@echo off
REM uninstall_autostart_windows.bat - Gỡ bỏ auto-start cho Windows

echo ===============================================
echo   Removing Auto-Start for Photobooth App
echo ===============================================

REM Xóa Windows Task Scheduler entry
echo Removing Windows Task Scheduler entry...
schtasks /delete /tn "PhotoboothApp AutoStart" /f >nul 2>&1

if %errorLevel% equ 0 (
    echo ✅ Task Scheduler entry removed
) else (
    echo ⚠️ Task Scheduler entry not found or already removed
)

REM Xóa registry entry
echo Removing registry entry...
reg delete "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run" ^
    /v "PhotoboothApp" ^
    /f >nul 2>&1

if %errorLevel% equ 0 (
    echo ✅ Registry entry removed
) else (
    echo ⚠️ Registry entry not found or already removed
)

echo.
echo ✅ Auto-start removed successfully!
echo PhotoboothApp will no longer start automatically
echo.
pause
