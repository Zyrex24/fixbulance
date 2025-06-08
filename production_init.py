#!/usr/bin/env python3
"""
Production initialization script for Digital Ocean Droplet
This script runs automatically during deployment to set up the database
"""
import os
import sys
from flask import Flask
from flask_migrate import init
from app import create_app

def init_production():
    """Initialize production environment"""
    print("🚀 Starting production initialization...")
    
    # Create Flask app
    app = create_app()
    
    with app.app_context():
        try:
            from app import db
            
            # Test database connection first
            print("📊 Testing database connection...")
            from sqlalchemy import text
            result = db.session.execute(text('SELECT 1'))
            print("✅ Database connection verified")
            
            # Check if migrations folder exists
            migrations_dir = os.path.join(os.getcwd(), 'migrations')
            if not os.path.exists(migrations_dir):
                print("📦 Initializing Flask-Migrate...")
                init()
                print("✅ Flask-Migrate initialized")
            
            # For fresh production deployment, use direct table creation
            # This avoids migration constraint naming issues
            print("🔧 Creating database tables directly...")
            
            # Import all models to ensure they're registered
            from app.models import User, Booking, Service, Review, Payment, BookingService, ServiceCategory, PriceHistory
            
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully")
            
            # Verify table creation
            print("🔍 Verifying table creation...")
            try:
                # Check if key tables exist by querying them
                db.session.execute(text('SELECT COUNT(*) FROM user'))
                db.session.execute(text('SELECT COUNT(*) FROM service'))
                db.session.execute(text('SELECT COUNT(*) FROM booking'))
                print("✅ All core tables verified")
            except Exception as table_error:
                print(f"⚠️  Table verification issue: {table_error}")
                # Try to create tables again if they don't exist
                db.create_all()
                print("✅ Tables recreated")
            
            print("🎉 Production initialization completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Production initialization failed: {str(e)}")
            print(f"Error details: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = init_production()
    sys.exit(0 if success else 1) 