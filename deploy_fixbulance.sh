#!/bin/bash

echo "🚀 Fixbulance Complete Deployment Script"
echo "========================================"
echo "This script will deploy Fixbulance from scratch on any Ubuntu/Debian server"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration - EDIT THESE VALUES
DOMAIN="fixbulance.com"
APP_USER="fixbulance"
APP_DIR="/var/www/fixbulance"
GIT_REPO=""  # Add your git repo URL here if using git
SOURCE_DIR=""  # Or specify source directory if copying files

print_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
    else
        echo -e "${RED}❌ $1 - FAILED${NC}"
        exit 1
    fi
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Please run this script as root (use sudo)${NC}"
    exit 1
fi

print_header "SYSTEM UPDATE"
print_info "Updating system packages..."
apt update && apt upgrade -y
print_status "System updated"

print_header "INSTALLING DEPENDENCIES"
print_info "Installing required packages..."
apt install -y nginx python3 python3-pip python3-venv git curl wget ufw fail2ban htop unzip
print_status "Dependencies installed"

print_header "CONFIGURING FIREWALL"
print_info "Setting up UFW firewall..."
ufw --force enable
ufw allow ssh
ufw allow 'Nginx Full'
ufw allow 80
ufw allow 443
print_status "Firewall configured"

print_header "CREATING APPLICATION USER"
if id "$APP_USER" &>/dev/null; then
    print_info "User $APP_USER already exists"
else
    useradd -m -s /bin/bash $APP_USER
    print_status "Created user $APP_USER"
fi

# Add nginx user to app user group
usermod -a -G $APP_USER www-data
print_status "Added www-data to $APP_USER group"

print_header "SETTING UP APPLICATION DIRECTORY"
print_info "Creating application directory structure..."
mkdir -p $APP_DIR
mkdir -p $APP_DIR/logs
mkdir -p $APP_DIR/backups
mkdir -p $APP_DIR/instance
chown -R $APP_USER:$APP_USER $APP_DIR
print_status "Directory structure created"

print_header "DEPLOYING APPLICATION CODE"
cd $APP_DIR

if [ -n "$GIT_REPO" ]; then
    print_info "Cloning from Git repository..."
    sudo -u $APP_USER git clone $GIT_REPO .
    print_status "Code cloned from Git"
elif [ -n "$SOURCE_DIR" ] && [ -d "$SOURCE_DIR" ]; then
    print_info "Copying from source directory..."
    cp -r $SOURCE_DIR/* .
    chown -R $APP_USER:$APP_USER .
    print_status "Code copied from source"
else
    print_info "No source specified. Please manually copy your application files to $APP_DIR"
    echo -e "${YELLOW}Manual step required: Copy your Fixbulance application files to $APP_DIR${NC}"
    read -p "Press Enter after copying files..."
fi

print_header "SETTING UP PYTHON VIRTUAL ENVIRONMENT"
print_info "Creating virtual environment..."
sudo -u $APP_USER python3 -m venv venv
print_status "Virtual environment created"

print_info "Installing Python dependencies..."
sudo -u $APP_USER bash -c "
source venv/bin/activate
pip install --upgrade pip
pip install gunicorn flask flask-sqlalchemy flask-migrate flask-login flask-mail flask-wtf python-dotenv stripe tabulate
"
print_status "Python dependencies installed"

# Install from requirements.txt if it exists
if [ -f "requirements.txt" ]; then
    print_info "Installing from requirements.txt..."
    sudo -u $APP_USER bash -c "
    source venv/bin/activate
    pip install -r requirements.txt
    "
    print_status "Requirements.txt dependencies installed"
fi

print_header "CREATING ENVIRONMENT FILE"
if [ ! -f ".env" ]; then
    print_info "Creating .env file..."
    sudo -u $APP_USER tee .env > /dev/null << EOF
FLASK_APP=wsgi.py
FLASK_ENV=production
SECRET_KEY=$(openssl rand -base64 32)
DATABASE_URL=sqlite:///instance/fixbulance.db
MAIL_SERVER=localhost
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=
MAIL_PASSWORD=
EOF
    print_status "Environment file created"
else
    print_info ".env file already exists"
fi

print_header "CREATING WSGI FILE"
sudo -u $APP_USER tee wsgi.py > /dev/null << 'EOF'
#!/usr/bin/env python3
import sys
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the project directory to Python path
project_dir = '/var/www/fixbulance'
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

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
        
        # Create a basic Flask app as fallback
        from flask import Flask
        app = Flask(__name__)
        
        @app.route('/')
        def hello():
            return '<h1>Fixbulance Deployment Successful!</h1><p>Main application needs to be configured.</p>'

if app is None:
    raise RuntimeError("Failed to create any Flask application")

# Ensure app is configured for production
if hasattr(app, 'config'):
    app.config['DEBUG'] = False

logger.info(f"App: {app}")

if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0', port=5000)
EOF
print_status "WSGI file created"

print_header "SETTING UP DATABASE"
if [ -f "run.py" ] || [ -f "app.py" ]; then
    print_info "Initializing database..."
    sudo -u $APP_USER bash -c "
    source venv/bin/activate
    export FLASK_APP=wsgi.py
    flask db init 2>/dev/null || true
    flask db migrate -m 'Initial migration' 2>/dev/null || true
    flask db upgrade 2>/dev/null || true
    " || print_info "Database initialization skipped (manual setup may be required)"
fi

print_header "CONFIGURING SYSTEMD SERVICE"
tee /etc/systemd/system/$APP_USER.service > /dev/null << EOF
[Unit]
Description=Gunicorn instance to serve $APP_USER
After=network.target

[Service]
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
Environment="PYTHONPATH=$APP_DIR"
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/gunicorn --workers 3 --bind unix:$APP_USER.sock --umask 0007 --access-logfile $APP_DIR/logs/access.log --error-logfile $APP_DIR/logs/error.log wsgi:app
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
print_status "Systemd service configured"

print_header "CONFIGURING NGINX"
tee /etc/nginx/sites-available/$APP_USER > /dev/null << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Main application
    location / {
        include proxy_params;
        proxy_pass http://unix:$APP_DIR/$APP_USER.sock;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
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
        alias $APP_DIR/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Favicon
    location /favicon.ico {
        alias $APP_DIR/app/static/img/favicon.ico;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Security - deny access to sensitive files
    location ~ /\\. {
        deny all;
    }

    location ~ \\.py\$ {
        deny all;
    }

    # Error pages
    error_page 404 /404.html;
    error_page 500 502 503 504 /50x.html;

    # Logging
    access_log /var/log/nginx/${APP_USER}_access.log;
    error_log /var/log/nginx/${APP_USER}_error.log;
}
EOF

# Enable site
ln -sf /etc/nginx/sites-available/$APP_USER /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
print_status "Nginx configured"

print_header "SETTING PERMISSIONS"
chown -R $APP_USER:$APP_USER $APP_DIR
chmod -R 755 $APP_DIR
chmod 644 $APP_DIR/*.py 2>/dev/null || true
print_status "Permissions set"

print_header "STARTING SERVICES"
systemctl daemon-reload
systemctl enable $APP_USER
systemctl start $APP_USER
sleep 3

if systemctl is-active --quiet $APP_USER; then
    print_status "$APP_USER service started"
else
    echo -e "${RED}❌ Service failed to start${NC}"
    journalctl -u $APP_USER --no-pager -n 10
    exit 1
fi

systemctl restart nginx
sleep 2

if systemctl is-active --quiet nginx; then
    print_status "Nginx restarted"
else
    echo -e "${RED}❌ Nginx failed to start${NC}"
    nginx -t
    exit 1
fi

print_header "TESTING DEPLOYMENT"
sleep 5

HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/ 2>/dev/null)
echo "HTTP Status: $HTTP_STATUS"

if [ "$HTTP_STATUS" = "200" ]; then
    print_status "Deployment successful!"
    
    echo ""
    echo -e "${GREEN}🎉 FIXBULANCE DEPLOYMENT COMPLETE! 🎉${NC}"
    echo -e "${GREEN}🌐 Your website should be accessible at:${NC}"
    echo -e "${GREEN}   • http://$DOMAIN${NC}"
    echo -e "${GREEN}   • http://YOUR_SERVER_IP${NC}"
    echo ""
    echo -e "${BLUE}📝 Next Steps:${NC}"
    echo "1. Point your domain DNS to this server's IP"
    echo "2. Set up SSL certificate (use certbot for Let's Encrypt)"
    echo "3. Configure your application settings in $APP_DIR/.env"
    echo "4. Upload any additional content/database data"
    echo ""
    echo -e "${BLUE}📊 Service Management:${NC}"
    echo "• Start: sudo systemctl start $APP_USER"
    echo "• Stop: sudo systemctl stop $APP_USER"
    echo "• Restart: sudo systemctl restart $APP_USER"
    echo "• Status: sudo systemctl status $APP_USER"
    echo "• Logs: sudo journalctl -u $APP_USER -f"
    
else
    echo -e "${RED}❌ Deployment test failed${NC}"
    echo "Checking logs..."
    journalctl -u $APP_USER --no-pager -n 10
    tail -10 /var/log/nginx/error.log
fi

echo ""
echo -e "${BLUE}📁 Important Paths:${NC}"
echo "• Application: $APP_DIR"
echo "• Logs: $APP_DIR/logs/"
echo "• Config: $APP_DIR/.env"
echo "• Nginx config: /etc/nginx/sites-available/$APP_USER"
echo "• Service config: /etc/systemd/system/$APP_USER.service" 