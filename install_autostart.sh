#!/bin/bash
# install_autostart.sh - Script cài đặt auto-start cho macOS

APP_NAME="PhotoboothApp"
CURRENT_DIR=$(pwd)
DIST_PATH="$CURRENT_DIR/dist/$APP_NAME"
PLIST_PATH="$HOME/Library/LaunchAgents/com.photobooth.app.plist"

echo "=== Setting up Auto-Start for Photobooth App ==="

# Kiểm tra file exe có tồn tại không
if [ ! -f "$DIST_PATH" ]; then
    echo "❌ Executable not found at: $DIST_PATH"
    echo "Please run build_exe.sh first to create the executable"
    exit 1
fi

# Tạo LaunchAgent plist file cho macOS
echo "Creating LaunchAgent configuration..."
cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.photobooth.app</string>
    <key>ProgramArguments</key>
    <array>
        <string>$DIST_PATH</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$CURRENT_DIR/dist</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$CURRENT_DIR/logs/autostart.log</string>
    <key>StandardErrorPath</key>
    <string>$CURRENT_DIR/logs/autostart_error.log</string>
</dict>
</plist>
EOF

# Load LaunchAgent
echo "Loading LaunchAgent..."
launchctl unload "$PLIST_PATH" 2>/dev/null
launchctl load "$PLIST_PATH"

# Kiểm tra trạng thái
if launchctl list | grep -q "com.photobooth.app"; then
    echo "✅ Auto-start setup successful!"
    echo "The app will now start automatically when you log in"
    echo "LaunchAgent file: $PLIST_PATH"
    echo ""
    echo "To manually control the service:"
    echo "  Start: launchctl load $PLIST_PATH"
    echo "  Stop:  launchctl unload $PLIST_PATH"
    echo "  Check status: launchctl list | grep com.photobooth.app"
else
    echo "❌ Failed to setup auto-start"
    exit 1
fi
