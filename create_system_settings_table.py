#!/usr/bin/env python3
"""
Create system_settings table and initialize base deposit
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.system_settings import SystemSettings

def create_system_settings():
    """Create system_settings table and initialize settings"""
    app = create_app()
    
    with app.app_context():
        try:
            # Create the table
            db.create_all()
            print("✅ System settings table created successfully")
            
            # Initialize base deposit setting if it doesn't exist
            base_deposit = SystemSettings.get_setting('base_deposit_amount')
            if base_deposit is None:
                SystemSettings.set_setting(
                    'base_deposit_amount',
                    '15.00',
                    'float',
                    'Standard deposit amount for all bookings',
                    'payment'
                )
                print("✅ Base deposit setting initialized to $15.00")
            else:
                print(f"ℹ️ Base deposit setting already exists: ${base_deposit}")
            
            # Initialize other default settings
            settings_to_create = [
                ('company_name', 'Fixbulance LLC', 'string', 'Company name', 'general'),
                ('service_radius_miles', '10', 'int', 'Service radius in miles', 'service'),
                ('max_emergency_surcharge', '25.00', 'float', 'Maximum emergency service surcharge', 'payment'),
                ('warranty_days_default', '30', 'int', 'Default warranty period in days', 'service'),
                ('business_hours_start', '08:00', 'string', 'Business hours start time', 'schedule'),
                ('business_hours_end', '18:00', 'string', 'Business hours end time', 'schedule'),
            ]
            
            for key, value, setting_type, description, category in settings_to_create:
                existing = SystemSettings.get_setting(key)
                if existing is None:
                    SystemSettings.set_setting(key, value, setting_type, description, category)
                    print(f"✅ Created setting: {key} = {value}")
                else:
                    print(f"ℹ️ Setting already exists: {key} = {existing}")
            
            print("\n🎉 System settings initialization complete!")
            
        except Exception as e:
            print(f"❌ Error creating system settings: {e}")
            db.session.rollback()

if __name__ == '__main__':
    create_system_settings() 