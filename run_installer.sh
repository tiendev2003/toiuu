#!/bin/bash
# run_installer.sh - Chạy GUI installer

echo "🚀 Starting PhotoboothApp GUI Installer..."

# Kiểm tra Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found!"
    echo "Installing Python3 first..."
    
    # Cài đặt Homebrew nếu chưa có
    if ! command -v brew &> /dev/null; then
        echo "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    
    # Cài Python
    brew install python@3.11
fi

# Kiểm tra tkinter
python3 -c "import tkinter" 2>/dev/null || {
    echo "❌ tkinter not found! Installing..."
    brew install python-tk
}

# Chạy GUI installer
echo "🎯 Launching GUI installer..."
python3 gui_installer.py
