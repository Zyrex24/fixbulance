from datetime import datetime
from app import db

class Service(db.Model):
    """Service model for repair services"""
    id = db.Column(db.Integer, primary_key=True)
    
    # Service information
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    device_type = db.Column(db.String(50), nullable=False, index=True)  # iPhone, Samsung, Other
    issue_type = db.Column(db.String(50), nullable=False, index=True)   # Screen, Battery, Water, etc.
    
    # Pricing and time
    base_price = db.Column(db.Float, nullable=False)
    deposit_amount = db.Column(db.Float, default=15.00)  # Standard $15 deposit
    estimated_time = db.Column(db.Integer, default=60)   # Minutes
    
    # Service details
    difficulty_level = db.Column(db.String(20), default='medium')  # easy, medium, hard
    requires_parts = db.Column(db.Boolean, default=True)
    warranty_days = db.Column(db.Integer, default=30)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    bookings = db.relationship('Booking', backref='service', lazy=True)
    
    def __repr__(self):
        return f'<Service {self.name} for {self.device_type}>'
    
    @property
    def display_name(self):
        """Get formatted display name"""
        return f"{self.device_type} {self.name}"
    
    @property
    def price_range(self):
        """Get price range description"""
        if self.base_price == self.deposit_amount:
            return f"${self.base_price:.0f}"
        else:
            return f"${self.deposit_amount:.0f} deposit + ${self.base_price - self.deposit_amount:.0f}"
    
    @property
    def estimated_time_display(self):
        """Get formatted time estimate"""
        if self.estimated_time < 60:
            return f"{self.estimated_time} minutes"
        else:
            hours = self.estimated_time // 60
            minutes = self.estimated_time % 60
            if minutes == 0:
                return f"{hours} hour{'s' if hours > 1 else ''}"
            else:
                return f"{hours}h {minutes}m"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'device_type': self.device_type,
            'issue_type': self.issue_type,
            'base_price': self.base_price,
            'deposit_amount': self.deposit_amount,
            'estimated_time': self.estimated_time,
            'difficulty_level': self.difficulty_level,
            'requires_parts': self.requires_parts,
            'warranty_days': self.warranty_days,
            'display_name': self.display_name,
            'price_range': self.price_range,
            'estimated_time_display': self.estimated_time_display
        }

# Predefined device types and issue types for the application
DEVICE_TYPES = [
    'iPhone',
    'Samsung',
    'Other'
]

ISSUE_TYPES = [
    'Screen',
    'Battery',
    'Water Damage',
    'Charging Port',
    'Speaker',
    'Camera',
    'Software',
    'Other'
]

DIFFICULTY_LEVELS = [
    'easy',
    'medium',
    'hard'
] 