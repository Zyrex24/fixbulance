#!/usr/bin/env python3
"""
Production initialization script for Digital Ocean App Platform
This script runs automatically during deployment to set up the database
"""
import os
import sys
from flask import Flask
from flask_migrate import upgrade
from app import create_app

def init_production():
    """Initialize production environment"""
    print("🚀 Starting production initialization...")
    
    # Create Flask app
    app = create_app()
    
    with app.app_context():
        try:
            # Run database migrations
            print("📊 Running database migrations...")
            upgrade()
            print("✅ Database migrations completed successfully")
            
            # Verify database connection
            from app.models import User, Booking, Service
            from sqlalchemy import text
            from app import db
            
            # Test database connection
            result = db.session.execute(text('SELECT 1'))
            print("✅ Database connection verified")
            
            # Create any missing tables
            db.create_all()
            print("✅ Database tables verified/created")
            
            print("🎉 Production initialization completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Production initialization failed: {str(e)}")
            return False

if __name__ == "__main__":
    success = init_production()
    sys.exit(0 if success else 1) 