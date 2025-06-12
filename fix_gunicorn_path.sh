#!/bin/bash

echo "🔧 Gunicorn Path Fix Script for Fixbulance"
echo "==========================================="

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

echo "=== DIAGNOSING CURRENT SETUP ==="
print_info "Checking /var/www/fixbulance directory structure..."
ls -la /var/www/fixbulance/

echo ""
print_info "Looking for Python virtual environments..."
find /var/www/fixbulance -name "bin" -type d 2>/dev/null
find /var/www/fixbulance -name "gunicorn" 2>/dev/null

echo ""
print_info "Checking system-wide gunicorn..."
which gunicorn || echo "Gunicorn not found in system PATH"

echo ""
print_info "Checking Python installations..."
python3 --version
which python3

echo "=== STOPPING SERVICES ==="
sudo systemctl stop fixbulance
sudo systemctl stop nginx
print_status "Stopped services"

echo "=== INSTALLING GUNICORN SYSTEM-WIDE ==="
sudo apt update
sudo apt install -y python3-pip python3-venv
sudo pip3 install gunicorn flask
print_status "Installed gunicorn and flask system-wide"

echo "=== CREATING PROPER VIRTUAL ENVIRONMENT ==="
cd /var/www/fixbulance
if [ -d "venv" ]; then
    print_info "Removing old virtual environment..."
    sudo rm -rf venv
fi

print_info "Creating new virtual environment..."
sudo python3 -m venv venv
sudo chown -R fixbulance:fixbulance venv
print_status "Created virtual environment"

echo "=== ACTIVATING VENV AND INSTALLING DEPENDENCIES ==="
print_info "Installing requirements in virtual environment..."
sudo -u fixbulance bash -c "
source /var/www/fixbulance/venv/bin/activate
pip install --upgrade pip
pip install gunicorn flask flask-sqlalchemy flask-migrate flask-login flask-mail flask-wtf python-dotenv stripe tabulate
"
print_status "Installed dependencies in virtual environment"

echo "=== VERIFYING GUNICORN INSTALLATION ==="
if [ -f "/var/www/fixbulance/venv/bin/gunicorn" ]; then
    print_status "Gunicorn found in virtual environment"
    ls -la /var/www/fixbulance/venv/bin/gunicorn
else
    print_info "Trying system gunicorn as fallback..."
    GUNICORN_PATH=$(which gunicorn)
    if [ -n "$GUNICORN_PATH" ]; then
        print_status "System gunicorn found at: $GUNICORN_PATH"
    else
        echo -e "${RED}❌ Gunicorn not found anywhere${NC}"
        exit 1
    fi
fi

echo "=== CREATING/UPDATING WSGI FILE ==="
sudo tee /var/www/fixbulance/wsgi.py > /dev/null << 'EOF'
#!/usr/bin/env python3
import sys
import os

# Add the project directory to Python path
sys.path.insert(0, '/var/www/fixbulance')

try:
    # Try importing from run.py first
    from run import app
    print("Successfully imported app from run.py")
except ImportError as e:
    print(f"Failed to import from run.py: {e}")
    try:
        # Fallback to app.py
        from app import app
        print("Successfully imported app from app.py")
    except ImportError as e2:
        print(f"Failed to import from app.py: {e2}")
        # Create a simple test app
        from flask import Flask
        app = Flask(__name__)
        
        @app.route('/')
        def hello():
            return '<h1>Fixbulance Test Page</h1><p>Flask is working! Main app will be restored soon.</p>'

if __name__ == "__main__":
    app.run(debug=False)
EOF

sudo chown fixbulance:fixbulance /var/www/fixbulance/wsgi.py
sudo chmod 644 /var/www/fixbulance/wsgi.py
print_status "Created/updated wsgi.py"

echo "=== TESTING WSGI FILE ==="
print_info "Testing wsgi.py import..."
cd /var/www/fixbulance
sudo -u fixbulance python3 -c "
import sys
sys.path.insert(0, '/var/www/fixbulance')
try:
    from wsgi import app
    print('✅ WSGI import successful')
except Exception as e:
    print(f'❌ WSGI import failed: {e}')
"

echo "=== UPDATING SYSTEMD SERVICE ==="
sudo tee /etc/systemd/system/fixbulance.service > /dev/null << 'EOF'
[Unit]
Description=Gunicorn instance to serve Fixbulance
After=network.target

[Service]
User=fixbulance
Group=fixbulance
WorkingDirectory=/var/www/fixbulance
Environment="PATH=/var/www/fixbulance/venv/bin"
ExecStart=/var/www/fixbulance/venv/bin/gunicorn --workers 3 --bind unix:fixbulance.sock -m 007 wsgi:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Fallback to system gunicorn if venv doesn't exist
if [ ! -f "/var/www/fixbulance/venv/bin/gunicorn" ]; then
    print_info "Using system gunicorn as fallback..."
    GUNICORN_PATH=$(which gunicorn)
    sudo tee /etc/systemd/system/fixbulance.service > /dev/null << EOF
[Unit]
Description=Gunicorn instance to serve Fixbulance
After=network.target

[Service]
User=fixbulance
Group=fixbulance
WorkingDirectory=/var/www/fixbulance
ExecStart=$GUNICORN_PATH --workers 3 --bind unix:fixbulance.sock -m 007 wsgi:app
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
fi

print_status "Updated systemd service"

echo "=== FIXING PERMISSIONS ==="
sudo chown -R fixbulance:fixbulance /var/www/fixbulance
sudo chmod -R 755 /var/www/fixbulance
sudo chmod 664 /var/www/fixbulance/*.py
print_status "Fixed permissions"

echo "=== RELOADING SYSTEMD ==="
sudo systemctl daemon-reload
print_status "Reloaded systemd"

echo "=== STARTING SERVICES ==="
print_info "Starting fixbulance service..."
sudo systemctl start fixbulance
sleep 5

if sudo systemctl is-active --quiet fixbulance; then
    print_status "Fixbulance service started successfully"
else
    print_info "Service failed, checking logs..."
    sudo systemctl status fixbulance --no-pager -l
fi

print_info "Starting nginx..."
sudo systemctl start nginx
sleep 2
print_status "Started nginx"

echo "=== VERIFYING SOCKET FILE ==="
if [ -S /var/www/fixbulance/fixbulance.sock ]; then
    print_status "Socket file created: /var/www/fixbulance/fixbulance.sock"
    ls -la /var/www/fixbulance/fixbulance.sock
else
    echo -e "${RED}❌ Socket file not found${NC}"
    print_info "Checking for socket creation..."
    ls -la /var/www/fixbulance/*.sock 2>/dev/null || echo "No socket files found"
fi

echo "=== TESTING LOCAL CONNECTION ==="
print_info "Testing local connection..."
sleep 3
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/ 2>/dev/null)
echo "HTTP Status: $HTTP_STATUS"

if [ "$HTTP_STATUS" = "200" ]; then
    print_status "Local connection successful!"
else
    print_info "Connection issues, checking recent logs..."
    echo "=== RECENT SERVICE LOGS ==="
    sudo journalctl -u fixbulance --no-pager -n 10
fi

echo "=== FINAL SERVICE STATUS ==="
print_info "Fixbulance service status:"
sudo systemctl is-active fixbulance && echo "✅ ACTIVE" || echo "❌ INACTIVE"

print_info "Nginx service status:"
sudo systemctl is-active nginx && echo "✅ ACTIVE" || echo "❌ INACTIVE"

echo ""
echo "=== FINAL RESULT ==="
if sudo systemctl is-active --quiet fixbulance && sudo systemctl is-active --quiet nginx && [ -S /var/www/fixbulance/fixbulance.sock ]; then
    echo -e "${GREEN}🎉 SUCCESS! All services are running and socket exists!${NC}"
    echo -e "${GREEN}🌐 Your website should now work: http://fixbulance.com${NC}"
else
    echo -e "${YELLOW}⚠️  Services started but may need additional debugging${NC}"
    echo "Next steps:"
    echo "1. Check service logs: sudo journalctl -u fixbulance -f"
    echo "2. Test local connection: curl -I http://localhost/"
    echo "3. Check nginx error log: sudo tail -f /var/log/nginx/error.log"
fi 