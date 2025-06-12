#!/bin/bash

echo "🔧 Flask Application Import Fix Script"
echo "======================================"

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

cd /var/www/fixbulance

echo "=== DIAGNOSING FLASK APP STRUCTURE ==="
print_info "Checking main application files..."
ls -la *.py

echo ""
print_info "Checking if dependencies are properly installed in venv..."
source venv/bin/activate
python3 -c "
import sys
print('Python path:', sys.path)
try:
    import flask_sqlalchemy
    print('✅ flask_sqlalchemy available')
except ImportError as e:
    print('❌ flask_sqlalchemy not available:', e)

try:
    import flask_migrate
    print('✅ flask_migrate available')
except ImportError as e:
    print('❌ flask_migrate not available:', e)

try:
    import flask_login
    print('✅ flask_login available')
except ImportError as e:
    print('❌ flask_login not available:', e)
"

echo ""
print_info "Testing run.py import..."
source venv/bin/activate
python3 -c "
import sys
sys.path.insert(0, '/var/www/fixbulance')
try:
    from run import app
    print('✅ Successfully imported app from run.py')
    print('App name:', app.name)
    print('App debug:', app.debug)
except Exception as e:
    print('❌ Failed to import from run.py:', str(e))
    import traceback
    traceback.print_exc()
"

echo ""
print_info "Testing app.py import..."
source venv/bin/activate
python3 -c "
import sys
sys.path.insert(0, '/var/www/fixbulance')
try:
    from app import app
    print('✅ Successfully imported app from app.py')
    print('App name:', app.name)
    print('App debug:', app.debug)
except Exception as e:
    print('❌ Failed to import from app.py:', str(e))
    import traceback
    traceback.print_exc()
"

echo "=== STOPPING SERVICES ==="
sudo systemctl stop fixbulance
sudo systemctl stop nginx
print_status "Stopped services"

echo "=== CREATING ROBUST WSGI FILE ==="
sudo tee /var/www/fixbulance/wsgi.py > /dev/null << 'EOF'
#!/usr/bin/env python3
import sys
import os
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add the project directory to Python path
project_dir = '/var/www/fixbulance'
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

logger.info(f"Python path: {sys.path}")
logger.info(f"Working directory: {os.getcwd()}")

# Change to the project directory
os.chdir(project_dir)

app = None

# Try importing the main application
try:
    logger.info("Attempting to import from run.py...")
    from run import app
    logger.info("✅ Successfully imported app from run.py")
except Exception as e:
    logger.error(f"❌ Failed to import from run.py: {e}")
    try:
        logger.info("Attempting to import from app.py...")
        from app import app
        logger.info("✅ Successfully imported app from app.py")
    except Exception as e2:
        logger.error(f"❌ Failed to import from app.py: {e2}")
        
        # Create a diagnostic Flask app
        try:
            from flask import Flask, jsonify
            app = Flask(__name__)
            
            @app.route('/')
            def diagnostic():
                return '''
                <html>
                <head><title>Fixbulance - Diagnostic Mode</title></head>
                <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px;">
                    <h1 style="color: #e74c3c;">🔧 Fixbulance - Diagnostic Mode</h1>
                    <p><strong>Status:</strong> Flask is running but the main application failed to load.</p>
                    <p><strong>Issue:</strong> Import errors with the main Fixbulance application.</p>
                    <p><strong>Next Steps:</strong> Please check the application logs and ensure all dependencies are installed.</p>
                    <hr>
                    <p><em>This is a temporary diagnostic page. Your main application will be restored once the import issues are resolved.</em></p>
                </body>
                </html>
                '''
            
            @app.route('/health')
            def health():
                return jsonify({
                    'status': 'diagnostic_mode',
                    'message': 'Flask is running but main app failed to import'
                })
                
            logger.info("✅ Created diagnostic Flask app")
        except Exception as e3:
            logger.error(f"❌ Failed to create diagnostic app: {e3}")
            raise

if app is None:
    raise RuntimeError("Failed to create any Flask application")

# Ensure app is configured for production
if hasattr(app, 'config'):
    app.config['DEBUG'] = False

logger.info(f"Final app object: {app}")
logger.info(f"App name: {getattr(app, 'name', 'unknown')}")

if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0', port=5000)
EOF

sudo chown fixbulance:fixbulance /var/www/fixbulance/wsgi.py
sudo chmod 644 /var/www/fixbulance/wsgi.py
print_status "Created robust WSGI file"

echo "=== TESTING NEW WSGI FILE ==="
print_info "Testing WSGI import with virtual environment..."
cd /var/www/fixbulance
sudo -u fixbulance bash -c "
source venv/bin/activate
export PYTHONPATH=/var/www/fixbulance:$PYTHONPATH
python3 -c '
import sys
sys.path.insert(0, \"/var/www/fixbulance\")
try:
    from wsgi import app
    print(\"✅ WSGI import successful\")
    print(\"App:\", app)
    print(\"App name:\", getattr(app, \"name\", \"unknown\"))
except Exception as e:
    print(\"❌ WSGI import failed:\", str(e))
    import traceback
    traceback.print_exc()
'
"

echo "=== CHECKING DATABASE CONFIGURATION ==="
print_info "Checking if database files exist..."
if [ -f "/var/www/fixbulance/instance/fixbulance.db" ]; then
    print_status "SQLite database found"
    ls -la /var/www/fixbulance/instance/fixbulance.db
else
    print_info "No SQLite database found, checking for PostgreSQL config..."
    if grep -q "postgresql" /var/www/fixbulance/.env 2>/dev/null; then
        echo "PostgreSQL configuration detected in .env"
    else
        echo "No database configuration detected"
    fi
fi

echo "=== FIXING ENVIRONMENT VARIABLES ==="
print_info "Ensuring .env file is readable..."
if [ -f "/var/www/fixbulance/.env" ]; then
    sudo chown fixbulance:fixbulance /var/www/fixbulance/.env
    sudo chmod 644 /var/www/fixbulance/.env
    print_status "Fixed .env permissions"
else
    print_info "No .env file found, creating basic one..."
    sudo tee /var/www/fixbulance/.env > /dev/null << 'EOF'
FLASK_APP=wsgi.py
FLASK_ENV=production
SECRET_KEY=your-secret-key-change-this
DATABASE_URL=sqlite:///instance/fixbulance.db
EOF
    sudo chown fixbulance:fixbulance /var/www/fixbulance/.env
    sudo chmod 644 /var/www/fixbulance/.env
    print_status "Created basic .env file"
fi

echo "=== UPDATING SYSTEMD SERVICE WITH ENVIRONMENT ==="
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
ExecStart=/var/www/fixbulance/venv/bin/gunicorn --workers 3 --bind unix:fixbulance.sock -m 007 --access-logfile /var/www/fixbulance/logs/access.log --error-logfile /var/www/fixbulance/logs/error.log wsgi:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
print_status "Updated systemd service with environment and logging"

echo "=== CREATING LOG DIRECTORY ==="
if [ ! -d "/var/www/fixbulance/logs" ]; then
    sudo mkdir -p /var/www/fixbulance/logs
    sudo chown fixbulance:fixbulance /var/www/fixbulance/logs
    sudo chmod 755 /var/www/fixbulance/logs
    print_status "Created logs directory"
fi

echo "=== RELOADING SYSTEMD ==="
sudo systemctl daemon-reload
print_status "Reloaded systemd"

echo "=== STARTING SERVICES ==="
print_info "Starting fixbulance service..."
sudo systemctl start fixbulance
sleep 5

print_info "Checking service status..."
if sudo systemctl is-active --quiet fixbulance; then
    print_status "Fixbulance service is running"
else
    echo -e "${RED}❌ Service failed to start${NC}"
    print_info "Checking service logs..."
    sudo journalctl -u fixbulance --no-pager -n 20
fi

print_info "Starting nginx..."
sudo systemctl start nginx
sleep 2
print_status "Started nginx"

echo "=== VERIFYING SOCKET AND CONNECTION ==="
if [ -S /var/www/fixbulance/fixbulance.sock ]; then
    print_status "Socket file exists"
    ls -la /var/www/fixbulance/fixbulance.sock
else
    echo -e "${RED}❌ Socket file not found${NC}"
fi

print_info "Testing local connection..."
sleep 3
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/ 2>/dev/null)
echo "HTTP Status: $HTTP_STATUS"

if [ "$HTTP_STATUS" = "200" ]; then
    print_status "Connection successful!"
    print_info "Testing actual response..."
    curl -s http://localhost/ | head -20
else
    print_info "Still getting errors, checking logs..."
    if [ -f "/var/www/fixbulance/logs/error.log" ]; then
        echo "=== GUNICORN ERROR LOG ==="
        tail -20 /var/www/fixbulance/logs/error.log
    fi
    
    echo "=== NGINX ERROR LOG ==="
    sudo tail -10 /var/log/nginx/error.log
fi

echo "=== FINAL STATUS ==="
print_info "Service status:"
sudo systemctl is-active fixbulance nginx

if sudo systemctl is-active --quiet fixbulance && sudo systemctl is-active --quiet nginx; then
    if [ "$HTTP_STATUS" = "200" ]; then
        echo -e "${GREEN}🎉 SUCCESS! Your website should now be fully working!${NC}"
        echo -e "${GREEN}🌐 Test it at: http://fixbulance.com${NC}"
    else
        echo -e "${YELLOW}⚠️  Services running but still troubleshooting connection${NC}"
        echo "The diagnostic page should help identify remaining issues"
    fi
else
    echo -e "${RED}❌ Some services are not running properly${NC}"
fi

echo ""
echo "=== DEBUG INFORMATION ==="
echo "Check these if issues persist:"
echo "1. Service logs: sudo journalctl -u fixbulance -f"
echo "2. Gunicorn errors: tail -f /var/www/fixbulance/logs/error.log"
echo "3. Nginx errors: sudo tail -f /var/log/nginx/error.log"
echo "4. Test direct app: cd /var/www/fixbulance && source venv/bin/activate && python3 wsgi.py" 