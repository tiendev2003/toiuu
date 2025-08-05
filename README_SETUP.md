# 🚀 PhotoboothApp - One-Click Setup Guide

## 🎯 ONE-CLICK SOLUTIONS

### 🍎 Option 1: macOS App (Siêu đơn giản)
```bash
# Tạo app .app một lần
./create_app.sh

# Sau đó chỉ cần double-click file PhotoboothInstaller.app
```

### 🖥️ Option 2: GUI Installer (Giao diện đẹp)
```bash
# Chạy GUI installer
./run_installer.sh
```
Sau đó chỉ cần bấm nút "ONE-CLICK INSTALL & DEPLOY"

### ⚡ Option 3: Terminal Script (Siêu nhanh)
```bash
# Chạy trực tiếp
./quick_setup.sh
```

---

## Cho máy mới (Fresh macOS)

### 🎯 Setup siêu nhanh (1 lệnh)
```bash
./quick_setup.sh
```
Script này sẽ làm tất cả: cài đặt Python, dependencies, build exe, và setup auto-start!

### 🔧 Setup từng bước
```bash
# Bước 1: Cài đặt môi trường
./fresh_install.sh

# Bước 2: Build và deploy
./deploy.sh
```

---

## Cho máy đã có Python

```bash
# Chỉ cần chạy deploy
./deploy.sh
```

---

## 📋 Các lệnh hữu ích

```bash
# Kiểm tra app đang chạy
ps aux | grep PhotoboothApp

# Xem logs
tail -f logs/autostart.log

# Dừng auto-start
./uninstall_autostart.sh

# Build lại
./build_exe.sh

# Khởi động thủ công
cd dist && ./PhotoboothApp
```

---

## 🌐 Truy cập ứng dụng

Sau khi setup xong, truy cập: **http://localhost:5000**

---

## 📁 Files quan trọng

- `quick_setup.sh` - Setup tất cả trong 1 lệnh
- `fresh_install.sh` - Cài đặt môi trường cho máy mới  
- `deploy.sh` - Build và setup auto-start
- `BUILD_GUIDE.md` - Hướng dẫn chi tiết

---

## ❓ Cần trợ giúp?

Xem hướng dẫn chi tiết trong `BUILD_GUIDE.md`
