#!/usr/bin/env python3
"""
Tax Implementation Migration Script
Adds tax calculation fields to the Booking model

Usage: python tax_implementation_migration.py
"""

from app import create_app, db
from datetime import datetime
import sys

def run_migration():
    """Add tax fields to existing Booking table"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔄 Starting tax implementation migration...")
            
            # Check if columns already exist (SQLite version)
            with db.engine.connect() as connection:
                try:
                    result = connection.execute(db.text("PRAGMA table_info(booking)"))
                    columns = [row[1] for row in result]  # Column name is at index 1
                    
                    tax_columns = ['tax_rate', 'tax_amount', 'subtotal', 'total_with_tax', 'tax_jurisdiction']
                    existing_tax_columns = [col for col in tax_columns if col in columns]
                    
                    if existing_tax_columns:
                        print(f"⚠️  Tax columns already exist: {existing_tax_columns}")
                        print("Migration may have already been run.")
                        return
                    
                    print("➕ Adding tax calculation fields to booking table...")
                    
                    # Add columns one by one (SQLite limitation)
                    connection.execute(db.text("ALTER TABLE booking ADD COLUMN tax_rate FLOAT DEFAULT 0.1025"))
                    connection.execute(db.text("ALTER TABLE booking ADD COLUMN tax_amount FLOAT DEFAULT 0.0"))
                    connection.execute(db.text("ALTER TABLE booking ADD COLUMN subtotal FLOAT DEFAULT 0.0"))
                    connection.execute(db.text("ALTER TABLE booking ADD COLUMN total_with_tax FLOAT DEFAULT 0.0"))
                    connection.execute(db.text("ALTER TABLE booking ADD COLUMN tax_jurisdiction VARCHAR(100) DEFAULT 'Illinois'"))
                    
                    connection.commit()
                    print("✅ Tax fields added successfully!")
                    
                except Exception as e:
                    print(f"❌ Database error: {str(e)}")
                    raise
            
            # Update existing bookings with tax calculations
            print("🔄 Updating existing bookings with tax calculations...")
            
            from app.models.booking import Booking
            bookings = Booking.query.all()
            
            updated_count = 0
            for booking in bookings:
                try:
                    if booking.total_estimated_cost and booking.service_zip_code:
                        # Calculate tax for existing bookings
                        booking.calculate_tax(booking.total_estimated_cost)
                        updated_count += 1
                except Exception as e:
                    print(f"⚠️  Error updating booking {booking.id}: {str(e)}")
                    continue
            
            db.session.commit()
            print(f"✅ Updated {updated_count} existing bookings with tax calculations")
            
            print("🎉 Tax implementation migration completed successfully!")
            
        except Exception as e:
            print(f"❌ Migration failed: {str(e)}")
            try:
                db.session.rollback()
            except:
                pass
            sys.exit(1)

if __name__ == "__main__":
    run_migration() 