# Hướng dẫn đóng gói và auto-start Photobooth App

## 🖥️ Chọn hệ điều hành của bạn

### 🍎 macOS Users
- Xem hướng dẫn chi tiết trong phần dưới
- Quick start: `./quick_setup.sh`

### 🪟 Windows Users  
- **Xem file: `README_WINDOWS.md`** để có hướng dẫn đầy đủ cho Windows
- **Quick start: Double-click `run_installer_windows.bat`**

---

## 💻 Cài đặt cho máy mới (Fresh Installation) - macOSướng dẫn đóng gói và auto-start Photobooth App

## � Cài đặt cho máy mới (Fresh Installation)

### Option 1: Cài đặt tự động (Khuyến nghị)
```bash
# Tải và chạy script cài đặt tự động
./fresh_install.sh
```

Script này sẽ tự động cài đặt:
- Xcode Command Line Tools
- Homebrew (package manager)
- Python 3.11
- pip (Python package manager)
- FFmpeg và các dependencies hệ thống
- Virtual environment
- Tất cả Python packages cần thiết
- PyInstaller

### Option 2: Cài đặt thủ công

#### Bước 1: Cài đặt Xcode Command Line Tools
```bash
xcode-select --install
```

#### Bước 2: Cài đặt Homebrew
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### Bước 3: Cài đặt Python và dependencies
```bash
brew install python@3.11
brew install ffmpeg pkg-config libpng jpeg libtiff
```

#### Bước 4: Tạo virtual environment
```bash
python3 -m venv photobooth_env
source photobooth_env/bin/activate
```

#### Bước 5: Cài đặt Python packages
```bash
pip install -r requirements.txt
pip install pyinstaller
```

---

## �🚀 Đóng gói thành file EXE

### Bước 1: Kích hoạt virtual environment (nếu sử dụng)
```bash
source photobooth_env/bin/activate
```

### Bước 2: Cài đặt các dependencies cần thiết
```bash
pip install -r requirements.txt
pip install pyinstaller
```

### Bước 3: Build executable
```bash
./build_exe.sh
```

Sau khi build thành công, file exe sẽ được tạo tại `dist/PhotoboothApp`

### Bước 4: Test chạy executable
```bash
cd dist
./PhotoboothApp
```

Ứng dụng sẽ chạy trên http://localhost:5000

---

## ⚙️ Thiết lập Auto-Start khi khởi động máy

### Cài đặt auto-start
```bash
./install_autostart.sh
```

### Gỡ bỏ auto-start
```bash
./uninstall_autostart.sh
```

### Kiểm tra trạng thái auto-start
```bash
launchctl list | grep com.photobooth.app
```

---

## 📁 Cấu trúc sau khi build

```
dist/
├── PhotoboothApp          # File executable chính
├── templates/             # Templates HTML
├── static/               # Static files (CSS, JS, images)
├── uploads/              # Thư mục upload (tự tạo)
├── outputs/              # Thư mục output (tự tạo)
├── logs/                 # Thư mục logs (tự tạo)
└── config.py            # File cấu hình
```

---

## 🔧 Troubleshooting

### Lỗi khi build
1. Đảm bảo tất cả dependencies đã được cài đặt: `pip install -r requirements.txt`
2. Cập nhật PyInstaller: `pip install --upgrade pyinstaller`
3. Xóa cache build cũ: `rm -rf build/ dist/`

### Lỗi auto-start
1. Kiểm tra quyền thực thi: `chmod +x dist/PhotoboothApp`
2. Kiểm tra đường dẫn trong plist file: `cat ~/Library/LaunchAgents/com.photobooth.app.plist`
3. Kiểm tra logs: `tail -f logs/autostart.log`

### Lỗi khi chạy executable
1. Đảm bảo các thư mục cần thiết đã được tạo (uploads, outputs, logs)
2. Kiểm tra quyền truy cập file
3. Xem logs trong thư mục logs/

---

## 📝 Lưu ý quan trọng

1. **Dependencies**: Tất cả Python packages cần thiết phải được cài đặt trước khi build
2. **Permissions**: Executable cần quyền thực thi và quyền truy cập các thư mục cần thiết
3. **Network**: Ứng dụng sẽ chạy trên cổng 5000, đảm bảo cổng này không bị chiếm dụng
4. **Auto-start**: Chỉ hoạt động khi user đăng nhập vào macOS
5. **Logs**: Kiểm tra logs để debug khi có vấn đề

---

## 🎯 Các lệnh hữu ích

```bash
# Setup siêu nhanh cho máy mới (all-in-one)
./quick_setup.sh

# Setup môi trường cho máy mới
./fresh_install.sh

# Kích hoạt virtual environment
source photobooth_env/bin/activate

# Build lại executable
./build_exe.sh

# Cài đặt auto-start
./install_autostart.sh

# Gỡ bỏ auto-start  
./uninstall_autostart.sh

# Kiểm tra process đang chạy
ps aux | grep PhotoboothApp

# Kiểm tra cổng 5000
lsof -i :5000

# Xem logs auto-start
tail -f logs/autostart.log

# Kiểm tra virtual environment
which python
pip list
```

---

## 🆕 Cho máy mới hoàn toàn

### Cách 1: Siêu nhanh (Khuyến nghị)
```bash
# Chỉ cần 1 lệnh duy nhất!
./quick_setup.sh
```

### Cách 2: Từng bước
```bash
# Bước 1: Cài đặt môi trường
./fresh_install.sh

# Bước 2: Kích hoạt virtual environment  
source photobooth_env/bin/activate

# Bước 3: Deploy app
./deploy.sh
```

### Cách 3: Thủ công hoàn toàn
Xem phần "Cài đặt cho máy mới" ở đầu tài liệu này.
