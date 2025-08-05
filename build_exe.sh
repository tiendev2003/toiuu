#!/bin/bash
# build_exe.sh - Script để build exe từ Python code

echo "=== Building Photobooth App to EXE ==="

# Kích hoạt virtual environment nếu có
if [ -d "photobooth_env" ]; then
    echo "Activating virtual environment..."
    source photobooth_env/bin/activate
fi

# Kiểm tra Python và pip
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please run fresh_install.sh first"
    exit 1
fi

# Kiểm tra và cài đặt PyInstaller nếu chưa có
echo "Checking PyInstaller installation..."
if ! pip show pyinstaller > /dev/null 2>&1; then
    echo "Installing PyInstaller..."
    pip install pyinstaller
else
    echo "PyInstaller already installed"
fi

# Tạo thư mục build nếu chưa có
mkdir -p build
mkdir -p dist

# Dọn dẹp build cũ
echo "Cleaning old build files..."
rm -rf build/*
rm -rf dist/*

# Build exe bằng PyInstaller với spec file
echo "Building executable with PyInstaller..."
pyinstaller main.spec

# Kiểm tra kết quả build
if [ -f "dist/PhotoboothApp" ]; then
    echo "✅ Build successful!"
    echo "Executable file: dist/PhotoboothApp"
    
    # Tạo thư mục cần thiết trong dist
    echo "Creating required directories..."
    mkdir -p dist/uploads
    mkdir -p dist/outputs
    mkdir -p dist/logs
    
    # Copy các file cấu hình cần thiết
    echo "Copying configuration files..."
    cp config.py dist/ 2>/dev/null || echo "config.py not found"
    cp requirements.txt dist/ 2>/dev/null || echo "requirements.txt not found"
    
    echo "Build process completed!"
    echo "You can run the app with: ./dist/PhotoboothApp"
else
    echo "❌ Build failed!"
    echo "Check the build logs above for errors"
    exit 1
fi
