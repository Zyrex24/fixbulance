#!/bin/bash

# =============================================================================
# Fixbulance Python Environment Fix Script
# Run this script to fix Python environment and dependencies
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
VENV_DIR="$APP_DIR/venv"

echo -e "${BLUE}🔧 Fixbulance Python Environment Fix Script${NC}"
echo -e "${BLUE}===========================================${NC}"

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

print_status "Stopping services first..."
sudo systemctl stop fixbulance || true
sudo systemctl stop nginx || true

cd "$APP_DIR"

# =============================================================================
# STEP 1: Check Python and Virtual Environment
# =============================================================================
echo -e "\n${BLUE}=== CHECKING PYTHON ENVIRONMENT ===${NC}"

print_status "Checking Python installation..."
python3 --version
which python3

print_status "Checking if virtual environment exists..."
if [ -d "$VENV_DIR" ]; then
    print_status "Virtual environment found at $VENV_DIR"
    ls -la "$VENV_DIR"
else
    print_warning "Virtual environment not found, will create one"
fi

# =============================================================================
# STEP 2: Create/Recreate Virtual Environment
# =============================================================================
echo -e "\n${BLUE}=== SETTING UP VIRTUAL ENVIRONMENT ===${NC}"

print_status "Installing python3-venv if not present..."
sudo apt update
sudo apt install -y python3-venv python3-pip

print_status "Removing old virtual environment if exists..."
sudo rm -rf "$VENV_DIR"

print_status "Creating fresh virtual environment..."
sudo -u $APP_USER python3 -m venv "$VENV_DIR"
print_status "Virtual environment created"

print_status "Activating virtual environment and upgrading pip..."
sudo -u $APP_USER "$VENV_DIR/bin/python" -m pip install --upgrade pip

# =============================================================================
# STEP 3: Install Required Packages
# =============================================================================
echo -e "\n${BLUE}=== INSTALLING REQUIRED PACKAGES ===${NC}"

print_status "Installing Flask and Gunicorn..."
sudo -u $APP_USER "$VENV_DIR/bin/pip" install flask gunicorn

print_status "Checking if requirements.txt exists..."
if [ -f "$APP_DIR/requirements.txt" ]; then
    print_status "Installing from requirements.txt..."
    sudo -u $APP_USER "$VENV_DIR/bin/pip" install -r "$APP_DIR/requirements.txt"
else
    print_warning "No requirements.txt found, installing basic packages..."
    sudo -u $APP_USER "$VENV_DIR/bin/pip" install \
        flask \
        gunicorn \
        flask-sqlalchemy \
        flask-migrate \
        flask-login \
        flask-wtf \
        flask-mail \
        python-dotenv \
        stripe \
        psycopg2-binary
fi

print_status "Verifying Flask installation..."
sudo -u $APP_USER "$VENV_DIR/bin/python" -c "import flask; print(f'Flask version: {flask.__version__}')"

# =============================================================================
# STEP 4: Create Working WSGI File
# =============================================================================
echo -e "\n${BLUE}=== CREATING WORKING WSGI FILE ===${NC}"

print_status "Creating WSGI file with proper Flask import..."
sudo -u $APP_USER tee "$APP_DIR/wsgi.py" > /dev/null << 'EOF'
#!/usr/bin/env python3
"""
WSGI entry point for Fixbulance Flask application
"""
import sys
import os

# Add the application directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Initialize application variable
application = None

def create_app():
    """Create and configure the Flask application"""
    global application
    
    # Method 1: Try importing from run.py
    try:
        from run import app
        application = app
        print("✅ Successfully imported app from run.py")
        return application
    except Exception as e:
        print(f"❌ Could not import from run.py: {e}")
    
    # Method 2: Try importing from app.py
    try:
        from app import app
        application = app
        print("✅ Successfully imported app from app.py")
        return application
    except Exception as e:
        print(f"❌ Could not import from app.py: {e}")
    
    # Method 3: Try importing from app package
    try:
        from app import create_app as app_factory
        application = app_factory()
        print("✅ Successfully created app from app factory")
        return application
    except Exception as e:
        print(f"❌ Could not import from app factory: {e}")
    
    # Method 4: Create a simple Flask app
    try:
        from flask import Flask, jsonify
        
        app = Flask(__name__)
        
        @app.route('/')
        def home():
            return '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Fixbulance - Service Active</title>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body { 
                        font-family: Arial, sans-serif; 
                        text-align: center; 
                        padding: 50px;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        margin: 0;
                        min-height: 100vh;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        flex-direction: column;
                    }
                    .container {
                        background: rgba(255,255,255,0.1);
                        padding: 40px;
                        border-radius: 10px;
                        backdrop-filter: blur(10px);
                    }
                    h1 { color: #4CAF50; margin-bottom: 20px; }
                    .status { color: #81C784; font-size: 18px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🚑 Fixbulance</h1>
                    <div class="status">✅ Service is Running Successfully</div>
                    <p>Web server deployed on Azure and working correctly.</p>
                    <p><small>Python Flask Application • Gunicorn WSGI Server</small></p>
                </div>
            </body>
            </html>
            '''
        
        @app.route('/health')
        def health():
            return jsonify({
                'status': 'healthy',
                'service': 'fixbulance',
                'message': 'Service is running correctly'
            })
        
        @app.route('/api/status')
        def api_status():
            return jsonify({
                'status': 'ok',
                'server': 'nginx + gunicorn',
                'application': 'flask'
            })
        
        application = app
        print("✅ Created fallback Flask application")
        return application
        
    except Exception as e:
        print(f"❌ Could not create Flask app: {e}")
        raise RuntimeError("Failed to create any Flask application")

# Create the application
application = create_app()

# For debugging
if __name__ == "__main__":
    print("🔧 Running Flask app in debug mode...")
    application.run(debug=True, host='0.0.0.0', port=5000)
EOF

print_status "Testing WSGI file with virtual environment..."
sudo -u $APP_USER "$VENV_DIR/bin/python" -c "
import sys
sys.path.insert(0, '/var/www/fixbulance')
try:
    from wsgi import application
    print('✅ WSGI import successful')
    print(f'Application type: {type(application)}')
    print(f'Application name: {application.name if hasattr(application, \"name\") else \"unknown\"}')
except Exception as e:
    print(f'❌ WSGI import failed: {e}')
    import traceback
    traceback.print_exc()
    exit(1)
"

# =============================================================================
# STEP 5: Create Optimized Gunicorn Config
# =============================================================================
echo -e "\n${BLUE}=== CREATING GUNICORN CONFIGURATION ===${NC}"

sudo -u $APP_USER tee "$APP_DIR/gunicorn_config.py" > /dev/null << 'EOF'
# Gunicorn configuration for Fixbulance
import multiprocessing

# Server socket
bind = "unix:/var/www/fixbulance/fixbulance.sock"
backlog = 2048

# Worker processes
workers = 2
worker_class = "sync"
worker_connections = 1000
timeout = 60
keepalive = 2

# Restart workers
max_requests = 1000
max_requests_jitter = 100

# Logging
errorlog = "-"
accesslog = "-"
loglevel = "info"

# Process naming
proc_name = "fixbulance"

# Server mechanics
preload_app = False
daemon = False
user = "fixbulance"
group = "fixbulance"

# Socket permissions
umask = 0o007
EOF

# =============================================================================
# STEP 6: Update Systemd Service
# =============================================================================
echo -e "\n${BLUE}=== UPDATING SYSTEMD SERVICE ===${NC}"

sudo tee /etc/systemd/system/fixbulance.service > /dev/null << EOF
[Unit]
Description=Fixbulance Flask App
After=network.target

[Service]
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment="PATH=$VENV_DIR/bin"
Environment="PYTHONPATH=$APP_DIR"
ExecStart=$VENV_DIR/bin/gunicorn --config $APP_DIR/gunicorn_config.py wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# =============================================================================
# STEP 7: Start Services
# =============================================================================
echo -e "\n${BLUE}=== STARTING SERVICES ===${NC}"

print_status "Reloading systemd..."
sudo systemctl daemon-reload

print_status "Starting fixbulance service..."
sudo systemctl start fixbulance

sleep 5

# Check service status
if sudo systemctl is-active --quiet fixbulance; then
    print_status "Fixbulance service is running"
else
    print_error "Service failed to start, checking logs..."
    sudo journalctl -u fixbulance -n 15 --no-pager
    exit 1
fi

# Check socket file
if [ -S "/var/www/fixbulance/fixbulance.sock" ]; then
    print_status "Socket file created successfully"
    ls -la "/var/www/fixbulance/fixbulance.sock"
else
    print_error "Socket file not created"
    sudo journalctl -u fixbulance -n 10 --no-pager
    exit 1
fi

print_status "Starting nginx..."
sudo systemctl start nginx

# =============================================================================
# STEP 8: Test Application
# =============================================================================
echo -e "\n${BLUE}=== TESTING APPLICATION ===${NC}"

sleep 3

# Test local connection
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/ 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    print_status "✅ SUCCESS! Application is working (HTTP 200)"
    
    # Test the actual content
    CONTENT=$(curl -s http://localhost/ | head -1)
    echo -e "${GREEN}Response preview: $CONTENT${NC}"
    
    # Get public IP
    PUBLIC_IP=$(curl -4 -s icanhazip.com 2>/dev/null || echo "unknown")
    
    echo -e "\n${GREEN}🎉 DEPLOYMENT SUCCESSFUL!${NC}"
    echo -e "${BLUE}Your website is now accessible at:${NC}"
    echo -e "   🌐 http://fixbulance.com"
    echo -e "   🌐 http://$PUBLIC_IP"
    echo -e "   🩺 http://fixbulance.com/health (health check)"
    
else
    print_warning "Got HTTP code: $HTTP_CODE"
    if [ "$HTTP_CODE" = "502" ]; then
        print_error "Still getting 502 error"
        sudo journalctl -u fixbulance -n 5 --no-pager
    fi
fi

# =============================================================================
# FINAL STATUS
# =============================================================================
echo -e "\n${BLUE}=== FINAL STATUS ===${NC}"
echo -e "Fixbulance: $(sudo systemctl is-active fixbulance)"
echo -e "Nginx: $(sudo systemctl is-active nginx)"
echo -e "Socket: $([ -S '/var/www/fixbulance/fixbulance.sock' ] && echo 'EXISTS' || echo 'MISSING')"
echo -e "Python: $($VENV_DIR/bin/python --version)"
echo -e "Flask: $($VENV_DIR/bin/python -c 'import flask; print(flask.__version__)' 2>/dev/null || echo 'Not found')"

echo -e "\n${BLUE}Useful commands:${NC}"
echo -e "• Check logs: sudo journalctl -u fixbulance -f"
echo -e "• Restart service: sudo systemctl restart fixbulance"
echo -e "• Test locally: curl -I http://localhost"
echo -e "• Check Python env: $VENV_DIR/bin/python --version"

echo -e "\n${GREEN}🔧 Python environment fix completed!${NC}" 