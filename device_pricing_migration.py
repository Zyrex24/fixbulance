#!/usr/bin/env python3
"""
Device Pricing Migration Script for Fixbulance

This script populates the database with comprehensive iPhone and Samsung device pricing
data including original and after-market parts for various repair services.

Run with: python device_pricing_migration.py
"""

import sys
import os
from datetime import datetime

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main migration function"""
    print("🚀 Starting Device Pricing Migration for Fixbulance")
    print("=" * 60)
    
    try:
        # Import after path setup
        from app import create_app, db
        from app.models.device_pricing import DevicePricing, WaterDamageService, LaptopTabletService
        
        # Create Flask app context
        app = create_app()
        
        with app.app_context():
            # Create tables first
            db.create_all()
            print("✅ Database tables created/verified")
            
            # iPhone pricing data based on user's comprehensive table
            iphone_data = [
                # Model, orig_screen, orig_battery, afm_screen, afm_battery, charger_port, speaker, camera_lens, vibrator, orig_bg, afm_bg, charger_port_orig
                ('XR', None, None, 100, 70, 80, 50, 40, 60, None, 120, None),
                ('X', None, None, 110, 70, 80, 50, 40, 60, None, 120, None),
                ('XS', None, None, 110, 70, 80, 50, 40, 60, None, 120, None),
                ('XS Max', 190, 90, 110, 70, 80, 50, 40, 60, None, 120, None),
                ('11', None, None, 100, 70, 80, 50, 40, 60, None, 120, None),
                ('11 Pro', None, None, 130, 70, 80, 50, 40, 60, None, 120, None),
                ('11 Pro Max', None, None, 110, 70, 80, 50, 40, 60, None, 120, None),
                ('SE 2020', None, None, 100, 70, 80, 50, 40, 60, None, 120, None),
                ('12 Mini', 260, 90, 110, 70, 80, 80, 40, 60, None, 120, None),
                ('12', 300, 90, 130, 70, 80, 60, 40, 60, None, 120, None),
                ('12 Pro', 320, 90, 130, 70, 80, 60, 40, 60, None, 120, None),
                ('12 Pro Max', 320, 90, 130, 70, 80, 50, 40, 60, None, 120, None),
                ('SE 2022', None, None, 100, 70, 80, 50, 40, 60, None, 120, None),
                ('13 Mini', 270, 90, 150, 70, 80, 50, 40, 60, None, 120, None),
                ('13', 300, 90, 120, 70, 80, 50, 40, 60, None, 120, None),
                ('13 Pro', 300, 90, 150, 80, 80, 50, 40, 60, None, 120, None),
                ('13 Pro Max', 340, 90, 140, 80, 80, 50, 40, 60, None, 120, None),
                ('14', 300, 100, 140, 80, 80, 50, 40, 60, 200, 100, None),
                ('14 Plus', 320, 100, 150, 80, 80, 50, 40, 60, 220, 120, None),
                ('14 Pro', 320, 100, 180, 80, 80, 50, 40, 60, 220, 120, None),
                ('14 Pro Max', 390, 100, 180, 80, 80, 50, 40, 60, None, 120, None),
                ('15', 320, 100, 140, 80, 80, 50, 40, 60, 200, 120, None),
                ('15 Plus', 350, 110, 180, 90, 80, 50, 40, 60, 220, 120, None),
                ('15 Pro', 360, 110, 190, 80, 80, 50, 40, 60, 220, 120, None),
                ('15 Pro Max', 400, 110, 200, 80, 80, 50, 40, 60, 250, 120, None),
                ('16', 340, 120, 190, 80, 120, 50, 40, 60, 210, 120, 180),
                ('16 Plus', 390, 100, 190, 80, 110, 50, 40, 60, 220, 120, None),
                ('16 Pro', 420, 120, 300, 90, 120, 50, 40, 60, 230, 120, 180),
                ('16 Pro Max', 450, 120, 340, 90, 120, 50, 40, 60, 250, 120, 180),
                ('16 E', 310, 110, 140, None, 120, 50, 40, 60, 220, 120, 180),
            ]
            
            print("Populating iPhone pricing data...")
            for data in iphone_data:
                model, orig_screen, orig_battery, afm_screen, afm_battery, charger_port, speaker, camera_lens, vibrator, orig_bg, afm_bg, charger_port_orig = data
                
                # Check if device already exists
                existing = DevicePricing.query.filter_by(brand='iPhone', model=model).first()
                if existing:
                    print(f"   iPhone {model} already exists, skipping...")
                    continue
                
                device = DevicePricing(
                    brand='iPhone',
                    model=model,
                    model_display=f'iPhone {model}',
                    original_screen=orig_screen,
                    original_battery=orig_battery,
                    afm_screen=afm_screen,
                    afm_battery=afm_battery,
                    charger_port=charger_port,
                    speaker=speaker,
                    camera_lens=camera_lens,
                    vibrator=vibrator,
                    original_back_glass=orig_bg,
                    afm_back_glass=afm_bg,
                    charger_port_original=charger_port_orig
                )
                
                db.session.add(device)
                print(f"   ✅ Added iPhone {model}")
            
            # Samsung pricing data based on user's comprehensive table
            samsung_data = [
                # Model, orig_screen, orig_battery, orig_bg, afm_screen, afm_battery, afm_bg, charger_port, is_refurb
                ('S20', 260, 80, 100, 160, 60, 80, 60, False),
                ('S20 Plus', 260, 80, 110, None, 60, 80, 60, False),
                ('S20 Ultra', 280, 100, 110, 170, 60, 80, 60, False),
                ('S20 FE', 170, 90, 100, 120, 60, 80, None, False),
                ('S21', 200, 100, 100, 120, 60, 80, None, False),
                ('S21 Plus', 220, 100, 110, 140, 70, 80, None, False),
                ('S21 Ultra', 280, 110, 110, 160, 70, 80, None, False),
                ('S21 FE', 200, 110, 90, None, 70, None, 70, False),
                ('S22', 220, 110, 110, None, 70, 80, 60, False),
                ('S22 Plus', 220, 110, 110, 150, 80, 80, None, False),
                ('S22 Ultra', 290, 110, 120, 160, 80, 80, None, False),
                ('S23', 220, 110, 120, None, 80, 80, 70, False),
                ('S23 Plus', 220, 110, 120, 150, 80, 80, 70, False),
                ('S23 Ultra', 280, 110, 130, 170, 80, 80, 70, False),
                ('S23 FE', 190, None, 110, None, 70, 80, 80, False),
                ('S24', 210, None, 120, None, 80, 80, 80, False),
                ('S24 Plus', 240, 120, 120, None, 80, 80, 80, False),
                ('S24 Ultra', 290, None, 120, 220, 80, 80, 80, False),
                ('S24 FE', None, None, None, None, 80, None, 80, True),
                ('S25', None, None, None, None, None, None, 80, True),
                ('S25 Plus', 260, None, 140, None, None, None, 90, False),
                ('S25 Ultra', 340, None, 150, None, None, None, 90, False),
                ('Note 20', 250, 110, 100, None, 80, 80, 80, False),
                ('Note 20 Ultra', 280, 110, 130, 180, 80, 80, 80, False),
                ('A31', 140, 100, 90, 100, 80, 70, 70, False),
                ('A51', 170, None, 90, 120, 80, None, 70, False),
                ('A71', 180, 110, 80, None, 80, None, 80, False),
                ('A32', 130, 100, 100, 100, 80, 70, 70, False),
                ('A52', 150, None, 100, 120, 80, 70, 70, False),
                ('A72', 170, None, 110, None, 80, None, 80, False),
                ('A33', 150, 110, 110, 110, 80, None, 80, False),
                ('A53', 170, 110, 100, 120, 80, 80, 80, False),
                ('A73', 170, None, None, None, 80, None, 80, False),
                ('A34', 160, 110, 100, None, 80, None, 80, False),
                ('A54', 160, 110, 100, 120, 80, 80, 80, False),
                ('A35', None, None, None, None, 80, None, 70, True),
                ('A55', None, None, None, None, 80, 80, 80, True),
                ('A36', None, None, None, None, None, None, 80, True),
                ('A56', None, None, None, None, None, None, 80, True),
            ]
            
            print("Populating Samsung pricing data...")
            for data in samsung_data:
                model, orig_screen, orig_battery, orig_bg, afm_screen, afm_battery, afm_bg, charger_port, is_refurb = data
                
                # Check if device already exists
                existing = DevicePricing.query.filter_by(brand='Samsung', model=model).first()
                if existing:
                    print(f"   Samsung {model} already exists, skipping...")
                    continue
                
                device = DevicePricing(
                    brand='Samsung',
                    model=model,
                    model_display=f'Samsung Galaxy {model}',
                    original_screen=orig_screen,
                    original_battery=orig_battery,
                    original_back_glass=orig_bg,
                    afm_screen=afm_screen,
                    afm_battery=afm_battery,
                    afm_back_glass=afm_bg,
                    charger_port=charger_port,
                    speaker=50.0,  # Standard for Samsung
                    camera_lens=40.0,  # Standard for Samsung
                    vibrator=60.0,  # Standard for Samsung
                    is_refurbished_only=is_refurb,
                    notes="REFURB ONLY" if is_refurb else None
                )
                
                db.session.add(device)
                print(f"   ✅ Added Samsung {model}{' (REFURB ONLY)' if is_refurb else ''}")
            
            # Water damage service
            print("Populating water damage service...")
            existing_water = WaterDamageService.query.first()
            if not existing_water:
                water_service = WaterDamageService(
                    diagnostic_fee=55.00,
                    is_diagnostic_refundable=False,
                    name="Water Damage Diagnostic & Repair",
                    description="Replace Water Damaged device with diagnostic fee of $55 non-refundable, that goes towards the repair if the phone needs something to be replaced - it can be deducted from repair cost (diagnostic fee + deposit = total repair cost)"
                )
                db.session.add(water_service)
                print("   ✅ Added water damage service configuration")
            else:
                print("   Water damage service already exists, skipping...")
            
            # Laptop and tablet services
            print("Populating laptop and tablet services...")
            laptop_tablet_services = [
                ('Laptop', 'Screen Repair'),
                ('Laptop', 'Battery Replacement'),
                ('Laptop', 'Keyboard Repair'),
                ('Laptop', 'Charging Port Repair'),
                ('iPad', 'Screen Repair'),
                ('iPad', 'Battery Replacement'),
                ('iPad', 'Charging Port Repair'),
                ('Tablet', 'Screen Repair'),
                ('Tablet', 'Battery Replacement'),
            ]
            
            for device_type, service_type in laptop_tablet_services:
                existing_service = LaptopTabletService.query.filter_by(
                    device_type=device_type, 
                    service_type=service_type
                ).first()
                if existing_service:
                    print(f"   {device_type} {service_type} already exists, skipping...")
                    continue
                
                service = LaptopTabletService(
                    device_type=device_type,
                    service_type=service_type,
                    requires_quote=True,
                    requires_dropoff=True,
                    typical_turnaround="Same day",
                    quote_email="info@fixbulance.com"
                )
                
                db.session.add(service)
                print(f"   ✅ Added {device_type} {service_type}")
            
            # Commit all changes
            db.session.commit()
            
            print("=" * 60)
            print("✅ Device Pricing Migration completed successfully!")
            print(f"📱 iPhone models: {DevicePricing.query.filter_by(brand='iPhone').count()}")
            print(f"📱 Samsung models: {DevicePricing.query.filter_by(brand='Samsung').count()}")
            print(f"💧 Water damage services: {WaterDamageService.query.count()}")
            print(f"💻 Laptop/Tablet services: {LaptopTabletService.query.count()}")
            
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 