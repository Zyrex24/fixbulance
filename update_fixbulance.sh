#!/bin/bash

echo "🔄 Fixbulance Update & Deployment Script"
echo "======================================="
echo "This script handles updates and changes to your Fixbulance website"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_USER="fixbulance"
APP_DIR="/var/www/fixbulance"
BACKUP_DIR="$APP_DIR/backups"
GIT_REPO=""  # Set if using git
UPDATE_SOURCE=""  # Set if copying from local directory

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

print_warning() {
    echo -e "${RED}⚠️  $1${NC}"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Please run this script as root (use sudo)${NC}"
    exit 1
fi

# Check if application directory exists
if [ ! -d "$APP_DIR" ]; then
    echo -e "${RED}❌ Application directory $APP_DIR not found${NC}"
    echo "Please run the initial deployment script first"
    exit 1
fi

print_header "PRE-UPDATE CHECKS"
print_info "Checking current system status..."

# Check if services are running
if systemctl is-active --quiet $APP_USER; then
    echo "✅ $APP_USER service is running"
else
    echo "⚠️  $APP_USER service is not running"
fi

if systemctl is-active --quiet nginx; then
    echo "✅ Nginx service is running"
else
    echo "⚠️  Nginx service is not running"
fi

# Show current version if git is being used
cd $APP_DIR
if [ -d ".git" ]; then
    CURRENT_COMMIT=$(sudo -u $APP_USER git rev-parse --short HEAD 2>/dev/null)
    if [ -n "$CURRENT_COMMIT" ]; then
        echo "📍 Current version: $CURRENT_COMMIT"
    fi
fi

print_header "CREATING BACKUP"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="backup_$TIMESTAMP"
print_info "Creating backup: $BACKUP_NAME"

mkdir -p $BACKUP_DIR
cd $APP_DIR

# Create application backup
sudo -u $APP_USER tar -czf "$BACKUP_DIR/$BACKUP_NAME.tar.gz" \
    --exclude="venv" \
    --exclude="__pycache__" \
    --exclude="*.pyc" \
    --exclude=".git" \
    --exclude="logs" \
    --exclude="backups" \
    .
print_status "Application backup created"

# Backup database if it exists
if [ -f "instance/fixbulance.db" ]; then
    cp instance/fixbulance.db "$BACKUP_DIR/database_$TIMESTAMP.db"
    print_status "Database backup created"
fi

# Keep only last 10 backups
cd $BACKUP_DIR
ls -t backup_*.tar.gz 2>/dev/null | tail -n +11 | xargs rm -f 2>/dev/null
ls -t database_*.db 2>/dev/null | tail -n +11 | xargs rm -f 2>/dev/null
print_info "Cleaned old backups (keeping last 10)"

print_header "STOPPING SERVICES"
systemctl stop $APP_USER
print_status "Stopped $APP_USER service"

print_header "UPDATING APPLICATION CODE"
cd $APP_DIR

if [ -n "$GIT_REPO" ] && [ -d ".git" ]; then
    print_info "Pulling latest changes from Git..."
    sudo -u $APP_USER git fetch
    sudo -u $APP_USER git pull origin main
    print_status "Code updated from Git"
    
    NEW_COMMIT=$(sudo -u $APP_USER git rev-parse --short HEAD 2>/dev/null)
    if [ -n "$NEW_COMMIT" ] && [ "$NEW_COMMIT" != "$CURRENT_COMMIT" ]; then
        echo "📍 Updated to version: $NEW_COMMIT"
        sudo -u $APP_USER git log --oneline -5
    else
        echo "📍 No new changes"
    fi

elif [ -n "$UPDATE_SOURCE" ] && [ -d "$UPDATE_SOURCE" ]; then
    print_info "Copying files from update source..."
    
    # Create temporary directory for new files
    TEMP_DIR="/tmp/fixbulance_update_$TIMESTAMP"
    cp -r "$UPDATE_SOURCE" "$TEMP_DIR"
    
    # Preserve important files
    if [ -f ".env" ]; then
        cp .env "$TEMP_DIR/.env"
    fi
    if [ -d "instance" ]; then
        cp -r instance "$TEMP_DIR/"
    fi
    if [ -d "logs" ]; then
        cp -r logs "$TEMP_DIR/"
    fi
    
    # Replace application files
    rsync -av --exclude=venv --exclude=backups "$TEMP_DIR/" ./
    rm -rf "$TEMP_DIR"
    
    chown -R $APP_USER:$APP_USER .
    print_status "Files updated from source"

else
    print_info "No update source specified. Manual file updates required."
    echo -e "${YELLOW}Please update your files manually, then press Enter to continue...${NC}"
    read -p ""
fi

print_header "UPDATING DEPENDENCIES"
if [ -f "requirements.txt" ]; then
    print_info "Updating Python dependencies..."
    sudo -u $APP_USER bash -c "
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    "
    print_status "Dependencies updated"
fi

print_header "DATABASE MIGRATIONS"
if [ -f "run.py" ] || [ -f "app.py" ]; then
    print_info "Running database migrations..."
    sudo -u $APP_USER bash -c "
    source venv/bin/activate
    export FLASK_APP=wsgi.py
    flask db migrate -m 'Update migration $TIMESTAMP' 2>/dev/null || true
    flask db upgrade 2>/dev/null || true
    " || print_info "No migrations needed or migration failed"
fi

print_header "UPDATING CONFIGURATION"
# Check if new environment variables are needed
if [ -f ".env.example" ] && [ -f ".env" ]; then
    print_info "Checking for new environment variables..."
    while IFS= read -r line; do
        if [[ $line == *"="* ]] && ! grep -q "^${line%%=*}=" .env; then
            echo "New environment variable found: ${line%%=*}"
            echo "$line" >> .env
        fi
    done < .env.example
fi

print_header "COLLECTING STATIC FILES"
if [ -d "app/static" ]; then
    print_info "Setting static file permissions..."
    chown -R $APP_USER:$APP_USER app/static
    find app/static -type f -exec chmod 644 {} \;
    find app/static -type d -exec chmod 755 {} \;
    print_status "Static files updated"
fi

print_header "RESTARTING SERVICES"
# Reload systemd in case service file changed
systemctl daemon-reload

# Start the application service
systemctl start $APP_USER
sleep 5

if systemctl is-active --quiet $APP_USER; then
    print_status "$APP_USER service started"
else
    print_warning "Service failed to start - checking logs..."
    journalctl -u $APP_USER --no-pager -n 10
    
    print_info "Attempting to restore from backup..."
    systemctl stop $APP_USER
    
    cd $APP_DIR
    sudo -u $APP_USER tar -xzf "$BACKUP_DIR/$BACKUP_NAME.tar.gz"
    
    systemctl start $APP_USER
    sleep 3
    
    if systemctl is-active --quiet $APP_USER; then
        print_status "Service restored from backup"
    else
        echo -e "${RED}❌ Failed to restore service${NC}"
        exit 1
    fi
fi

# Restart nginx to ensure it picks up any changes
systemctl reload nginx
print_status "Nginx reloaded"

print_header "TESTING UPDATE"
sleep 3

HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/ 2>/dev/null)
echo "HTTP Status: $HTTP_STATUS"

if [ "$HTTP_STATUS" = "200" ]; then
    print_status "Update successful!"
    
    echo ""
    echo -e "${GREEN}🎉 FIXBULANCE UPDATE COMPLETE! 🎉${NC}"
    echo ""
    echo -e "${BLUE}📊 Update Summary:${NC}"
    if [ -n "$CURRENT_COMMIT" ] && [ -n "$NEW_COMMIT" ]; then
        echo "• Version: $CURRENT_COMMIT → $NEW_COMMIT"
    fi
    echo "• Backup created: $BACKUP_NAME"
    echo "• Services: ✅ Running"
    echo "• Website: ✅ Accessible"
    
else
    echo -e "${RED}❌ Update test failed - Rolling back...${NC}"
    
    systemctl stop $APP_USER
    
    cd $APP_DIR
    sudo -u $APP_USER tar -xzf "$BACKUP_DIR/$BACKUP_NAME.tar.gz"
    
    if [ -f "$BACKUP_DIR/database_$TIMESTAMP.db" ]; then
        cp "$BACKUP_DIR/database_$TIMESTAMP.db" instance/fixbulance.db
        chown $APP_USER:$APP_USER instance/fixbulance.db
    fi
    
    systemctl start $APP_USER
    systemctl reload nginx
    
    sleep 3
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/ 2>/dev/null)
    
    if [ "$HTTP_STATUS" = "200" ]; then
        echo -e "${GREEN}✅ Rollback successful${NC}"
    else
        echo -e "${RED}❌ Rollback failed - manual intervention required${NC}"
    fi
fi

print_header "POST-UPDATE TASKS"
echo -e "${BLUE}📝 Recommended post-update tasks:${NC}"
echo "1. Clear any application caches"
echo "2. Test critical functionality"
echo "3. Monitor logs for any issues"
echo "4. Update DNS records if domain changed"
echo ""
echo -e "${BLUE}📊 Monitoring Commands:${NC}"
echo "• Service status: sudo systemctl status $APP_USER"
echo "• Application logs: sudo journalctl -u $APP_USER -f"
echo "• Nginx logs: sudo tail -f /var/log/nginx/error.log"
echo "• Access logs: sudo tail -f $APP_DIR/logs/access.log"
echo ""
echo -e "${BLUE}🔄 Rollback Command (if needed):${NC}"
echo "sudo tar -xzf $BACKUP_DIR/$BACKUP_NAME.tar.gz -C $APP_DIR && sudo systemctl restart $APP_USER" 