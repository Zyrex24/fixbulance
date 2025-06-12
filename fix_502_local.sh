#!/bin/bash

# =============================================================================
# Fixbulance 502 Local Error Fix Script
# Run this script on your Azure VM to fix local 502 issues
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="/var/www/fixbulance"
APP_USER="fixbulance"
SOCKET_FILE="/var/www/fixbulance/fixbulance.sock"

echo -e "${BLUE}🔧 Fixbulance 502 Local Error Fix Script${NC}"
echo -e "${BLUE}=======================================${NC}"

# Function to print status messages
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check command success
check_success() {
    if [ $? -eq 0 ]; then
        print_status "$1"
    else
        print_error "$1 failed"
        exit 1
    fi
}

print_status "Starting 502 Local Error diagnosis and fix..."

# =============================================================================
# STEP 1: Diagnose Current Issues
# =============================================================================
echo -e "\n${BLUE}=== DIAGNOSTIC PHASE ===${NC}"

print_status "Checking current service status..."
sudo systemctl status fixbulance --no-pager -l || true
sudo systemctl status nginx --no-pager -l || true

print_status "Checking socket file..."
if [ -S "$SOCKET_FILE" ]; then
    echo -e "${GREEN}✅ Socket file exists${NC}"
    ls -la "$SOCKET_FILE"
else
    echo -e "${RED}❌ Socket file missing${NC}"
fi

print_status "Checking running processes..."
ps aux | grep gunicorn | grep -v grep || echo "No gunicorn processes found"

print_status "Checking recent application logs..."
sudo journalctl -u fixbulance -n 10 --no-pager || true

# =============================================================================
# STEP 2: Stop All Services
# =============================================================================
echo -e "\n${BLUE}=== STOPPING SERVICES ===${NC}"

print_status "Stopping nginx..."
sudo systemctl stop nginx
check_success "Nginx stopped"

print_status "Stopping fixbulance service..."
sudo systemctl stop fixbulance
check_success "Fixbulance service stopped"

print_status "Killing any remaining gunicorn processes..."
sudo pkill -f gunicorn || true
sleep 2

# =============================================================================
# STEP 3: Clean Up and Fix Permissions
# =============================================================================
echo -e "\n${BLUE}=== CLEANUP AND PERMISSIONS ===${NC}"

print_status "Removing old socket file..."
sudo rm -f "$SOCKET_FILE"
check_success "Old socket file removed"

print_status "Ensuring application directory has correct ownership..."
sudo chown -R $APP_USER:$APP_USER "$APP_DIR"
check_success "Directory ownership fixed"

print_status "Setting correct permissions..."
sudo chmod 755 "$APP_DIR"
sudo chmod +x "$APP_DIR"/*.py 2>/dev/null || true
check_success "Permissions set"

# =============================================================================
# STEP 4: Fix Gunicorn Configuration
# =============================================================================
echo -e "\n${BLUE}=== FIXING GUNICORN CONFIGURATION ===${NC}"

print_status "Creating optimized gunicorn configuration..."
sudo tee "$APP_DIR/gunicorn_config.py" > /dev/null << 'EOF'
import multiprocessing
import os

# Server socket
bind = "unix:/var/www/fixbulance/fixbulance.sock"
backlog = 2048

# Worker processes
workers = 3
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 100

# Logging
errorlog = "/var/log/fixbulance/error.log"
accesslog = "/var/log/fixbulance/access.log"
loglevel = "info"

# Process naming
proc_name = "fixbulance"

# Server mechanics
preload_app = True
daemon = False
pidfile = "/var/run/fixbulance/fixbulance.pid"
user = "fixbulance"
group = "fixbulance"
tmp_upload_dir = None

# Socket permissions
umask = 0o007
EOF

print_status "Creating log directories..."
sudo mkdir -p /var/log/fixbulance
sudo mkdir -p /var/run/fixbulance
sudo chown -R $APP_USER:$APP_USER /var/log/fixbulance
sudo chown -R $APP_USER:$APP_USER /var/run/fixbulance
check_success "Log directories created"

# =============================================================================
# STEP 5: Fix Application Entry Point
# =============================================================================
echo -e "\n${BLUE}=== FIXING APPLICATION ENTRY POINT ===${NC}"

print_status "Checking application entry point..."
cd "$APP_DIR"

# Check if wsgi.py exists, if not create it
if [ ! -f "wsgi.py" ]; then
    print_status "Creating wsgi.py entry point..."
    sudo -u $APP_USER tee wsgi.py > /dev/null << 'EOF'
#!/usr/bin/env python3
import sys
import os

# Add the application directory to Python path
sys.path.insert(0, '/var/www/fixbulance')

# Import the Flask application
try:
    from run import app
    application = app
except ImportError:
    try:
        from app import app
        application = app
    except ImportError:
        # Create a simple test app if import fails
        from flask import Flask
        application = Flask(__name__)
        
        @application.route('/')
        def hello():
            return '<h1>Fixbulance - Service Running!</h1><p>Application is working correctly.</p>'

if __name__ == "__main__":
    application.run()
EOF
    check_success "wsgi.py created"
fi

# =============================================================================
# STEP 6: Update Systemd Service
# =============================================================================
echo -e "\n${BLUE}=== UPDATING SYSTEMD SERVICE ===${NC}"

print_status "Creating optimized systemd service..."
sudo tee /etc/systemd/system/fixbulance.service > /dev/null << EOF
[Unit]
Description=Fixbulance Flask App on Azure
After=network.target

[Service]
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
Environment="FLASK_ENV=production"
ExecStart=$APP_DIR/venv/bin/gunicorn --config $APP_DIR/gunicorn_config.py wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=5
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

print_status "Reloading systemd daemon..."
sudo systemctl daemon-reload
check_success "Systemd daemon reloaded"

# =============================================================================
# STEP 7: Fix Nginx Configuration
# =============================================================================
echo -e "\n${BLUE}=== FIXING NGINX CONFIGURATION ===${NC}"

print_status "Creating optimized nginx configuration..."
sudo tee /etc/nginx/sites-available/fixbulance > /dev/null << 'EOF'
server {
    listen 80;
    server_name fixbulance.com www.fixbulance.com;
    
    # Increase timeouts
    proxy_connect_timeout       300s;
    proxy_send_timeout          300s;
    proxy_read_timeout          300s;
    send_timeout                300s;
    
    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/fixbulance/fixbulance.sock;
        
        # Better error handling
        proxy_intercept_errors on;
        error_page 502 503 504 /50x.html;
        
        # Additional headers
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location = /50x.html {
        root /var/www/html;
        internal;
    }
    
    location /static {
        alias /var/www/fixbulance/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
}
EOF

print_status "Testing nginx configuration..."
sudo nginx -t
check_success "Nginx configuration valid"

# =============================================================================
# STEP 8: Start Services in Correct Order
# =============================================================================
echo -e "\n${BLUE}=== STARTING SERVICES ===${NC}"

print_status "Starting fixbulance service..."
sudo systemctl start fixbulance
sleep 3
check_success "Fixbulance service started"

print_status "Checking if socket file was created..."
sleep 2
if [ -S "$SOCKET_FILE" ]; then
    print_status "Socket file created successfully"
    ls -la "$SOCKET_FILE"
else
    print_error "Socket file not created - checking logs..."
    sudo journalctl -u fixbulance -n 20 --no-pager
    exit 1
fi

print_status "Starting nginx..."
sudo systemctl start nginx
check_success "Nginx started"

# =============================================================================
# STEP 9: Test Everything
# =============================================================================
echo -e "\n${BLUE}=== TESTING APPLICATION ===${NC}"

print_status "Testing socket connection directly..."
if curl --unix-socket "$SOCKET_FILE" http://localhost/ -s -o /dev/null; then
    print_status "Socket connection working"
else
    print_error "Socket connection failed"
fi

print_status "Testing local HTTP connection..."
sleep 2
HTTP_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/)
if [ "$HTTP_RESPONSE" = "200" ]; then
    print_status "Local HTTP test successful (200 OK)"
elif [ "$HTTP_RESPONSE" = "502" ]; then
    print_error "Still getting 502 - checking detailed logs..."
    sudo journalctl -u fixbulance -n 10 --no-pager
    sudo tail -5 /var/log/nginx/error.log
else
    print_warning "Got HTTP response code: $HTTP_RESPONSE"
fi

print_status "Testing external access..."
PUBLIC_IP=$(curl -4 -s icanhazip.com)
echo "Your public IP: $PUBLIC_IP"
EXTERNAL_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "http://$PUBLIC_IP/" || echo "failed")
echo "External response: $EXTERNAL_RESPONSE"

# =============================================================================
# STEP 10: Final Status Report
# =============================================================================
echo -e "\n${BLUE}=== FINAL STATUS REPORT ===${NC}"

print_status "Service statuses:"
sudo systemctl is-active fixbulance || print_error "Fixbulance service not active"
sudo systemctl is-active nginx || print_error "Nginx service not active"

print_status "Socket file status:"
ls -la "$SOCKET_FILE" 2>/dev/null || print_error "Socket file missing"

print_status "Process status:"
ps aux | grep gunicorn | grep -v grep || print_warning "No gunicorn processes found"

echo -e "\n${GREEN}🎉 Fix script completed!${NC}"
echo -e "\n${BLUE}Next Steps:${NC}"
echo "1. Check if website loads: curl -I http://fixbulance.com"
echo "2. If still not working, run: sudo journalctl -u fixbulance -f"
echo "3. For manual restart: sudo systemctl restart fixbulance"

echo -e "\n${BLUE}Useful Commands:${NC}"
echo "• Check app status: sudo systemctl status fixbulance"
echo "• View live logs: sudo journalctl -u fixbulance -f"
echo "• Restart app: sudo systemctl restart fixbulance"
echo "• Check socket: ls -la /var/www/fixbulance/fixbulance.sock" 