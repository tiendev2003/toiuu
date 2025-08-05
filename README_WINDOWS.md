# 🚀 PhotoboothApp - Windows Setup Guide

## 🎯 ONE-CLICK SOLUTIONS CHO WINDOWS

### 🖥️ Option 1: GUI Installer (Giao diện đẹp - Khuyến nghị)
```cmd
run_installer_windows.bat
```
**Click đúp** vào file `run_installer_windows.bat` và bấm nút **"ONE-CLICK INSTALL & DEPLOY"**

### ⚡ Option 2: Command Line (Siêu nhanh)
```cmd
quick_setup_windows.bat
```
**Click đúp** vào file `quick_setup_windows.bat` (cần chạy **Run as Administrator**)

---

## 🆕 Cho máy Windows mới hoàn toàn

### 🎯 Setup siêu nhanh (1 click - Khuyến nghị)
1. **Click đúp** vào `quick_setup_windows.bat`
2. **Click "Run as Administrator"** khi Windows hỏi
3. Chờ script cài đặt tất cả (Python, dependencies, build exe, auto-start)
4. Xong! App sẽ chạy tự động khi khởi động Windows

### 🔧 Setup từng bước
```cmd
REM Bước 1: Cài đặt môi trường (Run as Administrator)
fresh_install_windows.bat

REM Bước 2: Build và deploy
deploy_windows.bat
```

---

## 🛠️ Cho máy Windows đã có Python

```cmd
REM Chỉ cần chạy deploy
deploy_windows.bat
```

---

## 📋 Các lệnh hữu ích cho Windows

```cmd
REM Kiểm tra app đang chạy
tasklist | findstr PhotoboothApp

REM Xem auto-start status
schtasks /query /tn "PhotoboothApp AutoStart"

REM Dừng auto-start
uninstall_autostart_windows.bat

REM Build lại
build_exe_windows.bat

REM Khởi động thủ công
dist\PhotoboothApp.exe
```

---

## 🌐 Truy cập ứng dụng

Sau khi setup xong, truy cập: **http://localhost:5000**

---

## ⚠️ Lưu ý quan trọng cho Windows

1. **Quyền Administrator**: Cần chạy **"Run as Administrator"** để cài đặt đầy đủ
2. **Windows Defender**: Có thể cần cho phép app chạy qua Windows Defender
3. **Firewall**: Windows có thể hỏi cho phép app truy cập mạng - click **Allow**
4. **Auto-start**: Sử dụng Windows Task Scheduler và Registry

---

## 📁 Files quan trọng cho Windows

- `run_installer_windows.bat` - GUI installer (khuyến nghị)
- `quick_setup_windows.bat` - Setup tất cả trong 1 lệnh
- `fresh_install_windows.bat` - Cài đặt môi trường cho máy mới  
- `deploy_windows.bat` - Build và setup auto-start
- `build_exe_windows.bat` - Build executable
- `install_autostart_windows.bat` - Setup auto-start
- `uninstall_autostart_windows.bat` - Gỡ auto-start

---

## ❓ Cần trợ giúp?

1. **Chạy GUI Installer**: Double-click `run_installer_windows.bat`
2. **Lỗi quyền**: Click chuột phải → **"Run as Administrator"**
3. **Python không tìm thấy**: Script sẽ tự động cài Python
4. **Xem log chi tiết**: Mở Command Prompt và chạy script để xem chi tiết
