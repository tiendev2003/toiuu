#!/bin/bash
# create_app.sh - Tạo ứng dụng .app cho macOS

APP_NAME="PhotoboothInstaller"
APP_DIR="$APP_NAME.app"
CONTENTS_DIR="$APP_DIR/Contents"
MACOS_DIR="$CONTENTS_DIR/MacOS"
RESOURCES_DIR="$CONTENTS_DIR/Resources"

echo "🍎 Creating macOS App Bundle: $APP_NAME.app"

# Xóa app cũ nếu có
if [ -d "$APP_DIR" ]; then
    echo "Removing existing app..."
    rm -rf "$APP_DIR"
fi

# Tạo cấu trúc thư mục .app
echo "Creating app directory structure..."
mkdir -p "$MACOS_DIR"
mkdir -p "$RESOURCES_DIR"

# Tạo Info.plist
echo "Creating Info.plist..."
cat > "$CONTENTS_DIR/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>$APP_NAME</string>
    <key>CFBundleIdentifier</key>
    <string>com.photobooth.installer</string>
    <key>CFBundleName</key>
    <string>$APP_NAME</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.12</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF

# Tạo executable script
echo "Creating executable script..."
cat > "$MACOS_DIR/$APP_NAME" << 'EOF'
#!/bin/bash

# Lấy đường dẫn thư mục chứa .app
APP_DIR="$(dirname "$(dirname "$(dirname "$0")")")"
cd "$APP_DIR"

# Hiển thị thông báo bắt đầu
osascript -e 'display notification "Starting PhotoboothApp installer..." with title "PhotoboothApp"'

# Tạo terminal window và chạy installer
osascript << 'APPLESCRIPT'
tell application "Terminal"
    activate
    set currentTab to do script "echo '🚀 PhotoboothApp One-Click Installer'; echo '====================================='; echo ''; echo 'This will install everything needed for PhotoboothApp'; echo 'Please wait while we set up your system...'; echo ''"
    
    do script "cd '" & (do shell script "dirname \"$(dirname \"$(dirname \"$0\")\")\"") & "'" in currentTab
    
    do script "./quick_setup.sh" in currentTab
end tell
APPLESCRIPT

# Hiển thị hướng dẫn
osascript << 'APPLESCRIPT'
display dialog "🚀 PhotoboothApp Installer Started!

The installer is running in Terminal.
Please follow the instructions in the Terminal window.

After installation completes:
✅ Your app will be available at http://localhost:5000
✅ App will start automatically when you login

Click OK to continue..." buttons {"OK"} default button "OK" with title "PhotoboothApp Installer"
APPLESCRIPT
EOF

# Cấp quyền thực thi
chmod +x "$MACOS_DIR/$APP_NAME"

# Tạo icon đơn giản (optional)
echo "Creating icon..."
cat > "$RESOURCES_DIR/app_icon.icns" << 'EOF'
# This would contain an actual icon file, but for simplicity we'll skip it
EOF

echo "✅ macOS App created: $APP_DIR"
echo ""
echo "🎯 To use:"
echo "   Double-click: $APP_DIR"
echo "   Or run: open $APP_DIR"
echo ""
echo "📱 The app will:"
echo "   1. Open Terminal"
echo "   2. Run the complete installation"
echo "   3. Set up auto-start"
echo "   4. Launch PhotoboothApp"

# Mở app luôn nếu muốn
read -p "🤔 Do you want to run the installer now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Launching installer..."
    open "$APP_DIR"
fi
