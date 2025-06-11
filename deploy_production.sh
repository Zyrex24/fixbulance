#!/bin/bash

# =============================================================================
# FIXBULANCE PRODUCTION DEPLOYMENT SCRIPT
# =============================================================================
# Complete deployment script for Digital Ocean Droplet
# Incorporates all fixes and debugging from development process
# 
# Business: Fixbulance LLC - Mobile Phone Repair Service
# Owner: Ahmed Khalil - (708) 971-4053
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="fixbulance.com"  # Change to your domain
APP_USER="fixbulance"
APP_DIR="/var/www/fixbulance"
REPO_URL="https://github.com/Zyrex24/fixbulance.git"  # Change to your repo
PYTHON_VERSION="3.10"

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# =============================================================================
# SYSTEM PREPARATION
# =============================================================================

log "Starting Fixbulance production deployment..."

# Update system
log "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install essential packages
log "Installing essential packages..."
sudo apt install -y \
    curl \
    wget \
    git \
    build-essential \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    ufw \
    fail2ban \
    htop \
    nano \
    unzip

# =============================================================================
# PYTHON SETUP
# =============================================================================

log "Setting up Python ${PYTHON_VERSION}..."

# Install Python and pip (Ubuntu 22.04 comes with Python 3.10)
sudo apt install -y python3 python3-dev python3-venv python3-pip

# Create symlinks for python (if needed)
sudo ln -sf /usr/bin/python3 /usr/bin/python

# Upgrade pip
python3 -m pip install --upgrade pip

# =============================================================================
# NGINX SETUP
# =============================================================================

log "Installing and configuring Nginx..."

sudo apt install -y nginx

# Remove default Nginx site
sudo rm -f /etc/nginx/sites-enabled/default

# Create Nginx configuration for Fixbulance
sudo tee /etc/nginx/sites-available/fixbulance << EOF
server {
    listen 80;
    server_name ${DOMAIN} www.${DOMAIN};
    
    # Redirect HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name ${DOMAIN} www.${DOMAIN};
    
    # SSL Configuration (certificates will be added by Certbot)
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied expired no-cache no-store private must-revalidate auth;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss;
    
    # Main application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Static files
    location /static {
        alias ${APP_DIR}/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Media files
    location /media {
        alias ${APP_DIR}/media;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Favicon
    location /favicon.ico {
        alias ${APP_DIR}/app/static/images/favicon.ico;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Block access to sensitive files
    location ~ /\. {
        deny all;
    }
    
    location ~ /\_(.*) {
        deny all;
    }
}
EOF

# Enable the site
sudo ln -sf /etc/nginx/sites-available/fixbulance /etc/nginx/sites-enabled/

# Test Nginx configuration
sudo nginx -t || error "Nginx configuration test failed"

# =============================================================================
# APPLICATION USER SETUP
# =============================================================================

log "Setting up application user..."

# Create application user
sudo useradd -m -s /bin/bash ${APP_USER} || true
sudo usermod -aG sudo ${APP_USER} || true

# Create application directory
sudo mkdir -p ${APP_DIR}
sudo chown ${APP_USER}:${APP_USER} ${APP_DIR}

# =============================================================================
# APPLICATION DEPLOYMENT
# =============================================================================

log "Deploying Fixbulance application..."

# Switch to app user and directory
sudo -u ${APP_USER} bash << EOF
cd ${APP_DIR}

# Clone repository
if [ -d ".git" ]; then
    log "Updating existing repository..."
    git pull origin main
else
    log "Cloning repository..."
    git clone ${REPO_URL} .
fi

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip in virtual environment
pip install --upgrade pip

# Install Python dependencies
pip install -r requirements.txt

# Install additional production dependencies
pip install gunicorn supervisor

# Create instance directory for SQLite database
mkdir -p instance
mkdir -p logs
mkdir -p media

# Set proper permissions
chmod 755 instance logs media
EOF

# =============================================================================
# DATABASE INITIALIZATION
# =============================================================================

log "Initializing database..."

sudo -u ${APP_USER} bash << EOF
cd ${APP_DIR}
source venv/bin/activate

# Run database migrations in correct order
log "Running database migrations..."
python create_system_settings_table.py
python create_waiver_table.py
python device_pricing_migration.py
python multi_service_migration.py
python stripe_migration.py
python tax_implementation_migration.py

# Create initial admin user
log "Creating initial admin user..."
python production_init.py
EOF

# =============================================================================
# ENVIRONMENT CONFIGURATION
# =============================================================================

log "Setting up environment configuration..."

# Create production environment file
sudo -u ${APP_USER} tee ${APP_DIR}/.env << EOF
# Flask Configuration
FLASK_APP=run.py
FLASK_ENV=production
SECRET_KEY=$(openssl rand -base64 32)

# Database Configuration
DATABASE_URL=sqlite:///instance/repair_service.db

# Email Configuration (Namecheap Private Email)
MAIL_SERVER=mail.privateemail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=info@fixbulance.com
MAIL_PASSWORD=YOUR_EMAIL_PASSWORD_HERE

# Stripe Configuration
STRIPE_PUBLISHABLE_KEY=pk_live_YOUR_STRIPE_PUBLISHABLE_KEY
STRIPE_SECRET_KEY=sk_live_YOUR_STRIPE_SECRET_KEY
STRIPE_WEBHOOK_SECRET=whsec_YOUR_WEBHOOK_SECRET

# Security
WTF_CSRF_ENABLED=True
WTF_CSRF_TIME_LIMIT=None

# Production Settings
SERVER_NAME=${DOMAIN}
PREFERRED_URL_SCHEME=https
EOF

# Set proper permissions for environment file
sudo chown ${APP_USER}:${APP_USER} ${APP_DIR}/.env
sudo chmod 600 ${APP_DIR}/.env

# =============================================================================
# GUNICORN SETUP
# =============================================================================

log "Setting up Gunicorn..."

# Create Gunicorn configuration
sudo -u ${APP_USER} tee ${APP_DIR}/gunicorn_config.py << EOF
import multiprocessing

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "${APP_DIR}/logs/access.log"
errorlog = "${APP_DIR}/logs/error.log"
loglevel = "info"
access_log_format = '%h %l %u %t "%r" %s %b "%{Referer}i" "%{User-Agent}i"'

# Process naming
proc_name = "fixbulance"

# Server mechanics
preload_app = True
daemon = False
pidfile = "${APP_DIR}/gunicorn.pid"
user = "${APP_USER}"
group = "${APP_USER}"
tmp_upload_dir = None

# SSL (if serving directly via Gunicorn)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"
EOF

# =============================================================================
# SYSTEMD SERVICE SETUP
# =============================================================================

log "Setting up systemd service..."

# Create systemd service file
sudo tee /etc/systemd/system/fixbulance.service << EOF
[Unit]
Description=Fixbulance Flask Application
After=network.target

[Service]
Type=notify
User=${APP_USER}
Group=${APP_USER}
WorkingDirectory=${APP_DIR}
Environment=PATH=${APP_DIR}/venv/bin
EnvironmentFile=${APP_DIR}/.env
ExecStart=${APP_DIR}/venv/bin/gunicorn --config gunicorn_config.py run:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=10
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable fixbulance

# =============================================================================
# SSL CERTIFICATE SETUP (Let's Encrypt)
# =============================================================================

log "Setting up SSL certificates..."

# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Start Nginx
sudo systemctl start nginx
sudo systemctl enable nginx

info "SSL certificate setup requires manual intervention."
info "After deployment, run: sudo certbot --nginx -d ${DOMAIN} -d www.${DOMAIN}"

# =============================================================================
# FIREWALL SETUP
# =============================================================================

log "Configuring firewall..."

# Configure UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

# =============================================================================
# FAIL2BAN SETUP
# =============================================================================

log "Setting up Fail2Ban..."

# Configure Fail2Ban for additional security
sudo tee /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[nginx-http-auth]
enabled = true

[nginx-limit-req]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log

[ssh]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
EOF

sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# =============================================================================
# LOG ROTATION SETUP
# =============================================================================

log "Setting up log rotation..."

sudo tee /etc/logrotate.d/fixbulance << EOF
${APP_DIR}/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 ${APP_USER} ${APP_USER}
    postrotate
        systemctl reload fixbulance
    endscript
}
EOF

# =============================================================================
# BACKUP SCRIPT SETUP
# =============================================================================

log "Setting up backup script..."

sudo -u ${APP_USER} tee ${APP_DIR}/backup.sh << EOF
#!/bin/bash

# Fixbulance Backup Script
BACKUP_DIR="${APP_DIR}/backups"
DATE=\$(date +%Y%m%d_%H%M%S)

mkdir -p \$BACKUP_DIR

# Backup database
cp ${APP_DIR}/instance/repair_service.db \$BACKUP_DIR/repair_service_\$DATE.db

# Backup media files
tar -czf \$BACKUP_DIR/media_\$DATE.tar.gz ${APP_DIR}/media/

# Backup environment file
cp ${APP_DIR}/.env \$BACKUP_DIR/env_\$DATE.backup

# Remove backups older than 30 days
find \$BACKUP_DIR -type f -mtime +30 -delete

echo "Backup completed: \$DATE"
EOF

sudo chmod +x ${APP_DIR}/backup.sh

# Add backup to crontab
(sudo -u ${APP_USER} crontab -l 2>/dev/null; echo "0 2 * * * ${APP_DIR}/backup.sh") | sudo -u ${APP_USER} crontab -

# =============================================================================
# FINAL SETUP AND DEPLOYMENT
# =============================================================================

log "Starting services..."

# Start Fixbulance application
sudo systemctl start fixbulance

# Check service status
sleep 5
if sudo systemctl is-active --quiet fixbulance; then
    log "Fixbulance service started successfully"
else
    error "Failed to start Fixbulance service"
fi

# Restart Nginx
sudo systemctl restart nginx

# Check Nginx status
if sudo systemctl is-active --quiet nginx; then
    log "Nginx restarted successfully"
else
    error "Failed to restart Nginx"
fi

# =============================================================================
# DEPLOYMENT VERIFICATION
# =============================================================================

log "Verifying deployment..."

# Check if application is responding
sleep 5
if curl -f http://localhost:8000 > /dev/null 2>&1; then
    log "Application is responding on port 8000"
else
    warning "Application may not be responding on port 8000"
fi

# Display service status
sudo systemctl status fixbulance --no-pager
sudo systemctl status nginx --no-pager

# =============================================================================
# POST-DEPLOYMENT INSTRUCTIONS
# =============================================================================

log "Deployment completed successfully!"
echo ""
info "=== POST-DEPLOYMENT STEPS ==="
info "1. Update DNS records to point to this server"
info "2. Set up SSL certificate: sudo certbot --nginx -d ${DOMAIN} -d www.${DOMAIN}"
info "3. Update .env file with production credentials:"
info "   - MAIL_PASSWORD (Namecheap email)"
info "   - STRIPE_PUBLISHABLE_KEY and STRIPE_SECRET_KEY"
info "   - STRIPE_WEBHOOK_SECRET"
info "4. Test the application: https://${DOMAIN}"
info "5. Access admin panel: https://${DOMAIN}/admin"
info "6. Default admin login: admin@fixbulance.com / admin123"
echo ""
info "=== USEFUL COMMANDS ==="
info "- View logs: sudo journalctl -u fixbulance -f"
info "- Restart app: sudo systemctl restart fixbulance"
info "- Update app: cd ${APP_DIR} && git pull && sudo systemctl restart fixbulance"
info "- Check status: sudo systemctl status fixbulance"
echo ""
info "=== CONTACT INFORMATION ==="
info "Business Owner: Ahmed Khalil - (708) 971-4053"
info "Support Email: support@fixbulance.com"
echo ""
log "Fixbulance deployment complete!" 