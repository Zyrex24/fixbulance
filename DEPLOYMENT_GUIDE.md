# 🚀 Automated Deployment Guide: GitHub + Digital Ocean Droplet

## Overview
This guide provides a **production-ready deployment solution** using Digital Ocean Droplets with automated GitHub deployments. You get full server control while maintaining automated deployments.

## 📋 Prerequisites
- GitHub account
- Digital Ocean account
- Domain name (fixbulance.com)
- Stripe account keys
- Email credentials (booking@fixbulance.com / #AsAs1234)
- Basic Linux knowledge (helpful but not required)

---

## 🔧 Step 1: GitHub Repository Setup

### 1.1 Create GitHub Repository
```bash
# Create new repository on GitHub named 'fixbulance-app'
# Or use existing repository
```

### 1.2 Push Your Code
```bash
git init
git add .
git commit -m "Initial commit - Fixbulance app with automated deployment"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/fixbulance-app.git
git push -u origin main
```

---

## 🌊 Step 2: Digital Ocean Droplet Setup

### 2.1 Create Droplet
1. Go to [Digital Ocean Droplets](https://cloud.digitalocean.com/droplets)
2. Click **"Create Droplet"**
3. Choose **Ubuntu 22.04 LTS**
4. Select **Basic plan** - $6/month (1GB RAM, 1 vCPU, 25GB SSD)
5. Choose datacenter region closest to your users
6. Add SSH key or use password authentication
7. Name: `fixbulance-production`

### 2.2 Create Managed Database (Optional but Recommended)
1. Go to **Databases** in Digital Ocean
2. Click **"Create Database"**
3. Choose **PostgreSQL 15**
4. Select **Basic plan** - $15/month (1GB RAM, 1 vCPU, 10GB)
5. Same datacenter as your droplet
6. Name: `fixbulance-db`

### 2.3 Point Domain to Droplet
1. In Digital Ocean, go to **Networking → Domains**
2. Add domain `fixbulance.com`
3. Create A record pointing to your droplet's IP address
4. Update your domain registrar's nameservers to Digital Ocean's

---

## 🤖 Step 3: Server Setup & Configuration

### 3.1 Connect to Your Droplet
```bash
# SSH into your droplet (replace with your droplet's IP)
ssh root@your-droplet-ip

# Or if using SSH key:
ssh -i ~/.ssh/your-key root@your-droplet-ip
```

### 3.2 Install Required Software
```bash
# Update system
apt update && apt upgrade -y

# Install Python, pip, and essential packages
apt install python3 python3-pip python3-venv nginx git curl supervisor -y

# Install PostgreSQL (if not using managed database)
apt install postgresql postgresql-contrib -y

# Install Node.js (for potential frontend assets)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
apt install nodejs -y
```

### 3.3 Setup Application User
```bash
# Create application user
adduser --system --group --home /var/www/fixbulance fixbulance

# Create app directory
mkdir -p /var/www/fixbulance
chown fixbulance:fixbulance /var/www/fixbulance
```

### 3.4 Clone and Setup Application
```bash
# Switch to app user
su - fixbulance

# Clone your repository
cd /var/www/fixbulance
git clone https://github.com/YOUR_USERNAME/fixbulance-app.git .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### 3.5 Environment Configuration
```bash
# Create environment file
nano /var/www/fixbulance/.env
```

Add the following to `.env`:
```bash
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-generate-a-long-random-string
DATABASE_URL=postgresql://username:password@localhost/fixbulance_db
MAIL_SERVER=mail.privateemail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=booking@fixbulance.com
MAIL_PASSWORD=#AsAs1234
STRIPE_PUBLISHABLE_KEY=pk_live_your_stripe_key
STRIPE_SECRET_KEY=sk_live_your_stripe_key
COMPANY_NAME=Fixbulance
COMPANY_PHONE=+1-708-971-4053
COMPANY_EMAIL=booking@fixbulance.com
COMPANY_ADDRESS=Your Business Address
```

---

## 🗄️ Step 4: Database Setup

### 4.1 If Using Managed Database (Recommended)
```bash
# Get connection string from Digital Ocean dashboard
# Update DATABASE_URL in .env file with provided connection string
```

### 4.2 If Using Local PostgreSQL
```bash
# Exit to root user
exit

# Setup PostgreSQL
sudo -u postgres psql

# Create database and user
CREATE DATABASE fixbulance_db;
CREATE USER fixbulance_user WITH PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE fixbulance_db TO fixbulance_user;
\q

# Update .env with local database URL
DATABASE_URL=postgresql://fixbulance_user:secure_password_here@localhost/fixbulance_db
```

### 4.3 Initialize Database
```bash
# Switch back to app user
su - fixbulance
cd /var/www/fixbulance
source venv/bin/activate

# Run database migrations
python production_init.py
```

---

## 🌐 Step 5: Web Server Configuration

### 5.1 Create Gunicorn Service
```bash
# Exit to root user
exit

# Create systemd service file
nano /etc/systemd/system/fixbulance.service
```

Add the following content:
```ini
[Unit]
Description=Fixbulance Flask App
After=network.target

[Service]
User=fixbulance
Group=fixbulance
WorkingDirectory=/var/www/fixbulance
Environment="PATH=/var/www/fixbulance/venv/bin"
EnvironmentFile=/var/www/fixbulance/.env
ExecStart=/var/www/fixbulance/venv/bin/gunicorn --workers 3 --bind unix:fixbulance.sock -m 007 run:app
Restart=always

[Install]
WantedBy=multi-user.target
```

### 5.2 Configure Nginx
```bash
# Create Nginx site configuration
nano /etc/nginx/sites-available/fixbulance
```

Add the following content:
```nginx
server {
    listen 80;
    server_name fixbulance.com www.fixbulance.com;

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/fixbulance/fixbulance.sock;
    }

    location /static {
        alias /var/www/fixbulance/app/static;
    }
}
```

### 5.3 Enable Site and Start Services
```bash
# Enable site
ln -s /etc/nginx/sites-available/fixbulance /etc/nginx/sites-enabled
rm /etc/nginx/sites-enabled/default

# Test Nginx configuration
nginx -t

# Start and enable services
systemctl start fixbulance
systemctl enable fixbulance
systemctl restart nginx
systemctl enable nginx

# Check service status
systemctl status fixbulance
systemctl status nginx
```

---

## 🔒 Step 6: SSL Certificate Setup

### 6.1 Install Certbot
```bash
# Install Certbot
apt install certbot python3-certbot-nginx -y

# Get SSL certificate
certbot --nginx -d fixbulance.com -d www.fixbulance.com

# Test automatic renewal
certbot renew --dry-run
```

---

## 🚀 Step 7: Automated Deployment Setup

### 7.1 Create Deployment Script
```bash
# Switch to app user
su - fixbulance

# Create deployment script
nano /var/www/fixbulance/deploy.sh
```

Add the following content:
```bash
#!/bin/bash
set -e

echo "🚀 Starting deployment..."

# Navigate to app directory
cd /var/www/fixbulance

# Pull latest changes
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
pip install -r requirements.txt

# Run database migrations
python production_init.py

# Collect static files (if needed)
# python manage.py collectstatic --noinput

# Restart the application
sudo systemctl restart fixbulance

echo "✅ Deployment completed successfully!"
```

Make it executable:
```bash
chmod +x /var/www/fixbulance/deploy.sh
```

### 7.2 Setup GitHub Webhook (Optional)
For automatic deployments, you can set up a webhook endpoint that triggers deployment when you push to GitHub.

### 7.3 Developer Workflow
```bash
# Make changes to your code locally
git add .
git commit -m "Fix bug in booking system"
git push origin main

# SSH to server and deploy
ssh fixbulance@your-server-ip
cd /var/www/fixbulance
./deploy.sh
```

---

## 💰 Cost Breakdown

| Component | Cost/Month |
|-----------|------------|
| Basic Droplet (1GB RAM) | $6 |
| Managed PostgreSQL (optional) | $15 |
| **Total (with managed DB)** | **$21/month** |
| **Total (with local DB)** | **$6/month** |

---

## 📊 Production Monitoring

### 7.1 System Monitoring
```bash
# Check application status
systemctl status fixbulance

# View application logs
journalctl -u fixbulance -f

# Check Nginx status and logs
systemctl status nginx
tail -f /var/log/nginx/error.log

# Monitor system resources
htop
df -h
free -h
```

### 7.2 Database Monitoring
```bash
# If using local PostgreSQL
sudo -u postgres psql fixbulance_db
\l
\dt
SELECT * FROM booking LIMIT 5;
```

### 7.3 Log Management
```bash
# Setup log rotation for application logs
nano /etc/logrotate.d/fixbulance
```

Add content:
```
/var/www/fixbulance/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    copytruncate
}
```

---

## 🚨 Troubleshooting

### Application Issues
```bash
# Check application status
systemctl status fixbulance

# View detailed logs
journalctl -u fixbulance -f

# Restart application
sudo systemctl restart fixbulance

# Check if app is listening
ss -tlnp | grep :8000
```

### Web Server Issues
```bash
# Check Nginx status
systemctl status nginx

# Test Nginx configuration
nginx -t

# View Nginx error logs
tail -f /var/log/nginx/error.log

# Restart Nginx
sudo systemctl restart nginx
```

### Database Issues
```bash
# Test database connection
sudo -u fixbulance psql $DATABASE_URL -c "SELECT 1;"

# Check database status (if local)
systemctl status postgresql

# Force database reset (if needed)
cd /var/www/fixbulance
python production_init.py
```

### Email Issues
Verify Namecheap Private Email settings:
- Server: mail.privateemail.com
- Port: 587
- TLS: Enabled
- Username: booking@fixbulance.com
- Password: #AsAs1234

### Permission Issues
```bash
# Fix file permissions
sudo chown -R fixbulance:fixbulance /var/www/fixbulance
sudo chmod -R 755 /var/www/fixbulance
```

---

## ✅ Verification Checklist

After deployment, verify:
- [ ] Website loads at `https://fixbulance.com`
- [ ] SSL certificate is active (green lock)
- [ ] Booking system works
- [ ] Email notifications send
- [ ] Stripe payments process
- [ ] Database operations work
- [ ] Admin interface accessible
- [ ] Application restarts automatically
- [ ] Logs are being generated

### Quick Health Check
```bash
# Test all endpoints
curl -I https://fixbulance.com
curl -I https://fixbulance.com/booking
curl -I https://fixbulance.com/admin

# Check SSL certificate
openssl s_client -connect fixbulance.com:443 -servername fixbulance.com
```

---

## 🎉 Success!

Your Fixbulance app is now live on a production server with:
- ✅ **Dedicated server** with full control
- ✅ **SSL certificate** (free with Let's Encrypt)
- ✅ **Professional web server** (Nginx + Gunicorn)
- ✅ **Database** (PostgreSQL)
- ✅ **Email notifications** working
- ✅ **Payment processing** active
- ✅ **Admin interface** live
- ✅ **Review system** operational
- ✅ **Easy deployment** script
- ✅ **System monitoring** and logging

**Developer Experience**: 
```bash
# Local development
git add .
git commit -m "Fix bug in booking system"
git push origin main

# Deploy to production
ssh fixbulance@your-server
cd /var/www/fixbulance
./deploy.sh
# ↓ 2 minutes later ↓
# Live website updated! 🚀
```

## 🔧 Advanced Features

### Automatic Deployments via Webhook
You can set up a webhook endpoint that automatically deploys when you push to GitHub. This requires additional setup but provides true CI/CD.

### Scaling Options
- **Vertical**: Upgrade droplet to higher CPU/RAM
- **Horizontal**: Add load balancer + multiple droplets
- **Database**: Scale to managed database cluster

### Backup Strategy
- **Database**: Automated daily backups (if using managed DB)
- **Application**: Regular server snapshots
- **Code**: GitHub repository serves as backup

Your Fixbulance app is production-ready! 🚀 