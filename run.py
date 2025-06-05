#!/usr/bin/env python3
"""
Flask Mobile Repair Service Application
Development Server Entry Point
"""

import os
from app import create_app, db
from app.models.user import User
from app.models.service import Service
from app.models.booking import Booking
from app.models.service_area import ServiceZipCode

# Create Flask application
app = create_app(os.getenv('FLASK_CONFIG') or 'development')

@app.shell_context_processor
def make_shell_context():
    """Make database models available in flask shell"""
    return {
        'db': db,
        'User': User,
        'Service': Service,
        'Booking': Booking,
        'ServiceZipCode': ServiceZipCode
    }

@app.cli.command()
def init_db():
    """Initialize the database with tables"""
    print("Creating database tables...")
    db.create_all()
    print("Database tables created successfully!")

@app.cli.command()
def seed_db():
    """Seed the database with sample data"""
    print("Seeding database with sample data...")
    
    # Create admin user
    admin = User(
        email='admin@repair.local',
        first_name='Admin',
        last_name='User',
        phone='555-123-4567',
        is_admin=True
    )
    admin.set_password('admin123')
    db.session.add(admin)
    
    # Create sample customer
    customer = User(
        email='customer@example.com',
        first_name='John',
        last_name='Doe',
        phone='555-987-6543',
        address='123 Main St',
        city='Orland Park',
        state='IL',
        zip_code='60462'
    )
    customer.set_password('customer123')
    db.session.add(customer)
    
    # Create sample services
    services_data = [
        # iPhone Services
        {'name': 'Screen Replacement', 'device_type': 'iPhone', 'issue_type': 'Screen', 'base_price': 150.0, 'is_featured': True},
        {'name': 'Battery Replacement', 'device_type': 'iPhone', 'issue_type': 'Battery', 'base_price': 80.0, 'is_featured': True},
        {'name': 'Water Damage Repair', 'device_type': 'iPhone', 'issue_type': 'Water Damage', 'base_price': 120.0},
        
        # Samsung Services
        {'name': 'Screen Replacement', 'device_type': 'Samsung', 'issue_type': 'Screen', 'base_price': 140.0, 'is_featured': True},
        {'name': 'Battery Replacement', 'device_type': 'Samsung', 'issue_type': 'Battery', 'base_price': 75.0, 'is_featured': True},
        {'name': 'Charging Port Repair', 'device_type': 'Samsung', 'issue_type': 'Charging Port', 'base_price': 90.0},
        
        # Other Device Services
        {'name': 'Screen Replacement', 'device_type': 'Other', 'issue_type': 'Screen', 'base_price': 100.0, 'is_featured': True},
        {'name': 'Battery Replacement', 'device_type': 'Other', 'issue_type': 'Battery', 'base_price': 70.0},
        {'name': 'Software Issues', 'device_type': 'Other', 'issue_type': 'Software', 'base_price': 50.0},
    ]
    
    for service_data in services_data:
        service = Service(**service_data)
        db.session.add(service)
    
    # Clear existing service area data
    ServiceZipCode.query.delete()
    db.session.commit()
    
    # Create sample service area ZIP codes
    zip_codes_data = [
        # CORE SERVICE AREA (0-5 miles) - FULL COVERAGE
        {'zip_code': '60462', 'city': 'Orland Park', 'distance_miles': 0.0, 'coverage_level': 'full'},  # Business HQ
        {'zip_code': '60467', 'city': 'Orland Park', 'distance_miles': 2.0, 'coverage_level': 'full'},
        {'zip_code': '60477', 'city': 'Tinley Park', 'distance_miles': 3.5, 'coverage_level': 'full'},
        {'zip_code': '60487', 'city': 'Tinley Park', 'distance_miles': 4.0, 'coverage_level': 'full'},
        {'zip_code': '60445', 'city': 'Midlothian', 'distance_miles': 4.5, 'coverage_level': 'full'},
        {'zip_code': '60463', 'city': 'Palos Heights', 'distance_miles': 3.0, 'coverage_level': 'full'},
        {'zip_code': '60464', 'city': 'Palos Park', 'distance_miles': 4.5, 'coverage_level': 'full'},
        {'zip_code': '60465', 'city': 'Palos Hills', 'distance_miles': 4.0, 'coverage_level': 'full'},
        
        # PRIMARY SERVICE AREA (5-8 miles) - FULL COVERAGE
        {'zip_code': '60448', 'city': 'Mokena', 'distance_miles': 8.0, 'coverage_level': 'full'},
        {'zip_code': '60452', 'city': 'Oak Forest', 'distance_miles': 6.0, 'coverage_level': 'full'},
        {'zip_code': '60457', 'city': 'Hickory Hills', 'distance_miles': 5.5, 'coverage_level': 'full'},
        {'zip_code': '60482', 'city': 'Worth', 'distance_miles': 7.0, 'coverage_level': 'full'},
        {'zip_code': '60415', 'city': 'Chicago Ridge', 'distance_miles': 6.5, 'coverage_level': 'full'},
        {'zip_code': '60453', 'city': 'Oak Lawn', 'distance_miles': 7.5, 'coverage_level': 'full'},
        {'zip_code': '60478', 'city': 'Country Club Hills', 'distance_miles': 7.0, 'coverage_level': 'full'},
        {'zip_code': '60455', 'city': 'Bridgeview', 'distance_miles': 8.0, 'coverage_level': 'full'},
        {'zip_code': '60458', 'city': 'Justice', 'distance_miles': 7.5, 'coverage_level': 'full'},
        
        # EXTENDED SERVICE AREA (8-12 miles) - PARTIAL COVERAGE
        {'zip_code': '60439', 'city': 'Lemont', 'distance_miles': 9.0, 'coverage_level': 'partial'},
        {'zip_code': '60491', 'city': 'Homer Glen', 'distance_miles': 10.0, 'coverage_level': 'partial'},
        {'zip_code': '60456', 'city': 'Hometown', 'distance_miles': 9.5, 'coverage_level': 'partial'},
        {'zip_code': '60480', 'city': 'Willow Springs', 'distance_miles': 8.5, 'coverage_level': 'partial'},
        {'zip_code': '60426', 'city': 'Harvey', 'distance_miles': 11.0, 'coverage_level': 'partial'},
        {'zip_code': '60429', 'city': 'Hazel Crest', 'distance_miles': 10.5, 'coverage_level': 'partial'},
        {'zip_code': '60406', 'city': 'Blue Island', 'distance_miles': 11.5, 'coverage_level': 'partial'},
        {'zip_code': '60473', 'city': 'South Holland', 'distance_miles': 12.0, 'coverage_level': 'partial'},
        {'zip_code': '60469', 'city': 'Posen', 'distance_miles': 10.0, 'coverage_level': 'partial'},
        
        # OUTER SERVICE AREA (12+ miles) - EDGE COVERAGE
        {'zip_code': '60501', 'city': 'Summit Argo', 'distance_miles': 13.0, 'coverage_level': 'edge', 'requires_confirmation': True},
        {'zip_code': '60525', 'city': 'La Grange', 'distance_miles': 12.5, 'coverage_level': 'edge', 'requires_confirmation': True},
        {'zip_code': '60526', 'city': 'La Grange Park', 'distance_miles': 13.0, 'coverage_level': 'edge', 'requires_confirmation': True},
        {'zip_code': '60534', 'city': 'Lyons', 'distance_miles': 12.5, 'coverage_level': 'edge', 'requires_confirmation': True},
        {'zip_code': '60546', 'city': 'Riverside', 'distance_miles': 14.0, 'coverage_level': 'edge', 'requires_confirmation': True},
        {'zip_code': '60558', 'city': 'Western Springs', 'distance_miles': 13.5, 'coverage_level': 'edge', 'requires_confirmation': True},
        {'zip_code': '60559', 'city': 'Westmont', 'distance_miles': 15.0, 'coverage_level': 'edge', 'requires_confirmation': True},
        {'zip_code': '60561', 'city': 'Darien', 'distance_miles': 14.5, 'coverage_level': 'edge', 'requires_confirmation': True},
        {'zip_code': '60514', 'city': 'Clarendon Hills', 'distance_miles': 16.0, 'coverage_level': 'edge', 'requires_confirmation': True},
        {'zip_code': '60521', 'city': 'Hinsdale', 'distance_miles': 15.5, 'coverage_level': 'edge', 'requires_confirmation': True},
    ]
    
    for zip_data in zip_codes_data:
        zip_code = ServiceZipCode(**zip_data)
        db.session.add(zip_code)
    
    db.session.commit()
    print("Database seeded successfully!")
    print("\nSample accounts:")
    print("Admin: admin@repair.local / admin123")
    print("Customer: customer@example.com / customer123")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 