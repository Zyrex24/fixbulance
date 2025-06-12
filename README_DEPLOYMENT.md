# Fixbulance Flask Application - Local Deployment Guide

## 📱 About Fixbulance
**Mobile Phone Repair Service Platform** - A comprehensive Flask web application for managing mobile device repair services.

- **Business Owner**: Ahmed Khalil
- **Phone**: (708) 971-4053  
- **Email**: support@fixbulance.com
- **Service Area**: Orland Park, IL (10-mile radius)

## 🚀 Quick Start (Local Development)

### 1. Prerequisites
- **Python 3.8+** (Recommended: Python 3.9 or 3.10)
- **pip** (Python package manager)
- **Virtual Environment** (recommended)

### 2. Setup Instructions

```bash
# 1. Extract the zip file
unzip Fixbulance_Flask_App.zip
cd Fixbulance_Flask_App

# 2. Create and activate virtual environment
python -m venv venv

# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Initialize database (run migration scripts)
python create_system_settings_table.py
python create_waiver_table.py
python device_pricing_migration.py
python multi_service_migration.py
python stripe_migration.py
python tax_implementation_migration.py

# 5. Create initial admin user (optional)
python production_init.py

# 6. Run the application
python run.py
```

### 3. Access the Application
- **URL**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin
- **Default Admin Login** (if created via production_init.py):
  - Email: admin@fixbulance.com
  - Password: admin123

## 📁 Project Structure

```
Fixbulance_Flask_App/
├── app/                          # Main application package
│   ├── blueprints/              # Route handlers
│   │   ├── admin.py            # Admin dashboard routes
│   │   ├── auth.py             # Authentication routes
│   │   ├── booking.py          # Booking wizard routes
│   │   ├── main.py             # Public pages routes
│   │   └── device_pricing.py   # Device pricing management
│   ├── models/                  # Database models
│   │   ├── user.py             # User authentication model
│   │   ├── booking.py          # Booking management model
│   │   ├── service.py          # Service catalog model
│   │   ├── waiver.py           # Digital waiver model
│   │   └── device_pricing.py   # Device pricing model
│   ├── templates/               # HTML templates
│   │   ├── admin/              # Admin interface templates
│   │   ├── auth/               # Authentication templates
│   │   ├── booking/            # Booking wizard templates
│   │   └── components/         # Reusable components
│   ├── static/                  # Static files (CSS, JS, images)
│   │   ├── css/                # Stylesheets
│   │   ├── js/                 # JavaScript files
│   │   └── images/             # Image assets
│   ├── forms/                   # WTForms form classes
│   └── services/                # Business logic services
├── config/                      # Configuration files
│   └── config.py               # Application configuration
├── run.py                      # Application entry point
├── requirements.txt            # Python dependencies
└── *.migration.py              # Database migration scripts
```

## 🛠️ Configuration

### Environment Variables
Create a `.env` file in the root directory:

```env
# Flask Configuration
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# Database Configuration
DATABASE_URL=sqlite:///instance/repair_service_dev.db

# Email Configuration (Namecheap Private Email)
MAIL_SERVER=mail.privateemail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=info@fixbulance.com
MAIL_PASSWORD=your-email-password

# Stripe Configuration (for payment processing)
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_key
STRIPE_SECRET_KEY=sk_test_your_stripe_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
```

### Database Setup
The application uses SQLite by default. Database files are stored in `instance/` directory:
- **Development**: `repair_service_dev.db`
- **Production**: `repair_service.db`

## 🔧 Key Features

### Customer Features
- **Multi-Step Booking Wizard**: Device selection → Service selection → Details → Location → Authentication → Scheduling → Payment
- **Device Pricing Lookup**: Real-time pricing for iPhone and Samsung devices
- **Service Area Validation**: 10-mile radius coverage from Orland Park, IL
- **Digital Waiver System**: Legal waiver with digital signature
- **Payment Processing**: Stripe integration for deposits and final payments
- **Email Verification**: Account verification system

### Admin Features
- **Dashboard**: Emergency dispatch overview with real-time van status
- **Booking Management**: Complete booking lifecycle management
- **Customer Management**: Customer profiles and communication history
- **Service Management**: Device pricing and service catalog management
- **Waiver Management**: Digital waiver review and void capability
- **Payment Management**: Stripe payment processing and refund handling

## 📊 Database Migration Scripts

**Required Scripts** (run in order):
1. `create_system_settings_table.py` - Global system settings
2. `create_waiver_table.py` - Digital waiver system
3. `device_pricing_migration.py` - Device pricing catalog (30 iPhone + 39 Samsung models)
4. `multi_service_migration.py` - Multi-service booking support
5. `stripe_migration.py` - Payment processing integration
6. `tax_implementation_migration.py` - Tax calculation system

## 🎨 UI/UX Features
- **Bootstrap 5**: Modern, responsive design
- **Navy/White/Red Branding**: Professional Fixbulance color scheme
- **Mobile-Optimized**: Touch-friendly interface for van operations
- **Real-time Updates**: AJAX-powered interactions
- **Professional Templates**: Card-based layouts with visual feedback

## 🔒 Security Features
- **CSRF Protection**: Form security across all interfaces
- **Password Hashing**: Secure user authentication
- **Email Verification**: Account activation system
- **Digital Signatures**: Legal waiver compliance
- **Stripe Security**: PCI-compliant payment processing

## 📞 Support & Contact
- **Business Owner**: Ahmed Khalil - (708) 971-4053
- **Technical Support**: support@fixbulance.com
- **Admin Support**: admin@fixbulance.com
- **Billing**: billing@fixbulance.com

## 🚀 Production Deployment
For production deployment:
1. Set `FLASK_ENV=production`
2. Use a production WSGI server (Gunicorn included)
3. Configure proper email credentials
4. Set up Stripe live API keys
5. Use PostgreSQL or MySQL for production database

## 📄 Legal Pages
The application includes comprehensive legal documentation:
- **Terms of Service**: /terms
- **Privacy Policy**: /privacy  
- **Refund Policy**: /refund

All policies effective June 9, 2025, with contact via support@fixbulance.com.

---

**Application Status**: ✅ Production-Ready
**Last Updated**: January 2025
**Version**: v2.0 (Complete Flask Implementation) 