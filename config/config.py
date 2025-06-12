import os
from datetime import timedelta

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Email settings (Gmail for testing - comment out Namecheap section above if using this)
    # MAIL_SERVER = 'smtp.gmail.com'  # Gmail SMTP for testing
    # MAIL_PORT = 587
    # MAIL_USE_TLS = True
    # MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'your_gmail@gmail.com'
    # MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')  # Gmail App Password
    
    # Email settings (Namecheap) - CURRENT
    MAIL_SERVER = 'mail.privateemail.com'  # Namecheap Private Email SMTP
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'info@fixbulance.com'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or '#AsAs1234' # Must be set as environment variable
    MAIL_DEBUG = True  # Enable debug logging
    MAIL_SUPPRESS_SEND = False  # Allow sending emails
    
    # Fixbulance Email Addresses
    MAIL_DEFAULT_SENDER = 'info@fixbulance.com'
    MAIL_SUPPORT = 'support@fixbulance.com'
    MAIL_ADMIN = 'admin@fixbulance.com'
    MAIL_BILLING = 'billing@fixbulance.com'
    MAIL_APPOINTMENTS = 'appointments@fixbulance.com'
    MAIL_BOOKING = 'booking@fixbulance.com'
    
    # Business Owner Information
    BUSINESS_OWNER_FIRST_NAME = 'Ahmed'
    BUSINESS_OWNER_LAST_NAME = 'Khalil'
    BUSINESS_PHONE = '+1 708 971 4053'
    BUSINESS_PHONE_DISPLAY = '(708) 971-4053'
    
    # Stripe settings
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    # Stripe business configuration
    STRIPE_BUSINESS_NAME = 'Fixbulance'
    STRIPE_BUSINESS_DESCRIPTION = 'Mobile Phone Repair Service'
    STRIPE_SUCCESS_URL = os.environ.get('STRIPE_SUCCESS_URL', 'http://localhost:5000/booking/payment-success')
    STRIPE_CANCEL_URL = os.environ.get('STRIPE_CANCEL_URL', 'http://localhost:5000/booking/payment-cancel')
    
    # Payment settings
    DEPOSIT_AMOUNT = 15.00  # Fixed $15 deposit for all bookings
    MINIMUM_PAYMENT_AMOUNT = 1.00  # Minimum payment amount in USD
    
    # SMS settings (Twilio)
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')
    
    # Google Maps API
    GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    
    # Upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = 'app/static/uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # Service area settings
    DEFAULT_SERVICE_RADIUS = 10  # miles
    BUSINESS_ZIP_CODE = '60462'  # Orland Park, IL
    
    # Communication budget limits
    MONTHLY_SMS_BUDGET = 200  # ~$15/month
    MONTHLY_EMAIL_LIMIT = 3000  # SendGrid free tier

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///repair_service_dev.db'
    
    # Stripe keys must be set via environment variables
    # Create a .env file or set these environment variables:
    # STRIPE_PUBLISHABLE_KEY=pk_test_your_key_here
    # STRIPE_SECRET_KEY=sk_test_your_key_here
    # STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://username:password@localhost/repair_service'
    
    # Security settings for production
    SESSION_COOKIE_SECURE = True
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 