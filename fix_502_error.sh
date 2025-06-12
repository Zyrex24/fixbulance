#!/bin/bash

# =============================================================================
# Fixbulance 502 Error Fix Script
# Run this script on your Azure VM as the azureuser
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

echo -e "${BLUE}🔧 Fixbulance 502 Error Fix Script${NC}"
echo -e "${BLUE}=================================${NC}"

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

# Check if running as azureuser (not root)
if [[ $EUID -eq 0 ]]; then
   print_error "This script should be run as azureuser, not root"
   echo "Run: ./fix_502_error.sh"
   exit 1
fi

print_status "Starting 502 error fix process..."

# =============================================================================
# STEP 1: Stop services and clean up
# =============================================================================
print_status "Stopping services and cleaning up..."
sudo systemctl stop fixbulance || true
sudo systemctl stop nginx || true

# Remove any existing socket files
sudo rm -f $APP_DIR/fixbulance.sock
sudo rm -f $APP_DIR/*.sock

# =============================================================================
# STEP 2: Fix file permissions and ownership
# =============================================================================
print_status "Fixing file permissions and ownership..."
sudo chown -R $APP_USER:$APP_USER $APP_DIR/
sudo chmod -R 755 $APP_DIR/

# Create logs directory
sudo mkdir -p $APP_DIR/logs
sudo chown $APP_USER:$APP_USER $APP_DIR/logs

# Ensure .env file has correct permissions
sudo chmod 600 $APP_DIR/.env
sudo chown $APP_USER:$APP_USER $APP_DIR/.env

# =============================================================================
# STEP 3: Create a proper WSGI entry point
# =============================================================================
print_status "Creating proper WSGI entry point..."
sudo -u $APP_USER tee $APP_DIR/wsgi.py << 'EOF'
#!/usr/bin/env python3
"""
WSGI entry point for Fixbulance Flask application
"""
import os
import sys

# Add the application directory to Python path
sys.path.insert(0, '/var/www/fixbulance')

# Set environment for production
os.environ.setdefault('FLASK_ENV', 'production')

try:
    from app import create_app
    
    # Create the application instance
    app = create_app('production')
    
    if __name__ == "__main__":
        app.run()
        
except Exception as e:
    print(f"Error creating Flask app: {e}")
    import traceback
    traceback.print_exc()
    raise
EOF

sudo chown $APP_USER:$APP_USER $APP_DIR/wsgi.py
sudo chmod +x $APP_DIR/wsgi.py

# =============================================================================
# STEP 4: Update systemd service configuration
# =============================================================================
print_status "Updating systemd service configuration..."
sudo tee /etc/systemd/system/fixbulance.service << 'EOF'
[Unit]
Description=Fixbulance Flask App on Azure
After=network.target

[Service]
User=fixbulance
Group=fixbulance
WorkingDirectory=/var/www/fixbulance
Environment="PATH=/var/www/fixbulance/venv/bin"
EnvironmentFile=/var/www/fixbulance/.env
ExecStart=/var/www/fixbulance/venv/bin/gunicorn --workers 3 --bind unix:/var/www/fixbulance/fixbulance.sock --umask 007 wsgi:app
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# =============================================================================
# STEP 5: Test the application manually
# =============================================================================
print_status "Testing the application..."

# Test if Python dependencies are installed
echo "Testing Python environment..."
sudo -u $APP_USER bash -c "cd $APP_DIR && source venv/bin/activate && python -c 'import flask; print(f\"Flask version: {flask.__version__}\")'"

# Test if the WSGI app can be imported
echo "Testing WSGI import..."
sudo -u $APP_USER bash -c "cd $APP_DIR && source venv/bin/activate && python -c 'from wsgi import app; print(\"✅ WSGI app imported successfully\")'"

# =============================================================================
# STEP 6: Update Nginx configuration for better error handling
# =============================================================================
print_status "Updating Nginx configuration..."
sudo tee /etc/nginx/sites-available/fixbulance << 'EOF'
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

# Test nginx configuration
sudo nginx -t

# =============================================================================
# STEP 7: Create a simple error page
# =============================================================================
print_status "Creating error page..."
sudo mkdir -p /var/www/html
sudo tee /var/www/html/50x.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Fixbulance - Service Temporarily Unavailable</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
        .container { max-width: 600px; margin: 0 auto; }
        .logo { color: #dc3545; font-size: 2em; margin-bottom: 20px; }
        .message { color: #6c757d; font-size: 1.2em; }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">📱 Fixbulance</div>
        <h1>Service Temporarily Unavailable</h1>
        <p class="message">We're working to restore service. Please try again in a few minutes.</p>
        <p>For urgent repairs, call: <strong>(708) 971-4053</strong></p>
    </div>
</body>
</html>
EOF

# =============================================================================
# STEP 8: Reload and start services
# =============================================================================
print_status "Reloading and starting services..."
sudo systemctl daemon-reload
sudo systemctl enable fixbulance
sudo systemctl start fixbulance

# Wait a moment for the service to start
sleep 5

# Start nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# =============================================================================
# STEP 9: Check service status and diagnostics
# =============================================================================
print_status "Running diagnostics..."

echo -e "\n${BLUE}=== SERVICE STATUS ===${NC}"
sudo systemctl status fixbulance --no-pager -l

echo -e "\n${BLUE}=== SOCKET FILE CHECK ===${NC}"
if [ -e "$APP_DIR/fixbulance.sock" ]; then
    echo -e "${GREEN}✅ Socket file exists:${NC}"
    ls -la $APP_DIR/fixbulance.sock
else
    echo -e "${RED}❌ Socket file missing${NC}"
fi

echo -e "\n${BLUE}=== RECENT LOGS ===${NC}"
sudo journalctl -u fixbulance --no-pager -n 10

echo -e "\n${BLUE}=== NGINX STATUS ===${NC}"
sudo systemctl status nginx --no-pager

echo -e "\n${BLUE}=== NGINX ERROR CHECK ===${NC}"
sudo tail -n 5 /var/log/nginx/error.log

# =============================================================================
# STEP 10: Final test
# =============================================================================
print_status "Testing application connectivity..."

# Test if socket responds
if [ -e "$APP_DIR/fixbulance.sock" ]; then
    echo "Testing socket connection..."
    timeout 5 bash -c "</dev/tcp/127.0.0.1/80" 2>/dev/null && echo -e "${GREEN}✅ Port 80 accessible${NC}" || echo -e "${YELLOW}⚠️  Port 80 test inconclusive${NC}"
fi

# =============================================================================
# COMPLETION
# =============================================================================
echo
echo -e "${GREEN}🎉 Fix script completed!${NC}"
echo
echo -e "${BLUE}Next Steps:${NC}"
echo "1. Check if website loads: curl -I http://fixbulance.com"
echo "2. If still not working, run: sudo journalctl -u fixbulance -f"
echo "3. For manual restart: sudo systemctl restart fixbulance"
echo
echo -e "${BLUE}Useful Commands:${NC}"
echo "• Check app status: sudo systemctl status fixbulance"
echo "• View live logs: sudo journalctl -u fixbulance -f"
echo "• Restart app: sudo systemctl restart fixbulance"
echo "• Check socket: ls -la /var/www/fixbulance/fixbulance.sock"
echo
if [ -e "$APP_DIR/fixbulance.sock" ]; then
    echo -e "${GREEN}✅ Socket file created successfully!${NC}"
    echo -e "${GREEN}✅ Your website should now be working!${NC}"
else
    echo -e "${YELLOW}⚠️  Socket file not found. Check the logs above for errors.${NC}"
fi 