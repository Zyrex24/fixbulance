from datetime import datetime
from app import db

class BookingService(db.Model):
    """Junction table for booking and service many-to-many relationship"""
    __tablename__ = 'booking_service'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign keys
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    
    # Service details at time of booking (price snapshot)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    price_snapshot = db.Column(db.Numeric(10, 2), nullable=False)  # Price at time of booking
    labor_cost = db.Column(db.Numeric(10, 2), default=0.00)
    parts_cost = db.Column(db.Numeric(10, 2), default=0.00)
    
    # Time estimation for this specific service in this booking
    estimated_time = db.Column(db.Integer, default=60)  # Minutes
    actual_time = db.Column(db.Integer)  # Actual time spent (minutes)
    
    # Service status within the booking
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed, cancelled
    
    # Work details for this specific service
    work_notes = db.Column(db.Text)
    completion_notes = db.Column(db.Text)
    
    # Completion tracking
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    booking = db.relationship('Booking', backref='booking_services')
    service = db.relationship('Service', backref='booking_services')
    
    # Unique constraint to prevent duplicate service entries per booking
    __table_args__ = (db.UniqueConstraint('booking_id', 'service_id', name='unique_booking_service'),)
    
    def __repr__(self):
        return f'<BookingService {self.booking_id}-{self.service_id}: {self.quantity}x @ ${self.price_snapshot}>'
    
    @property
    def total_cost(self):
        """Calculate total cost for this service (quantity * price)"""
        return float(self.price_snapshot) * self.quantity
    
    @property
    def total_labor_cost(self):
        """Calculate total labor cost"""
        return float(self.labor_cost) * self.quantity
    
    @property
    def total_parts_cost(self):
        """Calculate total parts cost"""
        return float(self.parts_cost) * self.quantity
    
    @property
    def service_name(self):
        """Get service name"""
        return self.service.name if self.service else 'Unknown Service'
    
    @property
    def service_display_name(self):
        """Get formatted service display name"""
        return self.service.display_name if self.service else 'Unknown Service'
    
    @property
    def status_color(self):
        """Get Bootstrap color class for status"""
        status_colors = {
            'pending': 'secondary',
            'in_progress': 'info',
            'completed': 'success',
            'cancelled': 'danger'
        }
        return status_colors.get(self.status, 'secondary')
    
    @property
    def is_completed(self):
        """Check if this service is completed"""
        return self.status == 'completed'
    
    @property
    def duration_display(self):
        """Get formatted duration display"""
        if self.estimated_time < 60:
            return f"{self.estimated_time} min"
        else:
            hours = self.estimated_time // 60
            minutes = self.estimated_time % 60
            if minutes == 0:
                return f"{hours}h"
            else:
                return f"{hours}h {minutes}m"
    
    def update_status(self, new_status):
        """Update service status with timestamps"""
        if new_status != self.status:
            self.status = new_status
            
            if new_status == 'in_progress' and not self.started_at:
                self.started_at = datetime.utcnow()
            elif new_status == 'completed' and not self.completed_at:
                self.completed_at = datetime.utcnow()
    
    @classmethod
    def create_from_service(cls, booking_id, service, quantity=1):
        """Create BookingService from a Service object with current pricing"""
        return cls(
            booking_id=booking_id,
            service_id=service.id,
            quantity=quantity,
            price_snapshot=service.base_price,
            labor_cost=getattr(service, 'labor_cost', 0.00),
            parts_cost=getattr(service, 'parts_cost', 0.00),
            estimated_time=service.estimated_time
        )
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'booking_id': self.booking_id,
            'service_id': self.service_id,
            'service_name': self.service_name,
            'service_display_name': self.service_display_name,
            'quantity': self.quantity,
            'price_snapshot': float(self.price_snapshot),
            'labor_cost': float(self.labor_cost),
            'parts_cost': float(self.parts_cost),
            'total_cost': self.total_cost,
            'estimated_time': self.estimated_time,
            'duration_display': self.duration_display,
            'status': self.status,
            'status_color': self.status_color,
            'is_completed': self.is_completed,
            'work_notes': self.work_notes,
            'completion_notes': self.completion_notes,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        } 