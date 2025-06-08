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
    
    # Category relationship (NEW for multi-service)
    category_id = db.Column(db.Integer, db.ForeignKey('service_category.id'))
    
    # Pricing and time (ENHANCED for admin control)
    base_price = db.Column(db.Float, nullable=False)
    deposit_amount = db.Column(db.Float, default=15.00)  # Admin-editable deposit
    labor_cost = db.Column(db.Float, default=0.00)  # NEW: Labor cost component
    parts_cost = db.Column(db.Float, default=0.00)  # NEW: Parts cost component
    estimated_time = db.Column(db.Integer, default=60)   # Minutes
    
    # Service details
    difficulty_level = db.Column(db.String(20), default='medium')  # easy, medium, hard
    requires_parts = db.Column(db.Boolean, default=True)
    warranty_days = db.Column(db.Integer, default=30)
    
    # Multi-service settings (NEW)
    is_emergency = db.Column(db.Boolean, default=False)  # Emergency repair service
    allows_multiple = db.Column(db.Boolean, default=True)  # Can be selected with other services
    max_quantity = db.Column(db.Integer, default=1)  # Maximum quantity per booking
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    
    # Admin tracking (NEW)
    last_price_update = db.Column(db.DateTime)
    last_updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    bookings = db.relationship('Booking', backref='service', lazy=True)
    last_updated_by_user = db.relationship('User', backref='services_updated')
    
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
    
    @property
    def total_cost(self):
        """Get total cost (labor + parts)"""
        return self.labor_cost + self.parts_cost
    
    @property
    def category_name(self):
        """Get category name"""
        return self.category.name if self.category else 'Uncategorized'
    
    @property
    def is_emergency_service(self):
        """Check if this is an emergency service"""
        return self.is_emergency or (self.category and self.category.is_emergency)
    
    @classmethod
    def get_emergency_services(cls):
        """Get all emergency services"""
        return cls.query.filter_by(is_active=True, is_emergency=True).order_by(cls.sort_order, cls.name).all()
    
    @classmethod
    def get_services_by_category(cls, category_id):
        """Get active services by category"""
        return cls.query.filter_by(is_active=True, category_id=category_id).order_by(cls.sort_order, cls.name).all()
    
    @classmethod
    def get_services_by_device_type(cls, device_type):
        """Get active services by device type"""
        return cls.query.filter_by(is_active=True, device_type=device_type).order_by(cls.sort_order, cls.name).all()
    
    def update_price(self, field_name, new_value, updated_by_user_id, change_reason=None):
        """Update a price field and log the change"""
        from app.models.price_history import PriceHistory
        
        old_value = getattr(self, field_name)
        
        if old_value != new_value:
            # Log the change
            PriceHistory.log_price_change(
                service_id=self.id,
                field_changed=field_name,
                old_value=old_value,
                new_value=new_value,
                changed_by_user_id=updated_by_user_id,
                change_reason=change_reason
            )
            
            # Update the field
            setattr(self, field_name, new_value)
            self.last_price_update = datetime.utcnow()
            self.last_updated_by = updated_by_user_id
            
            return True
        return False
    
    def can_be_combined_with(self, other_service):
        """Check if this service can be combined with another service"""
        if not self.allows_multiple or not other_service.allows_multiple:
            return False
        
        # Add business logic for service combinations
        # For example, you might not allow two screen repairs on the same booking
        if self.issue_type == other_service.issue_type and self.issue_type in ['Screen']:
            return False
            
        return True
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'device_type': self.device_type,
            'issue_type': self.issue_type,
            'category_id': self.category_id,
            'category_name': self.category_name,
            'base_price': self.base_price,
            'deposit_amount': self.deposit_amount,
            'labor_cost': self.labor_cost,
            'parts_cost': self.parts_cost,
            'total_cost': self.total_cost,
            'estimated_time': self.estimated_time,
            'difficulty_level': self.difficulty_level,
            'requires_parts': self.requires_parts,
            'warranty_days': self.warranty_days,
            'is_emergency': self.is_emergency,
            'is_emergency_service': self.is_emergency_service,
            'allows_multiple': self.allows_multiple,
            'max_quantity': self.max_quantity,
            'is_active': self.is_active,
            'is_featured': self.is_featured,
            'sort_order': self.sort_order,
            'display_name': self.display_name,
            'price_range': self.price_range,
            'estimated_time_display': self.estimated_time_display,
            'last_price_update': self.last_price_update.isoformat() if self.last_price_update else None
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