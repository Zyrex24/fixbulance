from datetime import datetime
from app import db

class ServiceCategory(db.Model):
    """Service category model for organizing repair services"""
    __tablename__ = 'service_category'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Category information
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    
    # Display settings
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    
    # Admin settings
    is_emergency = db.Column(db.Boolean, default=False)  # Emergency repair category
    requires_admin_approval = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    services = db.relationship('Service', backref='category', lazy=True)
    
    def __repr__(self):
        return f'<ServiceCategory {self.name}>'
    
    @property
    def active_services_count(self):
        """Get count of active services in this category"""
        return len([s for s in self.services if s.is_active])
    
    @property
    def total_services_count(self):
        """Get total count of services in this category"""
        return len(self.services)
    
    @classmethod
    def get_active_categories(cls):
        """Get all active categories ordered by sort_order"""
        return cls.query.filter_by(is_active=True).order_by(cls.sort_order, cls.name).all()
    
    @classmethod
    def get_emergency_categories(cls):
        """Get emergency repair categories"""
        return cls.query.filter_by(is_active=True, is_emergency=True).order_by(cls.sort_order).all()
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
            'is_emergency': self.is_emergency,
            'requires_admin_approval': self.requires_admin_approval,
            'active_services_count': self.active_services_count,
            'total_services_count': self.total_services_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 