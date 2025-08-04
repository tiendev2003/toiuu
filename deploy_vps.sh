#!/bin/bash
# VPS Deployment Script
set -e

echo "🚀 Deploying Photobooth to VPS..."

# Cập nhật hệ thống
sudo apt update && sudo apt upgrade -y

# Cài đặt dependencies
sudo apt install -y python3 python3-pip python3-venv nginx ffmpeg

# Tạo virtual environment
python3 -m venv venv
source venv/bin/activate

# Cài đặt Python packages
pip install --upgrade pip
pip install -r requirements_vps.txt

# Tạo thư mục logs
sudo mkdir -p /var/log/photobooth
sudo chown $USER:$USER /var/log/photobooth

# Tạo systemd service
sudo tee /etc/systemd/system/photobooth.service > /dev/null <<EOF
[Unit]
Description=Photobooth Video Processing API
After=network.target

[Service]
Type=notify
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 2 --worker-class gevent --worker-connections 100 app:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Cấu hình Nginx
sudo tee /etc/nginx/sites-available/photobooth > /dev/null <<EOF
server {
    listen 80;
    server_name _;
    
    client_max_body_size 100M;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
    
    location /outputs/ {
        alias $(pwd)/outputs/;
        expires 1h;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Kích hoạt Nginx config
sudo ln -sf /etc/nginx/sites-available/photobooth /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx

# Khởi động services
sudo systemctl daemon-reload
sudo systemctl enable photobooth
sudo systemctl start photobooth
sudo systemctl enable nginx
sudo systemctl start nginx

echo "✅ Deployment completed!"
echo "🌐 Service running on http://your-vps-ip/"
echo "📊 Check status: sudo systemctl status photobooth"
echo "📝 Check logs: sudo journalctl -u photobooth -f"
