#!/bin/bash

# =============================================================================
# FIXBULANCE GITHUB SETUP SCRIPT
# =============================================================================
# Script to initialize git repository and push all files to GitHub
# Run this script in your local Fixbulance directory
# =============================================================================

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "run.py" ] || [ ! -d "app" ]; then
    echo "ERROR: This script must be run in the Fixbulance application directory"
    echo "Please navigate to the directory containing run.py and the app/ folder"
    exit 1
fi

log "Initializing Fixbulance GitHub repository..."

# Get GitHub username and repository name
echo ""
info "Please enter your GitHub username:"
read -p "GitHub username: " GITHUB_USERNAME

if [ -z "$GITHUB_USERNAME" ]; then
    echo "ERROR: GitHub username is required"
    exit 1
fi

echo ""
info "Please enter your repository name (default: fixbulance-flask-app):"
read -p "Repository name [fixbulance-flask-app]: " REPO_NAME
REPO_NAME=${REPO_NAME:-fixbulance-flask-app}

echo ""
info "Repository will be: https://github.com/${GITHUB_USERNAME}/${REPO_NAME}"
read -p "Is this correct? (y/n): " CONFIRM

if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo "Exiting..."
    exit 1
fi

# Create .gitignore file
log "Creating .gitignore file..."
cat > .gitignore << EOF
# Python
__pycache__/
*.py[cod]
*\$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual Environment
venv/
env/
ENV/

# Flask
instance/
.env
*.db

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Logs
logs/
*.log

# Backups
backups/
*.backup

# Media uploads
media/

# Temporary files
*.tmp
*.temp

# Node modules (if any)
node_modules/

# Coverage reports
htmlcov/
.coverage
.coverage.*
coverage.xml
*.cover
.hypothesis/
.pytest_cache/

# Environment variables
.env.local
.env.production
.env.development
EOF

# Initialize git repository
log "Initializing git repository..."
git init

# Add all files
log "Adding files to git repository..."
git add .

# Create initial commit
log "Creating initial commit..."
git commit -m "Initial Fixbulance Flask application commit

Features included:
- Complete Flask application with admin dashboard
- Multi-step booking wizard
- Device pricing system (iPhone & Samsung)
- Digital waiver system
- Stripe payment integration
- Email notification system
- Production deployment scripts
- Digital Ocean deployment configuration

Business: Fixbulance LLC - Mobile Phone Repair Service
Owner: Ahmed Khalil - (708) 971-4053"

# Set main branch
log "Setting main branch..."
git branch -M main

# Add remote origin
log "Adding GitHub remote..."
git remote add origin https://github.com/${GITHUB_USERNAME}/${REPO_NAME}.git

echo ""
warning "IMPORTANT: Before pushing to GitHub:"
info "1. Go to GitHub.com and create a new repository named: ${REPO_NAME}"
info "2. Set it to Private (recommended) or Public"
info "3. Do NOT initialize with README, .gitignore, or license"
echo ""
read -p "Have you created the repository on GitHub? (y/n): " REPO_CREATED

if [ "$REPO_CREATED" != "y" ] && [ "$REPO_CREATED" != "Y" ]; then
    echo ""
    warning "Please create the repository on GitHub first, then run:"
    info "git push -u origin main"
    exit 0
fi

# Push to GitHub
log "Pushing to GitHub..."
git push -u origin main

if [ $? -eq 0 ]; then
    log "Successfully pushed to GitHub!"
    echo ""
    info "=== NEXT STEPS ==="
    info "1. Your code is now on GitHub: https://github.com/${GITHUB_USERNAME}/${REPO_NAME}"
    info "2. Set up Digital Ocean Droplet"
    info "3. Update deploy_production.sh with your repository URL:"
    info "   REPO_URL=\"https://github.com/${GITHUB_USERNAME}/${REPO_NAME}.git\""
    info "4. Run the deployment script on your server"
    echo ""
    info "For detailed deployment instructions, see: DIGITAL_OCEAN_SETUP.md"
else
    echo "ERROR: Failed to push to GitHub"
    echo "Please check your credentials and repository settings"
    exit 1
fi

log "GitHub setup completed successfully!" 