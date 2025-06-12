#!/usr/bin/env python3
"""
Database migration script to add ServiceWaiver table
Run this script to add the waiver functionality to your existing database
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.abspath('.'))

# Import from the app factory
from app import create_app, db

def create_waiver_table():
    """Create the ServiceWaiver table"""
    app = create_app()
    with app.app_context():
        try:
            # Create the table
            db.create_all()
            print("✅ ServiceWaiver table created successfully!")
            
            # Verify table exists
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'service_waiver' in tables:
                print("✅ Table 'service_waiver' verified in database")
                
                # Show table columns
                columns = inspector.get_columns('service_waiver')
                print(f"✅ Table has {len(columns)} columns:")
                for col in columns:
                    print(f"   - {col['name']} ({col['type']})")
            else:
                print("❌ Table 'service_waiver' not found")
                
        except Exception as e:
            print(f"❌ Error creating waiver table: {e}")
            return False
            
    return True

if __name__ == '__main__':
    print("🚀 Creating ServiceWaiver table...")
    success = create_waiver_table()
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("📋 Next steps:")
        print("   1. Test waiver functionality by creating a booking")
        print("   2. Access waiver at: /booking/<booking_id>/waiver")
        print("   3. View admin waivers at: /admin/waivers")
    else:
        print("\n❌ Migration failed!")
        sys.exit(1) 