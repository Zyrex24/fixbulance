# Digital Ocean Deployment Guide for Fixbulance

## 🌊 Digital Ocean Setup for Fixbulance Flask Application

### 📋 Prerequisites
- Digital Ocean account
- Domain name (recommended: fixbulance.com)
- GitHub account
- Basic SSH knowledge

## 🚀 Step 1: Create Digital Ocean Droplet

### 1.1 Droplet Configuration
```
Choose an image: Ubuntu 22.04 (LTS) x64
Choose a plan: Basic ($6/month - 1 vCPU, 1GB RAM, 25GB SSD)
Choose a datacenter region: [Choose closest to your users]
Authentication: SSH keys (recommended) or Password
Choose a hostname: fixbulance-production
```

### 1.2 Recommended Droplet Specs for Fixbulance
- **Minimum**: 1GB RAM, 1 vCPU, 25GB SSD ($6/month)
- **Recommended**: 2GB RAM, 1 vCPU, 50GB SSD ($12/month)
- **High Traffic**: 4GB RAM, 2 vCPU, 80GB SSD ($24/month)

## 🔐 Step 2: Initial Server Access

### 2.1 Connect via SSH
```bash
# Replace YOUR_SERVER_IP with your droplet's IP address
ssh root@YOUR_SERVER_IP
```

### 2.2 Update System
```bash
apt update && apt upgrade -y
```

## 📂 Step 3: GitHub Repository Setup

### 3.1 Create GitHub Repository
1. Go to GitHub and create a new repository: `fixbulance-flask-app`
2. Set it to **Public** or **Private** (Private recommended for production)

### 3.2 Upload Application Files
```bash
# On your local machine, navigate to your application directory
cd /path/to/your/fixbulance/app

# Initialize git repository
git init
git add .
git commit -m "Initial Fixbulance application commit"

# Add remote origin (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/fixbulance-flask-app.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## 🛠️ Step 4: Deploy Application

### 4.1 Upload Deployment Script
```bash
# Copy the deploy_production.sh script to your server
scp deploy_production.sh root@YOUR_SERVER_IP:/root/

# Connect to server
ssh root@YOUR_SERVER_IP

# Make script executable
chmod +x /root/deploy_production.sh
```

### 4.2 Update Script Configuration
Edit the deployment script with your specific details:
```bash
nano /root/deploy_production.sh

# Update these variables:
DOMAIN="your-domain.com"  # Your actual domain
REPO_URL="https://github.com/YOUR_USERNAME/fixbulance-flask-app.git"
```

### 4.3 Run Deployment Script
```bash
# Execute the deployment script
./deploy_production.sh
```

## 🌐 Step 5: Domain Setup

### 5.1 Point Domain to Droplet
1. Go to your domain registrar (GoDaddy, Namecheap, etc.)
2. Update DNS records:
   ```
   Type: A
   Name: @
   Value: YOUR_DROPLET_IP
   TTL: 300

   Type: A  
   Name: www
   Value: YOUR_DROPLET_IP
   TTL: 300
   ```

### 5.2 Set up SSL Certificate
```bash
# After DNS propagation (5-30 minutes), run:
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

## 🔧 Step 6: GitHub Actions Setup (Optional Automated Deployment)

### 6.1 Generate SSH Key for GitHub Actions
```bash
# On your server, generate SSH key
ssh-keygen -t rsa -b 4096 -f ~/.ssh/github_actions

# Add public key to authorized_keys
cat ~/.ssh/github_actions.pub >> ~/.ssh/authorized_keys

# Display private key (copy this for GitHub secrets)
cat ~/.ssh/github_actions
```

### 6.2 Configure GitHub Secrets
Go to your GitHub repository → Settings → Secrets and variables → Actions

Add these secrets:
```
HOST: Your_Droplet_IP_Address
USERNAME: fixbulance
SSH_KEY: [Paste the private key from previous step]
PORT: 22
```

### 6.3 Test Automated Deployment
```bash
# Make a small change to your code and push
echo "# Test" >> README.md
git add .
git commit -m "Test automated deployment"
git push origin main
```

## 🔒 Step 7: Security Configuration

### 7.1 Create Non-Root User (Done by script)
The deployment script creates a `fixbulance` user for security.

### 7.2 Configure Firewall (Done by script)
- SSH (port 22)
- HTTP (port 80)
- HTTPS (port 443)

### 7.3 Fail2Ban Protection (Done by script)
Automatically blocks IPs after failed login attempts.

## 📧 Step 8: Email Configuration

### 8.1 Update Environment Variables
```bash
# Edit the .env file
sudo nano /var/www/fixbulance/.env

# Update email credentials:
MAIL_PASSWORD=your_namecheap_email_password
```

### 8.2 Test Email Functionality
```bash
# Restart application after updating environment
sudo systemctl restart fixbulance
```

## 💳 Step 9: Stripe Configuration

### 9.1 Get Stripe API Keys
1. Go to Stripe Dashboard
2. Get your Live API keys:
   - Publishable key: `pk_live_...`
   - Secret key: `sk_live_...`
   - Webhook secret: `whsec_...`

### 9.2 Update Environment Variables
```bash
sudo nano /var/www/fixbulance/.env

# Update Stripe configuration:
STRIPE_PUBLISHABLE_KEY=pk_live_your_actual_key
STRIPE_SECRET_KEY=sk_live_your_actual_key
STRIPE_WEBHOOK_SECRET=whsec_your_actual_secret
```

### 9.3 Configure Stripe Webhooks
1. In Stripe Dashboard → Webhooks
2. Add endpoint: `https://yourdomain.com/stripe/webhook`
3. Select events: `payment_intent.succeeded`, `payment_intent.payment_failed`

## 📊 Step 10: Monitoring and Maintenance

### 10.1 Application Monitoring
```bash
# Check application status
sudo systemctl status fixbulance

# View application logs
sudo journalctl -u fixbulance -f

# Check Nginx status
sudo systemctl status nginx

# View Nginx logs
sudo tail -f /var/log/nginx/error.log
```

### 10.2 Database Backup (Automated)
The deployment script sets up automatic daily backups at 2 AM.

```bash
# Manual backup
/var/www/fixbulance/backup.sh

# View backups
ls -la /var/www/fixbulance/backups/
```

### 10.3 Update Application
```bash
# Manual update (or use GitHub Actions)
cd /var/www/fixbulance
git pull origin main
sudo systemctl restart fixbulance
```

## 🏢 Step 11: Business Configuration

### 11.1 Admin Access
- **URL**: https://yourdomain.com/admin
- **Default Login**: admin@fixbulance.com / admin123
- **Change password immediately after first login**

### 11.2 Business Settings
1. Update system settings in admin panel
2. Configure service pricing
3. Set up device pricing catalog
4. Test booking process

## 🆘 Troubleshooting

### Common Issues

#### Application Won't Start
```bash
# Check logs
sudo journalctl -u fixbulance -n 50

# Check Python environment
sudo -u fixbulance bash
cd /var/www/fixbulance
source venv/bin/activate
python run.py
```

#### Database Issues
```bash
# Check database permissions
ls -la /var/www/fixbulance/instance/

# Recreate database if needed
cd /var/www/fixbulance
source venv/bin/activate
python production_init.py
```

#### SSL Certificate Issues
```bash
# Renew certificate
sudo certbot renew

# Check certificate status
sudo certbot certificates
```

#### Nginx Issues
```bash
# Test Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx

# Check Nginx status
sudo systemctl status nginx
```

## 💰 Cost Breakdown

### Monthly Costs (USD)
- **Droplet**: $6-24/month (depending on size)
- **Domain**: $10-15/year
- **SSL Certificate**: Free (Let's Encrypt)
- **Backups**: Free (included in deployment)
- **Email**: $1-5/month (Namecheap Private Email)

### Total Monthly: ~$7-30/month

## 📞 Support

### Fixbulance Contact
- **Business Owner**: Ahmed Khalil - (708) 971-4053
- **Support Email**: support@fixbulance.com

### Digital Ocean Support
- Community forum: https://www.digitalocean.com/community
- Documentation: https://docs.digitalocean.com/

## ✅ Deployment Checklist

- [ ] Create Digital Ocean Droplet
- [ ] Upload application to GitHub
- [ ] Run deployment script
- [ ] Configure domain DNS
- [ ] Set up SSL certificate
- [ ] Configure email credentials
- [ ] Configure Stripe credentials
- [ ] Test application functionality
- [ ] Set up GitHub Actions (optional)
- [ ] Change default admin password
- [ ] Configure monitoring
- [ ] Test backup system

---

**🎉 Congratulations! Your Fixbulance application is now live on Digital Ocean!**

Visit: `https://yourdomain.com` to see your application in action. 