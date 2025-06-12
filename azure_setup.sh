#!/bin/bash

# =============================================================================
# Fixbulance Azure Production Server Setup Script
# Run this script on a fresh Ubuntu 22.04 Azure Virtual Machine with Desktop
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration - UPDATE THESE VALUES
GITHUB_REPO="https://github.com/Zyrex24/fixbulance.git"
DOMAIN_NAME="fixbulance.com"
APP_USER="fixbulance"
APP_DIR="/var/www/fixbulance"
DB_NAME="fixbulance_db"
DB_USER="fixbulance_user"
DB_PASSWORD="$(openssl rand -base64 32)"

echo -e "${BLUE}🚀 Fixbulance Azure Production Server Setup${NC}"
echo -e "${BLUE}=========================================${NC}"

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

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (use sudo)"
   exit 1
fi

print_status "Starting Azure server setup..."

# =============================================================================
# STEP 1: System Updates and Essential Packages
# =============================================================================
print_status "Updating system packages..."
apt update && apt upgrade -y

print_status "Installing essential packages..."
apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    nginx \
    git \
    curl \
    supervisor \
    postgresql \
    postgresql-contrib \
    certbot \
    python3-certbot-nginx \
    htop \
    ufw \
    fail2ban \
    zenity \
    snapd

# Install Azure CLI for easier Azure management
print_status "Installing Azure CLI..."
curl -sL https://aka.ms/InstallAzureCLIDeb | bash

# =============================================================================
# STEP 2: Create Application User
# =============================================================================
print_status "Creating application user..."
if ! id "$APP_USER" &>/dev/null; then
    adduser --system --group --home $APP_DIR $APP_USER
fi

mkdir -p $APP_DIR
chown $APP_USER:$APP_USER $APP_DIR

# =============================================================================
# STEP 3: Setup PostgreSQL Database
# =============================================================================
print_status "Setting up PostgreSQL database..."
sudo -u postgres psql <<EOF
CREATE DATABASE $DB_NAME;
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
ALTER USER $DB_USER CREATEDB;
\q
EOF

# =============================================================================
# STEP 4: Clone Application and Setup Environment
# =============================================================================
print_status "Cloning application repository..."
sudo -u $APP_USER git clone $GITHUB_REPO $APP_DIR
cd $APP_DIR

print_status "Setting up Python virtual environment..."
sudo -u $APP_USER python3 -m venv venv
sudo -u $APP_USER $APP_DIR/venv/bin/pip install --upgrade pip

print_status "Installing Python dependencies..."
sudo -u $APP_USER $APP_DIR/venv/bin/pip install -r requirements.txt

# =============================================================================
# STEP 5: Create Environment Configuration
# =============================================================================
print_status "Creating environment configuration..."
cat > $APP_DIR/.env <<EOF
FLASK_ENV=production
SECRET_KEY=$(openssl rand -base64 32)
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost/$DB_NAME
MAIL_SERVER=mail.privateemail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=info@fixbulance.com
MAIL_PASSWORD=#AsAs1234
STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key_here
STRIPE_SECRET_KEY=your_stripe_secret_key_here
COMPANY_NAME=Fixbulance
COMPANY_PHONE=+1-708-971-4053
COMPANY_EMAIL=info@fixbulance.com
COMPANY_ADDRESS=Orland Park, IL 60462
EOF

chown $APP_USER:$APP_USER $APP_DIR/.env
chmod 600 $APP_DIR/.env

# =============================================================================
# STEP 6: Initialize Database
# =============================================================================
print_status "Initializing application database..."
cd $APP_DIR
sudo -u $APP_USER $APP_DIR/venv/bin/python production_init.py

# =============================================================================
# STEP 7: Create Systemd Service
# =============================================================================
print_status "Creating systemd service..."
cat > /etc/systemd/system/fixbulance.service <<EOF
[Unit]
Description=Fixbulance Flask App on Azure
After=network.target

[Service]
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/gunicorn --workers 3 --bind unix:fixbulance.sock -m 007 run:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# =============================================================================
# STEP 8: Configure Nginx
# =============================================================================
print_status "Configuring Nginx..."
cat > /etc/nginx/sites-available/fixbulance <<EOF
server {
    listen 80;
    server_name $DOMAIN_NAME www.$DOMAIN_NAME;

    location / {
        include proxy_params;
        proxy_pass http://unix:$APP_DIR/fixbulance.sock;
    }

    location /static {
        alias $APP_DIR/app/static;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
}
EOF

# Enable site and remove default
ln -sf /etc/nginx/sites-available/fixbulance /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
nginx -t

# =============================================================================
# STEP 9: Create Deployment Script
# =============================================================================
print_status "Creating deployment script..."
cat > $APP_DIR/deploy.sh <<EOF
#!/bin/bash
set -e

echo "🚀 Starting Azure deployment..."

# Navigate to app directory
cd $APP_DIR

# Pull latest changes
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
pip install -r requirements.txt

# Run database migrations
python production_init.py

# Restart the application
sudo systemctl restart fixbulance

echo "✅ Azure deployment completed successfully!"
EOF

chmod +x $APP_DIR/deploy.sh
chown $APP_USER:$APP_USER $APP_DIR/deploy.sh

# =============================================================================
# STEP 10: Setup Azure-specific Firewall
# =============================================================================
print_status "Configuring Azure firewall..."
ufw --force enable
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 'Nginx Full'
ufw allow 3389  # RDP for GUI access

# =============================================================================
# STEP 11: Start Services
# =============================================================================
print_status "Starting services..."
systemctl daemon-reload
systemctl start fixbulance
systemctl enable fixbulance
systemctl restart nginx
systemctl enable nginx

# =============================================================================
# STEP 12: Setup SSL Certificate
# =============================================================================
print_status "Setting up SSL certificate..."
print_warning "Make sure your domain $DOMAIN_NAME points to this Azure VM's public IP address"
read -p "Press Enter when your domain is pointing to this VM's public IP..."

# Get SSL certificate
certbot --nginx -d $DOMAIN_NAME -d www.$DOMAIN_NAME --non-interactive --agree-tos --email admin@$DOMAIN_NAME

# Test automatic renewal
certbot renew --dry-run

# =============================================================================
# STEP 13: Create GUI Management Tools
# =============================================================================
print_status "Setting up GUI management tools..."

# Install pgAdmin4 repository and tools
print_status "Adding pgAdmin4 repository..."
curl -fsS https://www.pgadmin.org/static/packages_pgadmin_org.pub | gpg --dearmor -o /usr/share/keyrings/packages-pgadmin-org.gpg
echo "deb [signed-by=/usr/share/keyrings/packages-pgadmin-org.gpg] https://ftp.postgresql.org/pub/pgadmin/pgadmin4/apt/jammy pgadmin4 main" > /etc/apt/sources.list.d/pgadmin4.list

print_status "Updating package list and installing pgAdmin4..."
apt update
apt install -y pgadmin4-desktop

# Create desktop shortcut for Fixbulance management
DESKTOP_FILE="/home/azureuser/Desktop/fixbulance-manager.sh"
cat > $DESKTOP_FILE <<EOF
#!/bin/bash
CHOICE=\$(zenity --list --title="Fixbulance Manager" --text="Choose an action:" \\
    --column="Action" \\
    "Start Application" \\
    "Stop Application" \\
    "Restart Application" \\
    "View Logs" \\
    "Deploy Updates" \\
    "Open Website" \\
    "Open Admin Panel" \\
    "Database Manager")

case \$CHOICE in
    "Start Application")
        sudo systemctl start fixbulance
        zenity --info --text="Application started!"
        ;;
    "Stop Application")
        sudo systemctl stop fixbulance
        zenity --info --text="Application stopped!"
        ;;
    "Restart Application")
        sudo systemctl restart fixbulance
        zenity --info --text="Application restarted!"
        ;;
    "View Logs")
        gnome-terminal -- journalctl -u fixbulance -f
        ;;
    "Deploy Updates")
        gnome-terminal -- $APP_DIR/deploy.sh
        ;;
    "Open Website")
        firefox https://$DOMAIN_NAME
        ;;
    "Open Admin Panel")
        firefox https://$DOMAIN_NAME/admin
        ;;
    "Database Manager")
        pgadmin4
        ;;
esac
EOF

chmod +x $DESKTOP_FILE
chown azureuser:azureuser $DESKTOP_FILE

# =============================================================================
# STEP 14: Final Setup
# =============================================================================
print_status "Setting up log rotation..."
cat > /etc/logrotate.d/fixbulance <<EOF
$APP_DIR/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    copytruncate
}
EOF

# Create logs directory
mkdir -p $APP_DIR/logs
chown $APP_USER:$APP_USER $APP_DIR/logs

# =============================================================================
# AZURE-SPECIFIC OPTIMIZATIONS
# =============================================================================
print_status "Applying Azure-specific optimizations..."

# Install Azure VM agent extensions
apt install -y walinuxagent

# Enable Azure monitoring
systemctl enable walinuxagent

# =============================================================================
# COMPLETION
# =============================================================================
echo
echo -e "${GREEN}🎉 SUCCESS! Your Fixbulance Azure server is ready!${NC}"
echo
echo -e "${BLUE}Server Information:${NC}"
echo -e "Domain: https://$DOMAIN_NAME"
echo -e "Azure VM: $(hostname)"
echo -e "Application Directory: $APP_DIR"
echo -e "Database: $DB_NAME"
echo -e "Database User: $DB_USER"
echo -e "Database Password: $DB_PASSWORD"
echo
echo -e "${BLUE}GUI Access:${NC}"
echo -e "RDP Address: $(curl -s ifconfig.me):3389"
echo -e "Username: azureuser"
echo -e "Desktop Manager: fixbulance-manager.sh (on desktop)"
echo
echo -e "${BLUE}Important Files:${NC}"
echo -e "Environment Config: $APP_DIR/.env"
echo -e "Deployment Script: $APP_DIR/deploy.sh"
echo -e "Nginx Config: /etc/nginx/sites-available/fixbulance"
echo -e "Service Config: /etc/systemd/system/fixbulance.service"
echo
echo -e "${YELLOW}Next Steps:${NC}"
echo -e "1. Connect via RDP to your Azure VM"
echo -e "2. Double-click fixbulance-manager.sh on desktop"
echo -e "3. Test your website: https://$DOMAIN_NAME"
echo -e "4. For future deployments: Use GUI manager or run $APP_DIR/deploy.sh"
echo
echo -e "${BLUE}Azure-Specific Commands:${NC}"
echo -e "Azure CLI: az vm list"
echo -e "VM Status: az vm get-instance-view --name fixbulance-vm --resource-group fixbulance-resources"
echo -e "Scale VM: az vm resize --resource-group fixbulance-resources --name fixbulance-vm --size Standard_B4ms"
echo
echo -e "${GREEN}Your Fixbulance app is now live on Azure with full GUI! 🚀${NC}" 