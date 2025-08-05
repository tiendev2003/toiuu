#!/bin/bash
# deploy.sh - Script triển khai hoàn chỉnh (build + auto-start)

#!/bin/bash
# deploy.sh - Script triển khai hoàn chỉnh (build + auto-start)

echo "🚀 === PHOTOBOOTH APP DEPLOYMENT === 🚀"
echo ""

# Kích hoạt virtual environment nếu có
if [ -d "photobooth_env" ]; then
    echo "🔧 Activating virtual environment..."
    source photobooth_env/bin/activate
fi

# Kiểm tra Python và pip
echo "1️⃣ Checking Python environment..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please run fresh_install.sh first."
    exit 1
fi

if ! command -v pip &> /dev/null; then
    echo "❌ pip not found. Please run fresh_install.sh first."
    exit 1
fi

# Cài đặt dependencies
echo ""
echo "2️⃣ Installing dependencies..."
pip install -r requirements.txt
pip install pyinstaller

# Build executable
echo ""
echo "3️⃣ Building executable..."
./build_exe.sh

if [ $? -eq 0 ]; then
    echo ""
    echo "4️⃣ Setting up auto-start..."
    ./install_autostart.sh
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "🎉 === DEPLOYMENT SUCCESSFUL === 🎉"
        echo ""
        echo "✅ Executable created: dist/PhotoboothApp"
        echo "✅ Auto-start configured"
        echo "✅ App will start automatically on login"
        echo ""
        echo "🌐 Access your app at: http://localhost:5000"
        echo ""
        echo "📋 Management commands:"
        echo "   Start manually: cd dist && ./PhotoboothApp"
        echo "   Stop auto-start: ./uninstall_autostart.sh"
        echo "   View logs: tail -f logs/autostart.log"
        echo ""
        
        # Hỏi có muốn chạy app ngay không
        read -p "🤔 Do you want to start the app now? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "Starting PhotoboothApp..."
            cd dist
            ./PhotoboothApp &
            echo "App started! Access at http://localhost:5000"
        fi
    else
        echo "❌ Auto-start setup failed"
        exit 1
    fi
else
    echo "❌ Build failed"
    exit 1
fi
