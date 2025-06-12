#!/bin/bash

echo "🔧 Nginx Configuration Fix Script for Fixbulance"
echo "==============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
    else
        echo -e "${RED}❌ $1${NC}"
        exit 1
    fi
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

echo "=== STOPPING SERVICES ==="
sudo systemctl stop nginx
print_status "Stopped nginx"

sudo systemctl stop fixbulance
print_status "Stopped fixbulance service"

echo "=== REMOVING BROKEN NGINX CONFIG ==="
sudo rm -f /etc/nginx/sites-enabled/fixbulance
sudo rm -f /etc/nginx/sites-available/fixbulance
print_status "Removed broken nginx configuration"

echo "=== CREATING CLEAN NGINX CONFIGURATION ==="
sudo tee /etc/nginx/sites-available/fixbulance > /dev/null << 'EOF'
server {
    listen 80;
    server_name fixbulance.com www.fixbulance.com 72.146.184.2;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Main application
    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/fixbulance/fixbulance.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static files
    location /static {
        alias /var/www/fixbulance/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Favicon
    location /favicon.ico {
        alias /var/www/fixbulance/app/static/img/favicon.ico;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Security - deny access to sensitive files
    location ~ /\. {
        deny all;
    }

    location ~ \.py$ {
        deny all;
    }

    # Error pages
    error_page 404 /404.html;
    error_page 500 502 503 504 /50x.html;

    # Logging
    access_log /var/log/nginx/fixbulance_access.log;
    error_log /var/log/nginx/fixbulance_error.log;
}
EOF
print_status "Created clean nginx configuration"

echo "=== ENABLING NGINX SITE ==="
sudo ln -sf /etc/nginx/sites-available/fixbulance /etc/nginx/sites-enabled/
print_status "Enabled fixbulance site"

echo "=== TESTING NGINX CONFIGURATION ==="
sudo nginx -t
print_status "Nginx configuration syntax is valid"

echo "=== ENSURING WSGI FILE EXISTS ==="
if [ ! -f /var/www/fixbulance/wsgi.py ]; then
    print_info "Creating wsgi.py file..."
    sudo tee /var/www/fixbulance/wsgi.py > /dev/null << 'EOF'
#!/usr/bin/env python3
import sys
import os

# Add the project directory to Python path
sys.path.insert(0, '/var/www/fixbulance')

# Import the Flask application
from run import app

if __name__ == "__main__":
    app.run()
EOF
    sudo chown fixbulance:fixbulance /var/www/fixbulance/wsgi.py
    sudo chmod 644 /var/www/fixbulance/wsgi.py
    print_status "Created wsgi.py file"
fi

echo "=== FIXING PERMISSIONS ==="
sudo chown -R fixbulance:fixbulance /var/www/fixbulance
sudo chmod -R 755 /var/www/fixbulance
sudo chmod 664 /var/www/fixbulance/*.py
print_status "Fixed file permissions"

echo "=== UPDATING SYSTEMD SERVICE ==="
sudo tee /etc/systemd/system/fixbulance.service > /dev/null << 'EOF'
[Unit]
Description=Gunicorn instance to serve Fixbulance
After=network.target

[Service]
User=fixbulance
Group=fixbulance
WorkingDirectory=/var/www/fixbulance
Environment="PATH=/var/www/fixbulance/flask_repair_app/bin"
ExecStart=/var/www/fixbulance/flask_repair_app/bin/gunicorn --workers 3 --bind unix:fixbulance.sock -m 007 wsgi:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF
print_status "Updated systemd service"

echo "=== RELOADING SYSTEMD ==="
sudo systemctl daemon-reload
print_status "Reloaded systemd"

echo "=== STARTING SERVICES ==="
sudo systemctl start fixbulance
sleep 3
print_status "Started fixbulance service"

sudo systemctl start nginx
sleep 2
print_status "Started nginx"

echo "=== CHECKING SERVICE STATUS ==="
print_info "Checking fixbulance service..."
sudo systemctl status fixbulance --no-pager -l

print_info "Checking nginx service..."
sudo systemctl status nginx --no-pager -l

echo "=== VERIFYING SOCKET FILE ==="
if [ -S /var/www/fixbulance/fixbulance.sock ]; then
    print_status "Socket file exists: /var/www/fixbulance/fixbulance.sock"
    ls -la /var/www/fixbulance/fixbulance.sock
else
    echo -e "${RED}❌ Socket file not found${NC}"
fi

echo "=== TESTING LOCAL CONNECTION ==="
print_info "Testing local connection..."
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost/ || echo "Connection failed"

echo "=== CHECKING NGINX ERROR LOG ==="
print_info "Recent nginx errors:"
sudo tail -n 10 /var/log/nginx/error.log

echo "=== FINAL STATUS ==="
if sudo systemctl is-active --quiet fixbulance && sudo systemctl is-active --quiet nginx; then
    echo -e "${GREEN}🎉 All services are running!${NC}"
    echo -e "${GREEN}🌐 Your website should now be accessible at http://fixbulance.com${NC}"
else
    echo -e "${RED}⚠️  Some services are not running properly${NC}"
fi

echo ""
echo "=== NEXT STEPS ==="
echo "1. Wait 30 seconds for services to fully start"
echo "2. Test your website: http://fixbulance.com"
echo "3. If still not working, check: sudo tail -f /var/log/nginx/error.log" 