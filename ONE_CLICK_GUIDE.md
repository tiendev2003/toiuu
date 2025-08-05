# 🎯 PhotoboothApp - ONE-CLICK INSTALLER

## 🚀 BẤM 1 NÚT DUY NHẤT ĐỂ CÀI ĐẶT TẤT CẢ!

### 🍎 macOS
```bash
# Cách 1: GUI đẹp
./run_installer.sh

# Cách 2: Terminal nhanh  
./quick_setup.sh
```

### 🪟 Windows
```cmd
REM Cách 1: GUI đẹp (khuyến nghị)
run_installer_windows.bat

REM Cách 2: Command line nhanh
quick_setup_windows.bat
```

**LÀM GÌ SAU KHI BẤM?**
- ✅ Tự động cài Python + tất cả dependencies
- ✅ Build thành file .exe/.app
- ✅ Setup auto-start khi khởi động máy
- ✅ Sẵn sàng sử dụng tại http://localhost:5000

---

## 📱 Hướng dẫn chi tiết

- **macOS**: Xem `BUILD_GUIDE.md` hoặc `README_SETUP.md`
- **Windows**: Xem `README_WINDOWS.md`

---

## 🎊 SAU KHI CÀI XONG

1. **Truy cập app**: http://localhost:5000
2. **App tự khởi động**: Khi bật máy/đăng nhập  
3. **File executable**:
   - macOS: `dist/PhotoboothApp`
   - Windows: `dist\PhotoboothApp.exe`

---

## 🛠️ Quản lý

### macOS
```bash
# Dừng auto-start
./uninstall_autostart.sh

# Build lại
./build_exe.sh

# Kiểm tra đang chạy
ps aux | grep PhotoboothApp
```

### Windows  
```cmd
REM Dừng auto-start
uninstall_autostart_windows.bat

REM Build lại
build_exe_windows.bat

REM Kiểm tra đang chạy
tasklist | findstr PhotoboothApp
```

---

**🎯 TÓM LẠI: CHỈ CẦN 1 CLICK!**
- macOS: `./run_installer.sh` hoặc `./quick_setup.sh`
- Windows: `run_installer_windows.bat` hoặc `quick_setup_windows.bat`
