#!/usr/bin/env python3

"""
Multi-Service Booking System Database Migration
===============================================

This script migrates the existing single-service booking system to support
multi-service bookings with admin price management capabilities.

CHANGES:
1. Create new tables: service_category, booking_service, price_history
2. Add new fields to existing service table
3. Add new fields to existing booking table
4. Migrate existing bookings to use new BookingService junction table
5. Create default service categories
6. Update existing services with enhanced pricing fields

SAFETY FEATURES:
- Backup existing data before migration
- Rollback capability if migration fails
- Data validation after migration
- Preserve all existing functionality

Run with: python multi_service_migration.py
"""

import sys
import os
import json
import sqlite3
from datetime import datetime, timezone

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db

class MultiServiceMigration:
    def __init__(self):
        self.app = create_app()
        self.backup_data = {}
        
    def log(self, message):
        """Log migration progress"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def backup_existing_data(self):
        """Backup existing data before migration using raw SQL"""
        self.log("🔄 Backing up existing data...")
        
        with self.app.app_context():
            # Use raw SQL to backup data without relying on updated models
            connection = db.engine.raw_connection()
            cursor = connection.cursor()
            
            # Backup services using raw SQL
            cursor.execute("SELECT * FROM service")
            service_columns = [description[0] for description in cursor.description]
            service_rows = cursor.fetchall()
            
            self.backup_data['services'] = [
                dict(zip(service_columns, row)) for row in service_rows
            ]
            
            # Backup bookings using raw SQL
            cursor.execute("SELECT * FROM booking")
            booking_columns = [description[0] for description in cursor.description]
            booking_rows = cursor.fetchall()
            
            self.backup_data['bookings'] = [
                dict(zip(booking_columns, row)) for row in booking_rows
            ]
            
            cursor.close()
            connection.close()
            
        # Save backup to file
        backup_filename = f"migration_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(backup_filename, 'w') as f:
            json.dump(self.backup_data, f, indent=2, default=str)
            
        self.log(f"✅ Data backed up to {backup_filename}")
        return backup_filename
    
    def create_new_tables(self):
        """Create new database tables and add columns to existing tables"""
        self.log("🔄 Creating new database tables and updating existing ones...")
        
        with self.app.app_context():
            connection = db.engine.raw_connection()
            cursor = connection.cursor()
            
            try:
                # Create new tables using raw SQL
                self.log("   Creating service_category table...")
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS service_category (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name VARCHAR(100) NOT NULL UNIQUE,
                        description TEXT,
                        sort_order INTEGER DEFAULT 0,
                        is_active BOOLEAN DEFAULT 1,
                        is_emergency BOOLEAN DEFAULT 0,
                        requires_admin_approval BOOLEAN DEFAULT 0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                self.log("   Creating booking_service table...")
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS booking_service (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        booking_id INTEGER NOT NULL,
                        service_id INTEGER NOT NULL,
                        quantity INTEGER DEFAULT 1 NOT NULL,
                        price_snapshot DECIMAL(10, 2) NOT NULL,
                        labor_cost DECIMAL(10, 2) DEFAULT 0.00,
                        parts_cost DECIMAL(10, 2) DEFAULT 0.00,
                        estimated_time INTEGER DEFAULT 60,
                        actual_time INTEGER,
                        status VARCHAR(20) DEFAULT 'pending',
                        work_notes TEXT,
                        completion_notes TEXT,
                        started_at DATETIME,
                        completed_at DATETIME,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (booking_id) REFERENCES booking (id),
                        FOREIGN KEY (service_id) REFERENCES service (id)
                    )
                """)
                
                self.log("   Creating price_history table...")
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS price_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        service_id INTEGER NOT NULL,
                        changed_by_user_id INTEGER NOT NULL,
                        field_changed VARCHAR(50) NOT NULL,
                        old_value DECIMAL(10, 2),
                        new_value DECIMAL(10, 2),
                        change_reason VARCHAR(200),
                        admin_notes TEXT,
                        batch_id VARCHAR(50),
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (service_id) REFERENCES service (id),
                        FOREIGN KEY (changed_by_user_id) REFERENCES user (id)
                    )
                """)
                
                # Add new columns to existing service table
                self.log("   Adding new columns to service table...")
                new_service_columns = [
                    "ALTER TABLE service ADD COLUMN category_id INTEGER",
                    "ALTER TABLE service ADD COLUMN labor_cost DECIMAL(10, 2) DEFAULT 0.00",
                    "ALTER TABLE service ADD COLUMN parts_cost DECIMAL(10, 2) DEFAULT 0.00",
                    "ALTER TABLE service ADD COLUMN is_emergency BOOLEAN DEFAULT 0",
                    "ALTER TABLE service ADD COLUMN allows_multiple BOOLEAN DEFAULT 1",
                    "ALTER TABLE service ADD COLUMN max_quantity INTEGER DEFAULT 1",
                    "ALTER TABLE service ADD COLUMN last_price_update DATETIME",
                    "ALTER TABLE service ADD COLUMN last_updated_by INTEGER"
                ]
                
                for alter_sql in new_service_columns:
                    try:
                        cursor.execute(alter_sql)
                        column_name = alter_sql.split("ADD COLUMN ")[1].split()[0]
                        self.log(f"      Added column: {column_name}")
                    except sqlite3.OperationalError as e:
                        if "duplicate column name" in str(e):
                            column_name = alter_sql.split("ADD COLUMN ")[1].split()[0]
                            self.log(f"      Column already exists: {column_name}")
                        else:
                            raise e
                
                # Add new columns to existing booking table
                self.log("   Adding new columns to booking table...")
                new_booking_columns = [
                    "ALTER TABLE booking ADD COLUMN total_services_count INTEGER DEFAULT 1",
                    "ALTER TABLE booking ADD COLUMN combined_estimated_duration INTEGER DEFAULT 60"
                ]
                
                for alter_sql in new_booking_columns:
                    try:
                        cursor.execute(alter_sql)
                        column_name = alter_sql.split("ADD COLUMN ")[1].split()[0]
                        self.log(f"      Added column: {column_name}")
                    except sqlite3.OperationalError as e:
                        if "duplicate column name" in str(e):
                            column_name = alter_sql.split("ADD COLUMN ")[1].split()[0]
                            self.log(f"      Column already exists: {column_name}")
                        else:
                            raise e
                
                connection.commit()
                
            except Exception as e:
                connection.rollback()
                raise e
            finally:
                cursor.close()
                connection.close()
            
        self.log("✅ New tables and columns created successfully")
    
    def create_default_categories(self):
        """Create default service categories"""
        self.log("🔄 Creating default service categories...")
        
        with self.app.app_context():
            connection = db.engine.raw_connection()
            cursor = connection.cursor()
            
            try:
                categories = [
                    (1, 'Emergency Repairs', 'Urgent repairs that need immediate attention', 1, 1, 0),
                    (2, 'Standard Repairs', 'Regular repair services', 2, 0, 0),
                    (3, 'Premium Services', 'High-end repair and upgrade services', 3, 0, 1),
                    (4, 'Diagnostic Services', 'Device diagnosis and assessment', 4, 0, 0)
                ]
                
                created_categories = {}
                for cat_id, name, description, sort_order, is_emergency, requires_admin_approval in categories:
                    # Check if category already exists
                    cursor.execute("SELECT id FROM service_category WHERE name = ?", (name,))
                    existing = cursor.fetchone()
                    
                    if not existing:
                        cursor.execute("""
                            INSERT INTO service_category 
                            (name, description, sort_order, is_emergency, requires_admin_approval)
                            VALUES (?, ?, ?, ?, ?)
                        """, (name, description, sort_order, is_emergency, requires_admin_approval))
                        
                        created_categories[name] = cursor.lastrowid
                        self.log(f"   Created category: {name}")
                    else:
                        created_categories[name] = existing[0]
                        self.log(f"   Category exists: {name}")
                
                connection.commit()
                
            except Exception as e:
                connection.rollback()
                raise e
            finally:
                cursor.close()
                connection.close()
            
        self.log("✅ Default categories created")
        return created_categories
    
    def migrate_services(self, category_mapping):
        """Migrate existing services with new fields"""
        self.log("🔄 Migrating existing services...")
        
        with self.app.app_context():
            connection = db.engine.raw_connection()
            cursor = connection.cursor()
            
            try:
                # Get all services
                cursor.execute("SELECT id, issue_type, device_type, base_price FROM service")
                services = cursor.fetchall()
                
                for service_id, issue_type, device_type, base_price in services:
                    # Assign category based on device type and issue type
                    if issue_type in ['Screen', 'Battery'] and device_type == 'iPhone':
                        category_name = 'Emergency Repairs'
                    elif issue_type in ['Water Damage', 'Charging Port']:
                        category_name = 'Standard Repairs'
                    elif issue_type in ['Camera', 'Speaker']:
                        category_name = 'Premium Services'
                    else:
                        category_name = 'Standard Repairs'
                    
                    category_id = category_mapping.get(category_name)
                    
                    # Break down pricing into labor and parts
                    if base_price <= 50:
                        labor_cost = base_price * 0.3
                        parts_cost = base_price * 0.7
                    elif base_price <= 100:
                        labor_cost = base_price * 0.4
                        parts_cost = base_price * 0.6
                    else:
                        labor_cost = base_price * 0.5
                        parts_cost = base_price * 0.5
                    
                    # Set multi-service settings
                    is_emergency = 1 if category_name == 'Emergency Repairs' else 0
                    max_quantity = 2 if issue_type in ['Screen', 'Battery'] else 1
                    
                    # Update service with new fields
                    cursor.execute("""
                        UPDATE service 
                        SET category_id = ?, labor_cost = ?, parts_cost = ?, 
                            is_emergency = ?, allows_multiple = 1, max_quantity = ?,
                            last_price_update = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (category_id, labor_cost, parts_cost, is_emergency, max_quantity, service_id))
                    
                    self.log(f"   Migrated service ID {service_id} -> {category_name}")
                
                connection.commit()
                
            except Exception as e:
                connection.rollback()
                raise e
            finally:
                cursor.close()
                connection.close()
            
        self.log(f"✅ Migrated {len(services)} services")
    
    def migrate_bookings(self):
        """Migrate existing bookings to use BookingService junction table"""
        self.log("🔄 Migrating existing bookings...")
        
        with self.app.app_context():
            connection = db.engine.raw_connection()
            cursor = connection.cursor()
            
            try:
                # Get bookings with service_id
                cursor.execute("""
                    SELECT b.id, b.service_id, s.base_price, s.labor_cost, s.parts_cost, s.estimated_time
                    FROM booking b 
                    JOIN service s ON b.service_id = s.id 
                    WHERE b.service_id IS NOT NULL
                """)
                bookings = cursor.fetchall()
                
                migrated_count = 0
                
                for booking_id, service_id, base_price, labor_cost, parts_cost, estimated_time in bookings:
                    # Check if BookingService already exists
                    cursor.execute("""
                        SELECT id FROM booking_service 
                        WHERE booking_id = ? AND service_id = ?
                    """, (booking_id, service_id))
                    existing_bs = cursor.fetchone()
                    
                    if not existing_bs:
                        # Create BookingService entry
                        cursor.execute("""
                            INSERT INTO booking_service 
                            (booking_id, service_id, quantity, price_snapshot, labor_cost, parts_cost, estimated_time)
                            VALUES (?, ?, 1, ?, ?, ?, ?)
                        """, (booking_id, service_id, base_price, labor_cost or 0, parts_cost or 0, estimated_time))
                        
                        # Update booking totals
                        cursor.execute("""
                            UPDATE booking 
                            SET total_services_count = 1, combined_estimated_duration = ?
                            WHERE id = ?
                        """, (estimated_time, booking_id))
                        
                        migrated_count += 1
                        self.log(f"   Migrated booking #{booking_id} -> Service ID: {service_id}")
                
                connection.commit()
                
            except Exception as e:
                connection.rollback()
                raise e
            finally:
                cursor.close()
                connection.close()
            
        self.log(f"✅ Migrated {migrated_count} bookings")
    
    def validate_migration(self):
        """Validate that migration was successful"""
        self.log("🔄 Validating migration...")
        
        with self.app.app_context():
            connection = db.engine.raw_connection()
            cursor = connection.cursor()
            
            try:
                # Validate categories
                cursor.execute("SELECT COUNT(*) FROM service_category")
                categories_count = cursor.fetchone()[0]
                self.log(f"   Service categories: {categories_count}")
                
                # Validate services
                cursor.execute("SELECT COUNT(*) FROM service")
                services_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM service WHERE category_id IS NOT NULL")
                services_with_categories = cursor.fetchone()[0]
                self.log(f"   Services: {services_count} total, {services_with_categories} with categories")
                
                # Validate bookings
                cursor.execute("SELECT COUNT(*) FROM booking")
                bookings_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM booking_service")
                booking_services_count = cursor.fetchone()[0]
                self.log(f"   Bookings: {bookings_count} total, {booking_services_count} booking-service relationships")
                
                # Validate pricing
                cursor.execute("SELECT COUNT(*) FROM service WHERE labor_cost IS NOT NULL AND parts_cost IS NOT NULL")
                services_with_pricing = cursor.fetchone()[0]
                self.log(f"   Services with enhanced pricing: {services_with_pricing}")
                
                # Check for inconsistencies
                issues = []
                
                # Check bookings without BookingService entries
                cursor.execute("""
                    SELECT COUNT(*) FROM booking b 
                    LEFT JOIN booking_service bs ON b.id = bs.booking_id 
                    WHERE bs.booking_id IS NULL AND b.service_id IS NOT NULL
                """)
                orphaned_bookings = cursor.fetchone()[0]
                
                if orphaned_bookings > 0:
                    issues.append(f"{orphaned_bookings} bookings without BookingService entries")
                
                # Check services without categories
                cursor.execute("SELECT COUNT(*) FROM service WHERE category_id IS NULL")
                uncategorized_services = cursor.fetchone()[0]
                if uncategorized_services > 0:
                    issues.append(f"{uncategorized_services} services without categories")
                
                if issues:
                    self.log("⚠️  Migration issues found:")
                    for issue in issues:
                        self.log(f"   - {issue}")
                    return False
                else:
                    self.log("✅ Migration validation passed")
                    return True
                    
            finally:
                cursor.close()
                connection.close()
    
    def run_migration(self):
        """Run the complete migration process"""
        self.log("🚀 Starting Multi-Service Booking System Migration")
        self.log("=" * 60)
        
        try:
            # Step 1: Backup existing data
            backup_file = self.backup_existing_data()
            
            # Step 2: Create new database tables and columns
            self.create_new_tables()
            
            # Step 3: Create default categories
            category_mapping = self.create_default_categories()
            
            # Step 4: Migrate existing services
            self.migrate_services(category_mapping)
            
            # Step 5: Migrate existing bookings
            self.migrate_bookings()
            
            # Step 6: Validate migration
            if self.validate_migration():
                self.log("=" * 60)
                self.log("🎉 Migration completed successfully!")
                self.log(f"📁 Backup saved to: {backup_file}")
                self.log("")
                self.log("🔄 Next steps:")
                self.log("   1. Test the application functionality")
                self.log("   2. Update booking wizard for multi-service selection")
                self.log("   3. Implement admin price management interface")
                self.log("")
                return True
            else:
                self.log("❌ Migration validation failed")
                return False
                
        except Exception as e:
            self.log(f"❌ Migration failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Main migration execution"""
    print("Multi-Service Booking System Migration")
    print("=====================================")
    print()
    
    response = input("This will modify your database. Continue? (y/N): ")
    if response.lower() != 'y':
        print("Migration cancelled.")
        return
    
    migration = MultiServiceMigration()
    success = migration.run_migration()
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("The application now supports multi-service bookings and admin price management.")
    else:
        print("\n❌ Migration failed!")
        print("Please check the error messages above and try again.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 