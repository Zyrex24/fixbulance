#!/usr/bin/env python3
"""
Production initialization script for Digital Ocean Droplet
This script runs automatically during deployment to set up the database
"""
import os
import sys
from flask import Flask
from flask_migrate import init, migrate, upgrade
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
                
                # Create initial migration
                print("📝 Creating initial migration...")
                migrate(message='Initial migration')
                print("✅ Initial migration created")
            
            # Run database migrations
            print("📊 Running database migrations...")
            upgrade()
            print("✅ Database migrations completed successfully")
            
            # Import models to ensure they're registered
            from app.models import User, Booking, Service, Review
            
            # Create any missing tables (fallback)
            print("🔧 Ensuring all tables exist...")
            db.create_all()
            print("✅ Database tables verified/created")
            
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