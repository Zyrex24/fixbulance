#!/usr/bin/env python3
"""
Simple Database Viewer for Fixbulance
View database contents without external dependencies
"""

import sqlite3
import os

def view_database():
    """View all tables and data in the database"""
    db_path = os.path.join('instance', 'repair_service_dev.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        return
    
    print(f"📊 FIXBULANCE DATABASE VIEWER")
    print(f"Database: {db_path}")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"\n📋 TABLES FOUND: {len(tables)}")
        for table in tables:
            print(f"  • {table[0]}")
        
        # View each table's data
        for table_name in [t[0] for t in tables]:
            print(f"\n" + "="*60)
            print(f"📊 TABLE: {table_name.upper()}")
            print("="*60)
            
            # Get column names
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            print(f"Columns: {', '.join(columns)}")
            
            # Get data
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            
            if rows:
                print(f"📈 Records: {len(rows)}")
                for i, row in enumerate(rows, 1):
                    print(f"\nRecord {i}:")
                    for col, val in zip(columns, row):
                        print(f"  {col}: {val}")
            else:
                print("📭 No data found")
        
        conn.close()
        print(f"\n✅ Database viewing completed!")
        
    except Exception as e:
        print(f"❌ Error accessing database: {e}")

if __name__ == "__main__":
    view_database() 