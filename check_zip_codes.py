#!/usr/bin/env python3
"""Check and populate ServiceZipCode records for testing"""

# Import from the main app.py file, not the app package
import app
from app.models.service_area import ServiceZipCode
from datetime import datetime

def check_and_populate_zip_codes():
    """Check ServiceZipCode table and populate if empty"""
    with app.app.app_context():
        # Check current count
        current_count = ServiceZipCode.query.count()
        print(f"Current ServiceZipCode records: {current_count}")
        
        if current_count == 0:
            print("No ZIP codes found. Adding sample data...")
            
            # Sample ZIP codes for Orland Park area (southwest Chicago suburbs)
            sample_zip_codes = [
                # Core Orland Park area (closest)
                {'zip_code': '60462', 'city': 'Orland Park', 'distance_miles': 0.0, 'coverage_level': 'full'},
                {'zip_code': '60467', 'city': 'Orland Park', 'distance_miles': 1.5, 'coverage_level': 'full'},
                
                # Immediate surrounding areas (within 5 miles)
                {'zip_code': '60477', 'city': 'Tinley Park', 'distance_miles': 3.2, 'coverage_level': 'full'},
                {'zip_code': '60452', 'city': 'Oak Forest', 'distance_miles': 4.1, 'coverage_level': 'full'},
                {'zip_code': '60463', 'city': 'Palos Heights', 'distance_miles': 4.8, 'coverage_level': 'full'},
                
                # Extended coverage (5-8 miles)
                {'zip_code': '60448', 'city': 'Mokena', 'distance_miles': 6.2, 'coverage_level': 'full'},
                {'zip_code': '60455', 'city': 'Bridgeview', 'distance_miles': 7.1, 'coverage_level': 'full'},
                {'zip_code': '60803', 'city': 'Alsip', 'distance_miles': 7.8, 'coverage_level': 'full'},
                
                # Edge coverage (8-10 miles)
                {'zip_code': '60445', 'city': 'Frankfort', 'distance_miles': 8.5, 'coverage_level': 'partial'},
                {'zip_code': '60464', 'city': 'Palos Park', 'distance_miles': 9.1, 'coverage_level': 'partial'},
                {'zip_code': '60525', 'city': 'La Grange', 'distance_miles': 9.7, 'coverage_level': 'partial'},
                
                # Test ZIP codes for debugging
                {'zip_code': '12345', 'city': 'Test City', 'distance_miles': 2.0, 'coverage_level': 'full'},
                {'zip_code': '54321', 'city': 'Demo Town', 'distance_miles': 5.0, 'coverage_level': 'full'},
            ]
            
            for zip_data in sample_zip_codes:
                zip_record = ServiceZipCode(
                    zip_code=zip_data['zip_code'],
                    city=zip_data['city'],
                    state='IL',
                    distance_miles=zip_data['distance_miles'],
                    coverage_level=zip_data['coverage_level'],
                    is_active=True,
                    last_validated=datetime.utcnow(),
                    validation_method='manual'
                )
                app.db.session.add(zip_record)
            
            try:
                app.db.session.commit()
                new_count = ServiceZipCode.query.count()
                print(f"✅ Successfully added {new_count} ServiceZipCode records")
                
                # Show some examples
                print("\nSample records:")
                for record in ServiceZipCode.query.limit(5).all():
                    print(f"  - {record.zip_code}: {record.city}, {record.state} ({record.distance_miles} miles, {record.coverage_level})")
                    
            except Exception as e:
                app.db.session.rollback()
                print(f"❌ Error adding ZIP codes: {e}")
        else:
            print("ZIP codes already exist:")
            for record in ServiceZipCode.query.limit(10).all():
                print(f"  - {record.zip_code}: {record.city}, {record.state} ({record.distance_miles} miles)")

if __name__ == '__main__':
    check_and_populate_zip_codes() 