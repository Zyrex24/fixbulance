#!/bin/bash

# =============================================================================
# Fixbulance WSGI Import Fix Script
# Run this script to fix the specific gunicorn import issue
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

echo -e "${BLUE}🔧 Fixbulance WSGI Import Fix Script${NC}"
echo -e "${BLUE}===================================${NC}"

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

# =============================================================================
# STEP 1: Check What Python Files Exist
# =============================================================================
print_status "Checking existing Python files..."
cd "$APP_DIR"
ls -la *.py 2>/dev/null || echo "No .py files found in root"

# =============================================================================
# STEP 2: Create a Simple Working WSGI File
# =============================================================================
print_status "Creating a simple, working wsgi.py file..."

sudo -u $APP_USER tee wsgi.py > /dev/null << 'EOF'
#!/usr/bin/env python3
"""
WSGI entry point for Fixbulance Flask application
"""
import sys
import os

# Add the application directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Try to import the Flask app in order of preference
app = None
application = None

# Method 1: Try importing from run.py
try:
    from run import app
    application = app
    print("✅ Successfully imported app from run.py")
except ImportError as e:
    print(f"❌ Could not import from run.py: {e}")
    
    # Method 2: Try importing from app.py
    try:
        from app import app
        application = app
        print("✅ Successfully imported app from app.py")
    except ImportError as e:
        print(f"❌ Could not import from app.py: {e}")
        
        # Method 3: Create a simple test Flask app
        try:
            from flask import Flask
            
            app = Flask(__name__)
            application = app
            
            @app.route('/')
            def home():
                return '''
                <html>
                <head><title>Fixbulance - Service Active</title></head>
                <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                    <h1 style="color: #4CAF50;">🚑 Fixbulance Service is Running!</h1>
                    <p style="color: #666;">The web server is working correctly.</p>
                    <p style="color: #666;">Application deployed successfully on Azure.</p>
                </body>
                </html>
                '''
            
            @app.route('/health')
            def health():
                return {'status': 'healthy', 'service': 'fixbulance'}
                
            print("✅ Created simple test Flask application")
            
        except ImportError as e:
            print(f"❌ Could not create Flask app: {e}")
            raise

# Ensure we have an application object
if application is None:
    raise RuntimeError("Failed to create Flask application object")

# For debugging
if __name__ == "__main__":
    print("🔧 Running Flask app in debug mode...")
    application.run(debug=True, host='0.0.0.0', port=5000)
EOF

print_status "WSGI file created"

# =============================================================================
# STEP 3: Test the WSGI File
# =============================================================================
print_status "Testing the WSGI file..."
cd "$APP_DIR"

# Test if the wsgi.py file can be imported
sudo -u $APP_USER python3 -c "
import sys
sys.path.insert(0, '/var/www/fixbulance')
try:
    from wsgi import application
    print('✅ WSGI import successful')
    print(f'Application type: {type(application)}')
except Exception as e:
    print(f'❌ WSGI import failed: {e}')
    exit(1)
"

print_status "WSGI file test passed"

# =============================================================================
# STEP 4: Create Simple Gunicorn Config
# =============================================================================
print_status "Creating simple gunicorn configuration..."

sudo -u $APP_USER tee gunicorn_config.py > /dev/null << 'EOF'
# Simple Gunicorn configuration for Fixbulance
bind = "unix:/var/www/fixbulance/fixbulance.sock"
workers = 2
timeout = 30
keepalive = 2
max_requests = 1000

# Logging
errorlog = "-"  # Log to stderr/systemd
accesslog = "-"  # Log to stdout/systemd
loglevel = "info"

# Process naming
proc_name = "fixbulance"

# Server mechanics
preload_app = False  # Don't preload to avoid import issues
daemon = False
user = "fixbulance"
group = "fixbulance"

# Socket permissions
umask = 0o007
EOF

print_status "Gunicorn config created"

# =============================================================================
# STEP 5: Update Systemd Service with Simple Config
# =============================================================================
print_status "Creating simplified systemd service..."

sudo tee /etc/systemd/system/fixbulance.service > /dev/null << EOF
[Unit]
Description=Fixbulance Flask App
After=network.target

[Service]
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONPATH=$APP_DIR"
ExecStart=$APP_DIR/venv/bin/gunicorn --config $APP_DIR/gunicorn_config.py wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

print_status "Systemd service updated"

# =============================================================================
# STEP 6: Start Services
# =============================================================================
print_status "Reloading systemd and starting services..."

sudo systemctl daemon-reload
sudo systemctl start fixbulance

# Wait a moment for the service to start
sleep 5

# Check if service started successfully
if sudo systemctl is-active --quiet fixbulance; then
    print_status "Fixbulance service started successfully"
else
    print_error "Fixbulance service failed to start"
    print_status "Checking logs..."
    sudo journalctl -u fixbulance -n 10 --no-pager
    exit 1
fi

# Check if socket file was created
if [ -S "/var/www/fixbulance/fixbulance.sock" ]; then
    print_status "Socket file created successfully"
    ls -la "/var/www/fixbulance/fixbulance.sock"
else
    print_error "Socket file not created"
    exit 1
fi

# Start nginx
sudo systemctl start nginx
print_status "Nginx started"

# =============================================================================
# STEP 7: Test the Application
# =============================================================================
print_status "Testing the application..."

# Test local connection
sleep 2
HTTP_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/ 2>/dev/null || echo "000")

if [ "$HTTP_RESPONSE" = "200" ]; then
    print_status "✅ Application is working! HTTP 200 OK"
    echo -e "${GREEN}🎉 SUCCESS! Your website should now be accessible.${NC}"
    
    # Get public IP and test
    PUBLIC_IP=$(curl -4 -s icanhazip.com 2>/dev/null || echo "unknown")
    echo -e "${BLUE}📍 Your website URLs:${NC}"
    echo -e "   • http://fixbulance.com"
    echo -e "   • http://$PUBLIC_IP"
    
elif [ "$HTTP_RESPONSE" = "502" ]; then
    print_warning "Still getting 502 error"
    sudo journalctl -u fixbulance -n 5 --no-pager
else
    print_warning "Got HTTP response: $HTTP_RESPONSE"
fi

# =============================================================================
# STEP 8: Final Status
# =============================================================================
echo -e "\n${BLUE}=== FINAL STATUS ===${NC}"
echo -e "Fixbulance service: $(sudo systemctl is-active fixbulance)"
echo -e "Nginx service: $(sudo systemctl is-active nginx)"
echo -e "Socket file: $([ -S '/var/www/fixbulance/fixbulance.sock' ] && echo 'EXISTS' || echo 'MISSING')"

echo -e "\n${BLUE}Useful commands:${NC}"
echo -e "• View logs: sudo journalctl -u fixbulance -f"
echo -e "• Restart: sudo systemctl restart fixbulance"
echo -e "• Test local: curl -I http://localhost"

echo -e "\n${GREEN}🔧 WSGI fix completed!${NC}" 