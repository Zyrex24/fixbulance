#!/bin/bash

# =============================================================================
# Fix Nginx Configuration and DNS Issues
# =============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

APP_DIR="/var/www/fixbulance"
APP_USER="fixbulance"

echo -e "${BLUE}🔧 Nginx & DNS Configuration Fix Script${NC}"
echo -e "${BLUE}=====================================${NC}"

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# =============================================================================
# STEP 1: Check Current Nginx Configuration
# =============================================================================
echo -e "\n${BLUE}=== CHECKING CURRENT NGINX SETUP ===${NC}"

print_status "Checking what nginx is currently serving..."
echo "Current nginx sites-enabled:"
ls -la /etc/nginx/sites-enabled/

echo -e "\nChecking if default site is interfering..."
if [ -f "/etc/nginx/sites-enabled/default" ]; then
    print_warning "Default nginx site is enabled - this might be interfering"
else
    print_status "Default site is not enabled"
fi

echo -e "\nChecking current nginx configuration:"
sudo nginx -T | grep -A 10 -B 5 "server_name\|listen\|proxy_pass" || true

# =============================================================================
# STEP 2: Fix Nginx Configuration
# =============================================================================
echo -e "\n${BLUE}=== FIXING NGINX CONFIGURATION ===${NC}"

print_status "Disabling default nginx site..."
sudo rm -f /etc/nginx/sites-enabled/default

print_status "Creating proper nginx configuration for Fixbulance..."
sudo tee /etc/nginx/sites-available/fixbulance > /dev/null << 'EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    
    # Handle all domain variations
    server_name 
        fixbulance.com 
        www.fixbulance.com 
        fixbulance.italynorth.cloudapp.azure.com
        72.146.184.2
        localhost;
    
    # Increase timeouts for better stability
    proxy_connect_timeout       300s;
    proxy_send_timeout          300s;
    proxy_read_timeout          300s;
    send_timeout                300s;
    
    # Main application
    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/fixbulance/fixbulance.sock;
        
        # Better error handling
        proxy_intercept_errors on;
        
        # Additional headers for better compatibility
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
        
        # Handle 502 errors gracefully
        error_page 502 503 504 @fallback;
    }
    
    # Fallback for when Flask app is down
    location @fallback {
        return 200 '<!DOCTYPE html>
<html>
<head>
    <title>Fixbulance - Emergency Services</title>
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
        }
        .container {
            background: rgba(255,255,255,0.95);
            padding: 40px;
            border-radius: 15px;
            color: #333;
            max-width: 500px;
        }
        h1 { color: #e74c3c; margin-bottom: 20px; }
        .status { color: #f39c12; font-size: 18px; margin-bottom: 20px; }
        .contact { background: #ecf0f1; padding: 20px; border-radius: 10px; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚑 Fixbulance</h1>
        <div class="status">⚠️ Service Temporarily Unavailable</div>
        <p>We are working to restore service. Please try again in a few minutes.</p>
        <div class="contact">
            <strong>For urgent repairs, call:</strong><br>
            <a href="tel:+17089714053" style="font-size: 1.5em; color: #e74c3c; text-decoration: none;">
                (708) 971-4053
            </a>
        </div>
    </div>
</body>
</html>';
        add_header Content-Type text/html;
    }
    
    # Static files
    location /static {
        alias /var/www/fixbulance/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Favicon
    location /favicon.ico {
        alias /var/www/fixbulance/app/static/favicon.ico;
        expires 1y;
    }
    
    # Health check endpoint that always works
    location /nginx-health {
        return 200 '{"status":"nginx_ok","timestamp":"'$(date -Iseconds)'"}';
        add_header Content-Type application/json;
    }
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
}
EOF

print_status "Enabling the Fixbulance site..."
sudo ln -sf /etc/nginx/sites-available/fixbulance /etc/nginx/sites-enabled/

print_status "Testing nginx configuration..."
if sudo nginx -t; then
    print_status "Nginx configuration is valid"
else
    print_error "Nginx configuration has errors"
    exit 1
fi

# =============================================================================
# STEP 3: Restart Services and Test
# =============================================================================
echo -e "\n${BLUE}=== RESTARTING SERVICES ===${NC}"

print_status "Restarting nginx..."
sudo systemctl restart nginx

print_status "Checking if Flask service is running..."
if sudo systemctl is-active --quiet fixbulance; then
    print_status "Flask service is running"
else
    print_warning "Flask service not running, starting it..."
    sudo systemctl restart fixbulance
    sleep 3
fi

# =============================================================================
# STEP 4: Test All Access Methods
# =============================================================================
echo -e "\n${BLUE}=== TESTING ALL ACCESS METHODS ===${NC}"

# Get public IP
PUBLIC_IP=$(curl -4 -s icanhazip.com 2>/dev/null || echo "unknown")
echo "Your Azure VM public IP: $PUBLIC_IP"

print_status "Testing localhost access..."
LOCAL_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/ 2>/dev/null || echo "000")
echo "Localhost response: $LOCAL_CODE"

print_status "Testing IP access..."
IP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://$PUBLIC_IP/" 2>/dev/null || echo "000")
echo "IP access response: $IP_CODE"

print_status "Testing nginx health endpoint..."
HEALTH_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/nginx-health 2>/dev/null || echo "000")
echo "Nginx health response: $HEALTH_CODE"

if [ "$HEALTH_CODE" = "200" ]; then
    print_status "✅ Nginx is working correctly"
else
    print_warning "Nginx health check failed"
fi

# =============================================================================
# STEP 5: DNS and Domain Configuration Check
# =============================================================================
echo -e "\n${BLUE}=== CHECKING DNS CONFIGURATION ===${NC}"

print_status "Checking domain DNS records..."
echo "fixbulance.com A record:"
nslookup fixbulance.com | grep -A 2 "Non-authoritative answer:" || echo "DNS lookup failed"

echo -e "\nwww.fixbulance.com A record:"
nslookup www.fixbulance.com | grep -A 2 "Non-authoritative answer:" || echo "DNS lookup failed"

print_status "Checking Azure domain..."
echo "fixbulance.italynorth.cloudapp.azure.com:"
nslookup fixbulance.italynorth.cloudapp.azure.com | grep -A 2 "Non-authoritative answer:" || echo "DNS lookup failed"

# =============================================================================
# STEP 6: Final Status and Instructions
# =============================================================================
echo -e "\n${BLUE}=== FINAL STATUS REPORT ===${NC}"

echo -e "Services:"
echo -e "  Nginx: $(sudo systemctl is-active nginx)"
echo -e "  Fixbulance: $(sudo systemctl is-active fixbulance)"

echo -e "\nSocket file:"
if [ -S "/var/www/fixbulance/fixbulance.sock" ]; then
    echo -e "  ✅ EXISTS"
    ls -la "/var/www/fixbulance/fixbulance.sock"
else
    echo -e "  ❌ MISSING"
fi

echo -e "\n${GREEN}🌐 Your website should now be accessible at:${NC}"
echo -e "   • http://$PUBLIC_IP (direct IP)"
echo -e "   • http://fixbulance.italynorth.cloudapp.azure.com (Azure domain)"
echo -e "   • http://$PUBLIC_IP/nginx-health (nginx health check)"

echo -e "\n${YELLOW}DNS Issues (if fixbulance.com doesn't work):${NC}"
echo -e "   • Your domain fixbulance.com needs to point to IP: $PUBLIC_IP"
echo -e "   • Contact your domain registrar to update A records"
echo -e "   • A record: fixbulance.com → $PUBLIC_IP"
echo -e "   • A record: www.fixbulance.com → $PUBLIC_IP"

echo -e "\n${BLUE}Troubleshooting commands:${NC}"
echo -e "   • Check nginx: sudo systemctl status nginx"
echo -e "   • Check Flask: sudo systemctl status fixbulance"
echo -e "   • View logs: sudo journalctl -u fixbulance -f"
echo -e "   • Test local: curl -I http://localhost/"
echo -e "   • Test nginx health: curl http://localhost/nginx-health"

echo -e "\n${GREEN}🔧 Configuration fix completed!${NC}" 