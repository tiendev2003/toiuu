#!/bin/bash
# quick_setup.sh - Setup nhanh cho máy mới và deploy ngay

echo "⚡ === PHOTOBOOTH APP - QUICK SETUP === ⚡"
echo "This script will install everything and deploy the app in one go!"
echo ""

# Kiểm tra nếu đã có cài đặt sẵn
if [[ -f "dist/PhotoboothApp" ]] && [[ -f "$HOME/Library/LaunchAgents/com.photobooth.app.plist" ]]; then
    echo "🎉 PhotoboothApp is already installed and configured!"
    echo ""
    read -p "Do you want to rebuild and redeploy? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled. Your existing installation is preserved."
        exit 0
    fi
fi

# Chạy fresh install
echo "🔧 Running fresh installation..."
./fresh_install.sh

if [ $? -ne 0 ]; then
    echo "❌ Fresh installation failed"
    exit 1
fi

echo ""
echo "⏳ Waiting 3 seconds before continuing..."
sleep 3

# Kích hoạt virtual environment
if [ -d "photobooth_env" ]; then
    echo "🔧 Activating virtual environment..."
    source photobooth_env/bin/activate
fi

# Chạy deployment
echo "🚀 Running deployment..."
./deploy.sh

if [ $? -eq 0 ]; then
    echo ""
    echo "🎊 === QUICK SETUP COMPLETED SUCCESSFULLY === 🎊"
    echo ""
    echo "✅ Everything is installed and configured!"
    echo "✅ PhotoboothApp will start automatically on login"
    echo "✅ You can access the app at: http://localhost:5000"
    echo ""
    echo "📱 Quick commands:"
    echo "   Check app status: ps aux | grep PhotoboothApp"
    echo "   View logs: tail -f logs/autostart.log"
    echo "   Stop auto-start: ./uninstall_autostart.sh"
    echo "   Start manually: cd dist && ./PhotoboothApp"
    echo ""
else
    echo "❌ Deployment failed"
    exit 1
fi
