# 🚀 Azure Deployment Guide - Ubuntu Desktop with GUI

## Overview
Deploy your Fixbulance app on Microsoft Azure using Ubuntu Desktop with full GUI interface. This gives you a graphical desktop environment to work with instead of command-line only.

---

## 📋 Prerequisites
- Microsoft Azure account
- GitHub account (already done ✅)
- Domain name (fixbulance.com)
- Stripe account keys
- Email credentials (info@fixbulance.com / #AsAs1234)

---

## 🌐 Step 1: Create Azure Virtual Machine

### 1.1 Sign into Azure Portal
1. Go to [portal.azure.com](https://portal.azure.com)
2. Sign in with your Microsoft account

### 1.2 Create Virtual Machine
1. Click **"Create a resource"**
2. Search for **"Ubuntu"**
3. Select **"Ubuntu Server 22.04 LTS"**
4. Click **"Create"**

### 1.3 VM Configuration
**Basics Tab:**
- **Subscription:** Your Azure subscription
- **Resource group:** Create new → `fixbulance-resources`
- **Virtual machine name:** `fixbulance-vm`
- **Region:** Choose closest to your users (e.g., East US)
- **Image:** Ubuntu Server 22.04 LTS - x64 Gen2
- **Size:** Standard B2s (2 vCPUs, 4 GB RAM) ~ $30/month
- **Authentication:** SSH public key or Password
- **Username:** `azureuser`

**Disks Tab:**
- **OS disk type:** Standard SSD (locally redundant storage)
- **Size:** 30 GB (default)

**Networking Tab:**
- **Virtual network:** Create new or use default
- **Subnet:** Default
- **Public IP:** Create new
- **NIC network security group:** Advanced
- **Configure network security group:** Create new

### 1.4 Network Security Group Rules
Add these inbound port rules:
- **SSH (22):** Source: Any, Destination: Any
- **HTTP (80):** Source: Any, Destination: Any  
- **HTTPS (443):** Source: Any, Destination: Any
- **RDP (3389):** Source: Any, Destination: Any (for GUI access)

### 1.5 Review and Create
1. Click **"Review + create"**
2. Verify configuration
3. Click **"Create"**
4. Wait 3-5 minutes for deployment

---

## 🖥️ Step 2: Install Ubuntu Desktop GUI

### 2.1 Connect via SSH
```bash
# Get the public IP from Azure portal
ssh azureuser@YOUR_VM_PUBLIC_IP
```

### 2.2 Install Ubuntu Desktop
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Ubuntu Desktop (GNOME)
sudo apt install ubuntu-desktop-minimal -y

# Install XRDP for remote desktop access
sudo apt install xrdp -y

# Configure XRDP
sudo systemctl enable xrdp
sudo systemctl start xrdp

# Add user to ssl-cert group
sudo adduser azureuser ssl-cert

# Allow RDP through firewall
sudo ufw allow 3389

# Reboot to complete installation
sudo reboot
```

### 2.3 Connect via Remote Desktop
1. **Windows:** Use built-in Remote Desktop Connection
2. **Mac:** Download Microsoft Remote Desktop from App Store
3. **Linux:** Use Remmina or similar RDP client

**Connection Details:**
- **Computer:** Your VM's public IP address
- **Username:** azureuser
- **Password:** Your VM password

---

## 🔧 Step 3: Automated Setup Script (Azure Version)

### 3.1 Download Setup Script
Open Terminal in Ubuntu Desktop and run:
```bash
# Download Azure setup script
wget https://raw.githubusercontent.com/Zyrex24/fixbulance/main/azure_setup.sh

# Make it executable
chmod +x azure_setup.sh

# Edit configuration
nano azure_setup.sh
# Update: GITHUB_REPO="https://github.com/Zyrex24/fixbulance.git"
```

### 3.2 Run Automated Setup
```bash
sudo ./azure_setup.sh
```

---

## 🌐 Step 4: Domain and DNS Setup

### 4.1 Configure Domain (Option 1: Azure DNS)
1. In Azure Portal, go to **"DNS zones"**
2. Click **"Create DNS zone"**
3. Enter `fixbulance.com`
4. Create the zone
5. Note the Name Servers (4 entries like: ns1-xx.azure-dns.com)

### 4.2 Update Domain Registrar
1. Go to your domain registrar (GoDaddy, Namecheap, etc.)
2. Change nameservers to Azure DNS servers
3. Wait 24-48 hours for propagation

### 4.3 Add DNS Records
In Azure DNS zone, add:
- **A Record:** Name: `@`, Value: `YOUR_VM_PUBLIC_IP`
- **A Record:** Name: `www`, Value: `YOUR_VM_PUBLIC_IP`

---

## 💰 Cost Breakdown (Azure)

| Component | Cost/Month |
|-----------|------------|
| Standard B2s VM (2 vCPU, 4GB RAM) | ~$30 |
| 30GB Premium SSD | ~$5 |
| Public IP Address | ~$3 |
| DNS Zone | ~$0.50 |
| **Total** | **~$38.50/month** |

*Note: Azure offers $200 free credit for new accounts*

---

## 🖥️ Step 5: GUI Development Environment

### 5.1 Install Development Tools
```bash
# Install VS Code
wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > packages.microsoft.gpg
sudo install -o root -g root -m 644 packages.microsoft.gpg /etc/apt/trusted.gpg.d/
sudo sh -c 'echo "deb [arch=amd64,arm64,armhf signed-by=/etc/apt/trusted.gpg.d/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" > /etc/apt/sources.list.d/vscode.list'
sudo apt update
sudo apt install code -y

# Install Firefox (if not already installed)
sudo apt install firefox -y

# Install Git GUI tools
sudo apt install gitg git-cola -y
```

### 5.2 Development Workflow
1. **Code Editor:** VS Code with full GUI
2. **File Manager:** Built-in file manager for easy navigation
3. **Terminal:** GUI terminal for commands
4. **Browser:** Firefox for testing your website
5. **Git GUI:** Visual git management

---

## 🚀 Step 6: Application Management

### 6.1 GUI Application Control
Create desktop shortcuts for easy management:

```bash
# Create desktop shortcut for app management
cat > ~/Desktop/fixbulance-manager.sh << 'EOF'
#!/bin/bash
CHOICE=$(zenity --list --title="Fixbulance Manager" --text="Choose an action:" \
    --column="Action" \
    "Start Application" \
    "Stop Application" \
    "Restart Application" \
    "View Logs" \
    "Deploy Updates" \
    "Open in Browser")

case $CHOICE in
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
        gnome-terminal -- /var/www/fixbulance/deploy.sh
        ;;
    "Open in Browser")
        firefox https://fixbulance.com
        ;;
esac
EOF

chmod +x ~/Desktop/fixbulance-manager.sh
```

### 6.2 Database Management GUI
```bash
# Install pgAdmin for PostgreSQL management
curl https://www.pgadmin.org/static/packages_pgadmin_org.pub | sudo apt-key add
sudo sh -c 'echo "deb https://ftp.postgresql.org/pub/pgadmin/pgadmin4/apt/$(lsb_release -cs) pgadmin4 main" > /etc/apt/sources.list.d/pgadmin4.list'
sudo apt update
sudo apt install pgadmin4-desktop -y
```

---

## ✅ Verification Steps

### 6.1 Test Your Setup
1. **Website Access:** Open Firefox → `https://fixbulance.com`
2. **Admin Panel:** `https://fixbulance.com/admin`
3. **Booking System:** `https://fixbulance.com/booking`
4. **SSL Certificate:** Green lock icon in browser

### 6.2 System Health Check
```bash
# Check all services
sudo systemctl status fixbulance nginx postgresql

# Check website response
curl -I https://fixbulance.com

# View application logs
sudo journalctl -u fixbulance -n 50
```

---

## 🔒 Security Considerations

### 6.1 Firewall Configuration
```bash
# Configure UFW firewall
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw allow 3389  # RDP for GUI access
```

### 6.2 Secure RDP Access
Consider restricting RDP access to your IP:
1. Azure Portal → Network Security Group
2. Edit RDP rule
3. Change Source from "Any" to "My IP address"

---

## 🎉 Advantages of Azure + GUI Setup

### ✅ **Benefits:**
- **Visual Interface:** Full Ubuntu desktop environment
- **Easy Management:** GUI tools for database, files, logs
- **Development Ready:** VS Code, browsers, git tools included
- **Azure Integration:** Easy scaling, monitoring, backups
- **Enterprise Grade:** Microsoft's enterprise infrastructure
- **Remote Access:** Work from anywhere with RDP

### ✅ **Perfect For:**
- **Visual Learners:** GUI makes everything easier to understand
- **Development:** Full IDE and debugging tools
- **Database Management:** pgAdmin for visual database operations
- **File Management:** Easy drag-and-drop file operations
- **Monitoring:** Visual system monitoring tools

---

## 🚀 Future Deployments

### Easy Update Process:
1. **RDP into your VM**
2. **Open Terminal**
3. **Navigate to project:** `cd /var/www/fixbulance`
4. **Run deploy script:** `./deploy.sh`
5. **Monitor in browser:** Check `https://fixbulance.com`

### Or use the GUI manager:
1. **Double-click** `fixbulance-manager.sh` on desktop
2. **Select** "Deploy Updates"
3. **Done!** ✨

Your Fixbulance app is now running on Azure with full GUI access! 🎉 