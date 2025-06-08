from datetime import datetime
from app import db

class PriceHistory(db.Model):
    """Price history model for tracking service price changes"""
    __tablename__ = 'price_history'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign keys
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    changed_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Price change details
    field_changed = db.Column(db.String(50), nullable=False)  # 'base_price', 'deposit_amount', 'labor_cost', etc.
    old_value = db.Column(db.Numeric(10, 2))
    new_value = db.Column(db.Numeric(10, 2))
    
    # Change reason and notes
    change_reason = db.Column(db.String(200))  # Brief reason for change
    admin_notes = db.Column(db.Text)  # Detailed notes about the change
    
    # Change context
    batch_id = db.Column(db.String(50))  # For grouping related changes
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    service = db.relationship('Service', backref='price_history')
    changed_by = db.relationship('User', backref='price_changes_made')
    
    def __repr__(self):
        return f'<PriceHistory {self.service_id}: {self.field_changed} ${self.old_value} → ${self.new_value}>'
    
    @property
    def change_amount(self):
        """Calculate the change amount"""
        if self.old_value is not None and self.new_value is not None:
            return float(self.new_value) - float(self.old_value)
        return 0.0
    
    @property
    def change_percentage(self):
        """Calculate percentage change"""
        if self.old_value and float(self.old_value) > 0:
            return ((float(self.new_value) - float(self.old_value)) / float(self.old_value)) * 100
        return 0.0
    
    @property
    def is_increase(self):
        """Check if this is a price increase"""
        return self.change_amount > 0
    
    @property
    def is_decrease(self):
        """Check if this is a price decrease"""
        return self.change_amount < 0
    
    @property
    def service_name(self):
        """Get service name"""
        return self.service.name if self.service else 'Unknown Service'
    
    @property
    def changed_by_name(self):
        """Get name of user who made the change"""
        if self.changed_by:
            return f"{self.changed_by.first_name} {self.changed_by.last_name}".strip()
        return 'Unknown User'
    
    @property
    def field_display_name(self):
        """Get human-readable field name"""
        field_names = {
            'base_price': 'Base Price',
            'deposit_amount': 'Deposit Amount',
            'labor_cost': 'Labor Cost',
            'parts_cost': 'Parts Cost',
            'estimated_time': 'Estimated Time'
        }
        return field_names.get(self.field_changed, self.field_changed.replace('_', ' ').title())
    
    @classmethod
    def log_price_change(cls, service_id, field_changed, old_value, new_value, 
                        changed_by_user_id, change_reason=None, admin_notes=None, 
                        batch_id=None):
        """Log a price change"""
        price_history = cls(
            service_id=service_id,
            changed_by_user_id=changed_by_user_id,
            field_changed=field_changed,
            old_value=old_value,
            new_value=new_value,
            change_reason=change_reason,
            admin_notes=admin_notes,
            batch_id=batch_id
        )
        db.session.add(price_history)
        return price_history
    
    @classmethod
    def get_service_price_history(cls, service_id, limit=10):
        """Get price history for a specific service"""
        return cls.query.filter_by(service_id=service_id).order_by(cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def get_recent_changes(cls, days=7, limit=50):
        """Get recent price changes"""
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return cls.query.filter(cls.created_at >= cutoff_date).order_by(cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def get_changes_by_user(cls, user_id, limit=20):
        """Get price changes made by a specific user"""
        return cls.query.filter_by(changed_by_user_id=user_id).order_by(cls.created_at.desc()).limit(limit).all()
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'service_id': self.service_id,
            'service_name': self.service_name,
            'changed_by_user_id': self.changed_by_user_id,
            'changed_by_name': self.changed_by_name,
            'field_changed': self.field_changed,
            'field_display_name': self.field_display_name,
            'old_value': float(self.old_value) if self.old_value else None,
            'new_value': float(self.new_value) if self.new_value else None,
            'change_amount': self.change_amount,
            'change_percentage': self.change_percentage,
            'is_increase': self.is_increase,
            'is_decrease': self.is_decrease,
            'change_reason': self.change_reason,
            'admin_notes': self.admin_notes,
            'batch_id': self.batch_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        } 