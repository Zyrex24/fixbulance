#!/bin/bash

echo "🔧 Socket Permissions Fix Script for Fixbulance"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
    else
        echo -e "${RED}❌ $1${NC}"
    fi
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

echo "=== DIAGNOSING CURRENT SOCKET ISSUE ==="
print_info "Checking nginx user and groups..."
echo "Nginx user: $(ps aux | grep nginx | grep -v grep | head -1 | awk '{print $1}')"
echo "Nginx groups: $(groups www-data 2>/dev/null || echo 'www-data user not found')"

print_info "Checking fixbulance user and groups..."
echo "Fixbulance user exists: $(id fixbulance 2>/dev/null && echo 'yes' || echo 'no')"
if id fixbulance >/dev/null 2>&1; then
    echo "Fixbulance groups: $(groups fixbulance)"
fi

print_info "Current socket file permissions..."
if [ -S "/var/www/fixbulance/fixbulance.sock" ]; then
    ls -la /var/www/fixbulance/fixbulance.sock
else
    echo "No socket file found"
fi

echo "=== STOPPING SERVICES ==="
sudo systemctl stop nginx
sudo systemctl stop fixbulance
print_status "Stopped services"

echo "=== ADDING NGINX USER TO FIXBULANCE GROUP ==="
sudo usermod -a -G fixbulance www-data
print_status "Added www-data to fixbulance group"

print_info "Verifying group membership..."
groups www-data

echo "=== CLEANING UP OLD SOCKET ==="
sudo rm -f /var/www/fixbulance/fixbulance.sock
print_status "Removed old socket file"

echo "=== UPDATING SYSTEMD SERVICE FOR CORRECT PERMISSIONS ==="
sudo tee /etc/systemd/system/fixbulance.service > /dev/null << 'EOF'
[Unit]
Description=Gunicorn instance to serve Fixbulance
After=network.target

[Service]
User=fixbulance
Group=fixbulance
WorkingDirectory=/var/www/fixbulance
Environment="PATH=/var/www/fixbulance/venv/bin"
Environment="PYTHONPATH=/var/www/fixbulance"
EnvironmentFile=/var/www/fixbulance/.env
ExecStart=/var/www/fixbulance/venv/bin/gunicorn --workers 3 --bind unix:fixbulance.sock --umask 0007 --access-logfile /var/www/fixbulance/logs/access.log --error-logfile /var/www/fixbulance/logs/error.log wsgi:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
print_status "Updated systemd service with correct umask"

echo "=== UPDATING NGINX CONFIGURATION ==="
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
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 8k;
        proxy_buffers 8 8k;
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
print_status "Updated nginx configuration"

echo "=== RELOADING SYSTEMD ==="
sudo systemctl daemon-reload
print_status "Reloaded systemd"

echo "=== STARTING FIXBULANCE SERVICE ==="
sudo systemctl start fixbulance
sleep 5

if sudo systemctl is-active --quiet fixbulance; then
    print_status "Fixbulance service started"
else
    echo -e "${RED}❌ Fixbulance service failed to start${NC}"
    sudo journalctl -u fixbulance --no-pager -n 10
    exit 1
fi

echo "=== VERIFYING SOCKET CREATION ==="
sleep 3
if [ -S "/var/www/fixbulance/fixbulance.sock" ]; then
    print_status "Socket file created"
    ls -la /var/www/fixbulance/fixbulance.sock
    
    print_info "Checking socket permissions..."
    SOCKET_PERMS=$(stat -c "%a" /var/www/fixbulance/fixbulance.sock)
    echo "Socket permissions: $SOCKET_PERMS"
    
    SOCKET_GROUP=$(stat -c "%G" /var/www/fixbulance/fixbulance.sock)
    echo "Socket group: $SOCKET_GROUP"
else
    echo -e "${RED}❌ Socket file was not created${NC}"
    exit 1
fi

echo "=== TESTING SOCKET ACCESS ==="
print_info "Testing if www-data can access the socket..."
sudo -u www-data test -r /var/www/fixbulance/fixbulance.sock && echo "✅ www-data can read socket" || echo "❌ www-data cannot read socket"
sudo -u www-data test -w /var/www/fixbulance/fixbulance.sock && echo "✅ www-data can write socket" || echo "❌ www-data cannot write socket"

echo "=== RESTARTING NGINX WITH NEW PERMISSIONS ==="
sudo systemctl restart nginx
sleep 3

if sudo systemctl is-active --quiet nginx; then
    print_status "Nginx restarted successfully"
else
    echo -e "${RED}❌ Nginx failed to restart${NC}"
    sudo journalctl -u nginx --no-pager -n 10
    exit 1
fi

echo "=== TESTING CONNECTION ==="
print_info "Waiting for services to fully initialize..."
sleep 5

print_info "Testing local connection..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/ 2>/dev/null)
echo "HTTP Status: $HTTP_STATUS"

if [ "$HTTP_STATUS" = "200" ]; then
    print_status "SUCCESS! Connection working!"
    
    print_info "Testing actual response..."
    echo "First 10 lines of response:"
    curl -s http://localhost/ | head -10
    
    echo ""
    echo -e "${GREEN}🎉 WEBSITE IS NOW WORKING! 🎉${NC}"
    echo -e "${GREEN}🌐 Your website should be accessible at:${NC}"
    echo -e "${GREEN}   • http://fixbulance.com${NC}"
    echo -e "${GREEN}   • http://72.146.184.2${NC}"
    
else
    print_info "Still getting errors, checking new logs..."
    echo ""
    echo "=== RECENT NGINX ERROR LOG ==="
    sudo tail -5 /var/log/nginx/error.log
    
    echo ""
    echo "=== RECENT GUNICORN LOGS ==="
    sudo journalctl -u fixbulance --no-pager -n 5
    
    echo ""
    echo "=== SOCKET CONNECTIVITY TEST ==="
    print_info "Testing direct socket connection..."
    echo -e "GET / HTTP/1.1\r\nHost: localhost\r\n\r\n" | socat - UNIX-CONNECT:/var/www/fixbulance/fixbulance.sock | head -5
fi

echo ""
echo "=== FINAL SERVICE STATUS ==="
echo "Fixbulance: $(sudo systemctl is-active fixbulance)"
echo "Nginx: $(sudo systemctl is-active nginx)"

echo ""
echo "=== DEBUGGING COMMANDS ==="
echo "If issues persist, use these commands:"
echo "1. Check real-time nginx errors: sudo tail -f /var/log/nginx/error.log"
echo "2. Check real-time app logs: sudo journalctl -u fixbulance -f"
echo "3. Test socket directly: echo 'GET / HTTP/1.1' | socat - UNIX-CONNECT:/var/www/fixbulance/fixbulance.sock"
echo "4. Check groups: groups www-data" 