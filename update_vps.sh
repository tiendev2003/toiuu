#!/bin/bash
# VPS Update Script
set -e

echo "🔄 Updating Photobooth on VPS..."

# Backup current version
cp -r . ../photobooth_backup_$(date +%Y%m%d_%H%M%S)

# Pull latest code (if using git)
# git pull origin main

# Activate virtual environment
source venv/bin/activate

# Update dependencies if needed
pip install -r requirements_vps.txt

# Restart service
sudo systemctl restart photobooth

echo "✅ Update completed!"
sudo systemctl status photobooth
