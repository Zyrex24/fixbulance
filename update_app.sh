#!/bin/bash

# =============================================================================
# FIXBULANCE APPLICATION UPDATE SCRIPT
# =============================================================================
# Quick update script for production application
# Run this after making changes and pushing to GitHub
# =============================================================================

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Configuration
APP_DIR="/var/www/fixbulance"
APP_USER="fixbulance"

log "Starting Fixbulance application update..."

# Switch to application directory
cd $APP_DIR

# Pull latest changes from GitHub
log "Pulling latest changes from GitHub..."
sudo -u $APP_USER git pull origin main

# Activate virtual environment and update dependencies
log "Updating Python dependencies..."
sudo -u $APP_USER bash << EOF
source venv/bin/activate
pip install -r requirements.txt
EOF

# Run any new database migrations if needed
log "Running database migrations..."
sudo -u $APP_USER bash << EOF
cd $APP_DIR
source venv/bin/activate

# Check if new migration files exist and run them
if [ -f "new_migration.py" ]; then
    log "Running new migration..."
    python new_migration.py
fi
EOF

# Restart application services
log "Restarting Fixbulance application..."
sudo systemctl restart fixbulance

# Wait a moment for service to start
sleep 3

# Check service status
if sudo systemctl is-active --quiet fixbulance; then
    log "Fixbulance service restarted successfully"
else
    echo "ERROR: Failed to restart Fixbulance service"
    sudo systemctl status fixbulance
    exit 1
fi

# Restart Nginx (in case of static file changes)
log "Restarting Nginx..."
sudo systemctl restart nginx

if sudo systemctl is-active --quiet nginx; then
    log "Nginx restarted successfully"
else
    echo "ERROR: Failed to restart Nginx"
    sudo systemctl status nginx
    exit 1
fi

# Verify application is responding
log "Verifying application..."
sleep 2

if curl -f http://localhost:8000 > /dev/null 2>&1; then
    log "Application is responding correctly"
else
    echo "WARNING: Application may not be responding"
fi

log "Application update completed successfully!"
info "Application is now running the latest version"

# Show recent logs
info "Recent application logs:"
sudo journalctl -u fixbulance -n 10 --no-pager 