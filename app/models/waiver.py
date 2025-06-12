from datetime import datetime
from app import db

class ServiceWaiver(db.Model):
    """Service Waiver Agreement model for digital waiver signatures"""
    __tablename__ = 'service_waiver'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign keys
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Customer information
    customer_name = db.Column(db.String(100), nullable=False)
    device_model = db.Column(db.String(100), nullable=False)
    service_date = db.Column(db.Date, nullable=False)
    
    # Digital signature
    digital_signature = db.Column(db.String(100), nullable=False)  # Customer's typed name
    signature_timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))  # IPv4/IPv6 address
    user_agent = db.Column(db.Text)  # Browser information
    
    # Technician information
    technician_name = db.Column(db.String(100))
    repair_location = db.Column(db.String(100), default='On-site')
    
    # Agreement details
    waiver_version = db.Column(db.String(10), default='1.0')
    effective_date = db.Column(db.Date, nullable=False)
    
    # Agreement acknowledgments (for detailed tracking)
    acknowledged_risk = db.Column(db.Boolean, default=True)
    acknowledged_data_responsibility = db.Column(db.Boolean, default=True)
    acknowledged_warranty_limitations = db.Column(db.Boolean, default=True)
    acknowledged_non_repairable = db.Column(db.Boolean, default=True)
    acknowledged_third_party_parts = db.Column(db.Boolean, default=True)
    authorized_repair = db.Column(db.Boolean, default=True)
    
    # Status tracking
    status = db.Column(db.String(20), default='signed')  # signed, voided, expired
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    booking = db.relationship('Booking', backref=db.backref('waiver', uselist=False))
    user = db.relationship('User', backref='waivers')
    
    def __repr__(self):
        return f'<ServiceWaiver {self.id}: {self.customer_name} - {self.device_model}>'
    
    @property
    def status_color(self):
        """Get Bootstrap color class for status"""
        status_colors = {
            'signed': 'success',
            'voided': 'warning',
            'expired': 'danger'
        }
        return status_colors.get(self.status, 'secondary')
    
    @property
    def status_icon(self):
        """Get icon for status display"""
        status_icons = {
            'signed': 'check-circle',
            'voided': 'x-circle',
            'expired': 'clock'
        }
        return status_icons.get(self.status, 'circle')
    
    @property
    def is_valid(self):
        """Check if waiver is still valid"""
        return self.status == 'signed'
    
    @property
    def signature_date_display(self):
        """Get formatted signature date"""
        return self.signature_timestamp.strftime('%B %d, %Y at %I:%M %p')
    
    def to_dict(self):
        """Convert waiver to dictionary for JSON responses"""
        return {
            'id': self.id,
            'booking_id': self.booking_id,
            'customer_name': self.customer_name,
            'device_model': self.device_model,
            'service_date': self.service_date.isoformat() if self.service_date else None,
            'digital_signature': self.digital_signature,
            'signature_timestamp': self.signature_timestamp.isoformat() if self.signature_timestamp else None,
            'technician_name': self.technician_name,
            'repair_location': self.repair_location,
            'status': self.status,
            'waiver_version': self.waiver_version,
            'created_at': self.created_at.isoformat() if self.created_at else None
        } 