from datetime import datetime
from app import db

class DevicePricing(db.Model):
    """Model for device-specific pricing including iPhone and Samsung pricing tables"""
    __tablename__ = 'device_pricing'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Device information
    brand = db.Column(db.String(50), nullable=False, index=True)  # iPhone, Samsung
    model = db.Column(db.String(100), nullable=False, index=True)  # iPhone 15 Pro, S24 Ultra, etc.
    model_display = db.Column(db.String(100))  # Human-readable model name
    
    # Part types and pricing
    original_screen = db.Column(db.Float, nullable=True)  # Original screen price
    original_battery = db.Column(db.Float, nullable=True)  # Original battery price
    original_back_glass = db.Column(db.Float, nullable=True)  # Original back glass
    
    afm_screen = db.Column(db.Float, nullable=True)  # After Market screen price
    afm_battery = db.Column(db.Float, nullable=True)  # After Market battery price
    afm_back_glass = db.Column(db.Float, nullable=True)  # After Market back glass
    
    charger_port = db.Column(db.Float, nullable=True)  # Charging port repair
    speaker = db.Column(db.Float, nullable=True)  # Speaker repair
    camera_lens = db.Column(db.Float, nullable=True)  # Camera lens repair (each)
    vibrator = db.Column(db.Float, nullable=True)  # Vibrator repair
    
    # Special pricing for newer models (iPhone 16 series)
    charger_port_original = db.Column(db.Float, nullable=True)  # Original charger port for newer models
    
    # Status and metadata
    is_active = db.Column(db.Boolean, default=True)
    is_refurbished_only = db.Column(db.Boolean, default=False)  # For refurb-only models
    notes = db.Column(db.Text)  # Special notes or conditions
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<DevicePricing {self.brand} {self.model}>'
    
    @property
    def display_name(self):
        """Get formatted display name"""
        return f"{self.brand} {self.model_display or self.model}"
    
    @classmethod
    def get_pricing_for_device(cls, brand, model):
        """Get pricing information for a specific device"""
        return cls.query.filter_by(brand=brand, model=model, is_active=True).first()
    
    @classmethod
    def get_all_iphone_models(cls):
        """Get all iPhone models with pricing"""
        return cls.query.filter_by(brand='iPhone', is_active=True).order_by(cls.model).all()
    
    @classmethod
    def get_all_samsung_models(cls):
        """Get all Samsung models with pricing"""
        return cls.query.filter_by(brand='Samsung', is_active=True).order_by(cls.model).all()
    
    def get_available_services(self):
        """Get list of available services with prices for this device"""
        services = []
        
        # Screen services
        if self.original_screen is not None:
            services.append({
                'type': 'screen_original',
                'name': 'Original Screen Replacement',
                'price': self.original_screen,
                'category': 'Screen'
            })
        
        if self.afm_screen is not None:
            services.append({
                'type': 'screen_afm',
                'name': 'After Market Screen Replacement',
                'price': self.afm_screen,
                'category': 'Screen'
            })
        
        # Battery services
        if self.original_battery is not None:
            services.append({
                'type': 'battery_original',
                'name': 'Original Battery Replacement',
                'price': self.original_battery,
                'category': 'Battery'
            })
        
        if self.afm_battery is not None:
            services.append({
                'type': 'battery_afm',
                'name': 'After Market Battery Replacement',
                'price': self.afm_battery,
                'category': 'Battery'
            })
        
        # Other services
        if self.charger_port is not None:
            services.append({
                'type': 'charger_port',
                'name': 'Charging Port Repair',
                'price': self.charger_port,
                'category': 'Charging Port'
            })
        
        if self.charger_port_original is not None:
            services.append({
                'type': 'charger_port_original',
                'name': 'Original Charging Port Repair',
                'price': self.charger_port_original,
                'category': 'Charging Port'
            })
        
        if self.speaker is not None:
            services.append({
                'type': 'speaker',
                'name': 'Speaker Repair',
                'price': self.speaker,
                'category': 'Speaker'
            })
        
        if self.camera_lens is not None:
            services.append({
                'type': 'camera_lens',
                'name': 'Camera Lens Replacement (each)',
                'price': self.camera_lens,
                'category': 'Camera'
            })
        
        if self.vibrator is not None:
            services.append({
                'type': 'vibrator',
                'name': 'Vibrator Repair',
                'price': self.vibrator,
                'category': 'Vibrator'
            })
        
        # Back Glass services
        if self.original_back_glass is not None:
            services.append({
                'type': 'back_glass_original',
                'name': 'Original Back Glass Replacement',
                'price': self.original_back_glass,
                'category': 'Back Glass'
            })
        
        if self.afm_back_glass is not None:
            services.append({
                'type': 'back_glass_afm',
                'name': 'After Market Back Glass Replacement',
                'price': self.afm_back_glass,
                'category': 'Back Glass'
            })
        
        return services
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'brand': self.brand,
            'model': self.model,
            'model_display': self.model_display,
            'display_name': self.display_name,
            'original_screen': self.original_screen,
            'original_battery': self.original_battery,
            'original_back_glass': self.original_back_glass,
            'afm_screen': self.afm_screen,
            'afm_battery': self.afm_battery,
            'afm_back_glass': self.afm_back_glass,
            'charger_port': self.charger_port,
            'charger_port_original': self.charger_port_original,
            'speaker': self.speaker,
            'camera_lens': self.camera_lens,
            'vibrator': self.vibrator,
            'is_active': self.is_active,
            'is_refurbished_only': self.is_refurbished_only,
            'notes': self.notes,
            'available_services': self.get_available_services()
        }


class WaterDamageService(db.Model):
    """Model for water damage diagnostic and repair services"""
    __tablename__ = 'water_damage_service'
    
    id = db.Column(db.Integer, primary_key=True)
    
    diagnostic_fee = db.Column(db.Float, nullable=False, default=55.00)  # Non-refundable diagnostic fee
    is_diagnostic_refundable = db.Column(db.Boolean, default=False)
    
    # Service details
    name = db.Column(db.String(100), default="Water Damage Diagnostic & Repair")
    description = db.Column(db.Text, default="Comprehensive diagnostic with repair if needed")
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<WaterDamageService {self.name}>'
    
    @classmethod
    def get_current_service(cls):
        """Get the current water damage service configuration"""
        return cls.query.first()


class LaptopTabletService(db.Model):
    """Model for laptop and tablet repair services"""
    __tablename__ = 'laptop_tablet_service'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Service information
    device_type = db.Column(db.String(50), nullable=False)  # Laptop, iPad, Tablet
    service_type = db.Column(db.String(100), nullable=False)  # Screen Repair, Battery, etc.
    
    # Pricing (call for quote)
    requires_quote = db.Column(db.Boolean, default=True)
    base_price = db.Column(db.Float, nullable=True)  # Optional base price
    
    # Service details
    requires_dropoff = db.Column(db.Boolean, default=True)
    typical_turnaround = db.Column(db.String(50), default="Same day")  # Same day, 24 hours, etc.
    
    # Contact information
    quote_email = db.Column(db.String(100), default="info@fixbulance.com")
    quote_phone = db.Column(db.String(20))
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<LaptopTabletService {self.device_type} {self.service_type}>'
    
    @classmethod
    def get_laptop_services(cls):
        """Get all laptop services"""
        return cls.query.filter_by(device_type='Laptop', is_active=True).all()
    
    @classmethod
    def get_ipad_services(cls):
        """Get all iPad services"""
        return cls.query.filter_by(device_type='iPad', is_active=True).all()


# Device model mappings for the pricing data
IPHONE_MODELS = [
    'XR', 'X', 'XS', 'XS Max', '11', '11 Pro', '11 Pro Max', 'SE 2020',
    '12 Mini', '12', '12 Pro', '12 Pro Max', 'SE 2022',
    '13 Mini', '13', '13 Pro', '13 Pro Max',
    '14', '14 Plus', '14 Pro', '14 Pro Max',
    '15', '15 Plus', '15 Pro', '15 Pro Max',
    '16', '16 Plus', '16 Pro', '16 Pro Max', '16 E'
]

SAMSUNG_MODELS = [
    'S20', 'S20 Plus', 'S20 Ultra', 'S20 FE',
    'S21', 'S21 Plus', 'S21 Ultra', 'S21 FE',
    'S22', 'S22 Plus', 'S22 Ultra',
    'S23', 'S23 Plus', 'S23 Ultra', 'S23 FE',
    'S24', 'S24 Plus', 'S24 Ultra', 'S24 FE',
    'S25', 'S25 Plus', 'S25 Ultra', 'S25 Edge',
    'Note 20', 'Note 20 Ultra',
    'A31', 'A51', 'A71', 'A32', 'A52', 'A72',
    'A33', 'A53', 'A73', 'A34', 'A54', 'A35', 'A55', 'A36', 'A56'
] 