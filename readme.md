pyinstaller --onefile --noconsole --add-data "ffmpeg.exe;." app.py
pyinstaller app.py --onefile --noconsole --add-data "ffmpeg/bin;ffmpeg/bin" --name my_flask_app

taskkill /PID 10972 /F 

netstat -ano | findstr :5000


rundll32 printui.dll,PrintUIEntry /if /b "DS-RX1-Cut" /f "D:\DRIVER_RX1HS_WIN_11 v1.14\DRIVER_RX1HS_WIN_11 v1.14\11\DriverPackage\DSRX1.inf" /r "USB001" /m "DS-RX1"
