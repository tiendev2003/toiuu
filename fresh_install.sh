#!/bin/bash
# fresh_install.sh - Script cài đặt hoàn chỉnh cho máy mới

echo "🚀 === PHOTOBOOTH APP - FRESH INSTALLATION === 🚀"
echo "This script will install everything needed for PhotoboothApp on a fresh macOS system"
echo ""

# Kiểm tra macOS version
echo "1️⃣ Checking macOS version..."
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This script is designed for macOS only"
    exit 1
fi

mac_version=$(sw_vers -productVersion)
echo "✅ macOS version: $mac_version"
echo ""

# Cài đặt Xcode Command Line Tools (cần thiết cho Python và pip)
echo "2️⃣ Installing Xcode Command Line Tools..."
if ! xcode-select -p &> /dev/null; then
    echo "Installing Xcode Command Line Tools..."
    xcode-select --install
    echo "⏳ Please complete the Xcode Command Line Tools installation in the popup window"
    echo "Press any key to continue after installation is complete..."
    read -n 1 -s
else
    echo "✅ Xcode Command Line Tools already installed"
fi
echo ""

# Cài đặt Homebrew (package manager cho macOS)
echo "3️⃣ Installing Homebrew..."
if ! command -v brew &> /dev/null; then
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Thêm Homebrew vào PATH
    if [[ -f "/opt/homebrew/bin/brew" ]]; then
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/opt/homebrew/bin/brew shellenv)"
    elif [[ -f "/usr/local/bin/brew" ]]; then
        echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/usr/local/bin/brew shellenv)"
    fi
else
    echo "✅ Homebrew already installed"
    brew update
fi
echo ""

# Cài đặt Python 3
echo "4️⃣ Installing Python 3..."
if ! command -v python3 &> /dev/null; then
    echo "Installing Python 3 via Homebrew..."
    brew install python@3.11
    brew link python@3.11
else
    python_version=$(python3 --version)
    echo "✅ Python already installed: $python_version"
fi

# Kiểm tra pip
echo "5️⃣ Checking pip installation..."
if ! command -v pip3 &> /dev/null; then
    echo "Installing pip..."
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    python3 get-pip.py
    rm get-pip.py
else
    pip_version=$(pip3 --version)
    echo "✅ pip already installed: $pip_version"
fi
echo ""

# Cài đặt các dependencies hệ thống cần thiết
echo "6️⃣ Installing system dependencies..."
echo "Installing ffmpeg for video processing..."
brew install ffmpeg

echo "Installing opencv dependencies..."
brew install pkg-config
brew install libpng jpeg libtiff

echo "Installing other useful tools..."
brew install wget curl git
echo ""

# Tạo virtual environment (khuyến nghị)
echo "7️⃣ Setting up Python virtual environment..."
python3 -m venv photobooth_env

echo "Activating virtual environment..."
source photobooth_env/bin/activate

# Upgrade pip trong virtual environment
pip install --upgrade pip
echo ""

# Cài đặt Python packages
echo "8️⃣ Installing Python packages..."
if [[ -f "requirements.txt" ]]; then
    echo "Installing from requirements.txt..."
    pip install -r requirements.txt
else
    echo "requirements.txt not found, installing essential packages..."
    pip install flask==3.1.0
    pip install flask-cors==3.0.10
    pip install werkzeug==3.1.3
    pip install Pillow==11.3.0
    pip install opencv-python==4.12.0.88
    pip install numpy==2.0.1
    pip install requests==2.32.4
    pip install qrcode==7.4.2
    pip install psutil
fi

# Cài đặt PyInstaller để build exe
echo "Installing PyInstaller for building executable..."
pip install pyinstaller
echo ""

# Tạo các thư mục cần thiết
echo "9️⃣ Creating required directories..."
mkdir -p uploads
mkdir -p outputs
mkdir -p logs
mkdir -p static
mkdir -p templates
echo "✅ Directories created"
echo ""

# Kiểm tra tất cả dependencies
echo "🔟 Verifying installation..."
echo "Checking Python..."
python3 --version

echo "Checking pip..."
pip --version

echo "Checking key packages..."
python3 -c "import flask; print(f'Flask: {flask.__version__}')" 2>/dev/null || echo "❌ Flask not installed properly"
python3 -c "import PIL; print(f'Pillow: {PIL.__version__}')" 2>/dev/null || echo "❌ Pillow not installed properly"
python3 -c "import cv2; print(f'OpenCV: {cv2.__version__}')" 2>/dev/null || echo "❌ OpenCV not installed properly"
python3 -c "import numpy; print(f'NumPy: {numpy.__version__}')" 2>/dev/null || echo "❌ NumPy not installed properly"

echo ""
echo "🎉 === INSTALLATION COMPLETED === 🎉"
echo ""
echo "📋 Next steps:"
echo "1. Make sure your PhotoboothApp source code is in this directory"
echo "2. Run: source photobooth_env/bin/activate (to activate virtual environment)"
echo "3. Run: ./build_exe.sh (to build executable)"
echo "4. Run: ./install_autostart.sh (to setup auto-start)"
echo ""
echo "💡 Virtual Environment:"
echo "   Activate: source photobooth_env/bin/activate"
echo "   Deactivate: deactivate"
echo ""
echo "🔧 Troubleshooting:"
echo "   If you encounter permission issues, try: sudo chown -R $(whoami) /usr/local"
echo "   If brew command not found, restart terminal or run: source ~/.zprofile"
echo ""

# Lưu thông tin cài đặt
cat > installation_info.txt << EOF
PhotoboothApp Installation Information
=====================================
Date: $(date)
macOS Version: $(sw_vers -productVersion)
Python Version: $(python3 --version 2>/dev/null || echo "Not installed")
Pip Version: $(pip --version 2>/dev/null || echo "Not installed")
Virtual Environment: photobooth_env/

Installation Status:
- Xcode Command Line Tools: Installed
- Homebrew: Installed
- Python 3: Installed
- Virtual Environment: Created
- System Dependencies: Installed
- Python Packages: Installed

Next Steps:
1. Activate virtual environment: source photobooth_env/bin/activate
2. Build executable: ./build_exe.sh
3. Setup auto-start: ./install_autostart.sh
EOF

echo "📄 Installation info saved to: installation_info.txt"
