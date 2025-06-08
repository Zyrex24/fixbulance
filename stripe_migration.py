#!/usr/bin/env python3
"""
Stripe Integration Database Migration Script
Adds Payment model table and stripe_customer_id to User model
"""

import sqlite3
import os
from datetime import datetime

def run_migration():
    """Run the Stripe integration database migration"""
    
    # Database path
    db_path = os.path.join('instance', 'repair_service_dev.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        print("Please run the Flask application first to create the database.")
        return False
    
    print("🔧 Starting Stripe Integration Database Migration...")
    print(f"📁 Database: {db_path}")
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if Payment table already exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='payment'
        """)
        
        if cursor.fetchone():
            print("⚠️  Payment table already exists. Skipping table creation.")
        else:
            # Create Payment table
            print("📊 Creating Payment table...")
            cursor.execute("""
                CREATE TABLE payment (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    booking_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    stripe_payment_intent_id VARCHAR(255) UNIQUE,
                    stripe_charge_id VARCHAR(255),
                    stripe_customer_id VARCHAR(255),
                    amount DECIMAL(10, 2) NOT NULL,
                    currency VARCHAR(3) DEFAULT 'usd' NOT NULL,
                    payment_type VARCHAR(20) NOT NULL,
                    status VARCHAR(50) DEFAULT 'pending',
                    payment_method_type VARCHAR(50),
                    card_brand VARCHAR(20),
                    card_last4 VARCHAR(4),
                    description VARCHAR(255),
                    receipt_email VARCHAR(255),
                    receipt_url VARCHAR(500),
                    device_type VARCHAR(50),
                    service_name VARCHAR(100),
                    customer_name VARCHAR(100),
                    customer_phone VARCHAR(20),
                    error_code VARCHAR(100),
                    error_message TEXT,
                    failure_reason VARCHAR(255),
                    refunded_amount DECIMAL(10, 2) DEFAULT 0.00,
                    refund_reason VARCHAR(255),
                    refunded_at DATETIME,
                    refunded_by INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    processed_at DATETIME,
                    FOREIGN KEY (booking_id) REFERENCES booking (id),
                    FOREIGN KEY (user_id) REFERENCES user (id),
                    FOREIGN KEY (refunded_by) REFERENCES user (id)
                )
            """)
            
            # Create indexes for Payment table
            cursor.execute("CREATE INDEX ix_payment_stripe_payment_intent_id ON payment (stripe_payment_intent_id)")
            cursor.execute("CREATE INDEX ix_payment_stripe_charge_id ON payment (stripe_charge_id)")
            cursor.execute("CREATE INDEX ix_payment_stripe_customer_id ON payment (stripe_customer_id)")
            cursor.execute("CREATE INDEX ix_payment_status ON payment (status)")
            cursor.execute("CREATE INDEX ix_payment_created_at ON payment (created_at)")
            
            print("✅ Payment table created successfully")
        
        # Check if stripe_customer_id column exists in User table
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'stripe_customer_id' in columns:
            print("⚠️  stripe_customer_id column already exists in User table. Skipping column addition.")
        else:
            # Add stripe_customer_id column to User table
            print("👤 Adding stripe_customer_id column to User table...")
            cursor.execute("ALTER TABLE user ADD COLUMN stripe_customer_id VARCHAR(255)")
            cursor.execute("CREATE UNIQUE INDEX ix_user_stripe_customer_id ON user (stripe_customer_id)")
            print("✅ stripe_customer_id column added to User table")
        
        # Commit changes
        conn.commit()
        print("💾 Database migration completed successfully!")
        
        # Display migration summary
        print("\n📋 Migration Summary:")
        print("✅ Payment table created (if not exists)")
        print("✅ Payment table indexes created")
        print("✅ stripe_customer_id column added to User table (if not exists)")
        print("✅ stripe_customer_id index created")
        
        print("\n🎯 Next Steps:")
        print("1. Set up Stripe API keys in environment variables:")
        print("   - STRIPE_PUBLISHABLE_KEY=pk_test_...")
        print("   - STRIPE_SECRET_KEY=sk_test_...")
        print("   - STRIPE_WEBHOOK_SECRET=whsec_...")
        print("2. Test payment functionality with Stripe test cards")
        print("3. Configure webhook endpoint in Stripe dashboard")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

def verify_migration():
    """Verify the migration was successful"""
    db_path = os.path.join('instance', 'repair_service_dev.db')
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n🔍 Verifying migration...")
        
        # Check Payment table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='payment'")
        if cursor.fetchone():
            print("✅ Payment table exists")
            
            # Count payment records
            cursor.execute("SELECT COUNT(*) FROM payment")
            count = cursor.fetchone()[0]
            print(f"📊 Payment records: {count}")
        else:
            print("❌ Payment table not found")
        
        # Check User table stripe_customer_id column
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'stripe_customer_id' in columns:
            print("✅ stripe_customer_id column exists in User table")
        else:
            print("❌ stripe_customer_id column not found in User table")
        
        print("✅ Migration verification completed")
        
    except Exception as e:
        print(f"❌ Verification failed: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Fixbulance Stripe Integration Migration")
    print("=" * 50)
    
    success = run_migration()
    
    if success:
        verify_migration()
        print("\n🎉 Migration completed successfully!")
        print("\n💡 You can now use Stripe payment processing in your Fixbulance application!")
    else:
        print("\n❌ Migration failed. Please check the errors above.") 