#!/bin/bash
# uninstall_autostart.sh - Script gỡ bỏ auto-start

PLIST_PATH="$HOME/Library/LaunchAgents/com.photobooth.app.plist"

echo "=== Removing Auto-Start for Photobooth App ==="

if [ -f "$PLIST_PATH" ]; then
    echo "Unloading LaunchAgent..."
    launchctl unload "$PLIST_PATH"
    
    echo "Removing plist file..."
    rm "$PLIST_PATH"
    
    echo "✅ Auto-start removed successfully!"
else
    echo "Auto-start is not installed"
fi
