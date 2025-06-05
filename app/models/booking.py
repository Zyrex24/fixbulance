from datetime import datetime
from app import db

class Booking(db.Model):
    """Booking model for repair appointments"""
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    
    # Booking details (Multi-step wizard data)
    device_model = db.Column(db.String(100), nullable=False)
    issue_description = db.Column(db.Text)
    photos_uploaded = db.Column(db.Boolean, default=False)
    photo_filenames = db.Column(db.Text)  # JSON array of uploaded photo filenames
    
    # Appointment scheduling
    scheduled_date = db.Column(db.Date, nullable=False, index=True)
    scheduled_time = db.Column(db.Time, nullable=False)
    estimated_duration = db.Column(db.Integer, default=60)  # Minutes
    
    # Customer location (Service radius validation)
    service_address = db.Column(db.Text, nullable=False)
    service_city = db.Column(db.String(100))
    service_state = db.Column(db.String(2), default='IL')
    service_zip_code = db.Column(db.String(10), nullable=False, index=True)
    address_validated = db.Column(db.Boolean, default=False)
    within_service_area = db.Column(db.Boolean, default=True)
    
    # Status tracking (Card-based admin dashboard)
    status = db.Column(db.String(20), default='pending', index=True)
    # pending -> confirmed -> in_progress -> completed -> cancelled
    
    previous_status = db.Column(db.String(20))
    status_updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    status_updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Payment information
    deposit_amount = db.Column(db.Float, default=15.00)
    total_estimated_cost = db.Column(db.Float)
    final_amount = db.Column(db.Float)
    payment_status = db.Column(db.String(20), default='pending')
    # pending -> deposit_paid -> balance_paid -> refunded
    
    # Stripe payment details
    stripe_payment_intent_id = db.Column(db.String(100))
    stripe_deposit_payment_id = db.Column(db.String(100))
    stripe_final_payment_id = db.Column(db.String(100))
    
    # Communication tracking (Email + SMS system)
    confirmation_sent = db.Column(db.Boolean, default=False)
    reminder_sent = db.Column(db.Boolean, default=False)
    arrival_notification_sent = db.Column(db.Boolean, default=False)
    completion_notification_sent = db.Column(db.Boolean, default=False)
    
    # Work summary
    work_performed = db.Column(db.Text)
    parts_used = db.Column(db.Text)
    technician_notes = db.Column(db.Text)
    customer_rating = db.Column(db.Integer)  # 1-5 stars
    customer_feedback = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Booking {self.id}: {self.device_model} on {self.scheduled_date}>'
    
    @property
    def appointment_datetime(self):
        """Get combined datetime for appointment"""
        if self.scheduled_date and self.scheduled_time:
            return datetime.combine(self.scheduled_date, self.scheduled_time)
        return None
    
    @property
    def status_color(self):
        """Get Bootstrap color class for status (Card-based dashboard design)"""
        status_colors = {
            'pending': 'warning',      # Orange
            'confirmed': 'success',    # Green
            'in_progress': 'primary',  # Blue
            'completed': 'info',       # Light blue
            'cancelled': 'danger'      # Red
        }
        return status_colors.get(self.status, 'secondary')
    
    @property
    def status_icon(self):
        """Get icon for status display"""
        status_icons = {
            'pending': 'clock',
            'confirmed': 'check-circle',
            'in_progress': 'tools',
            'completed': 'check-square',
            'cancelled': 'x-circle'
        }
        return status_icons.get(self.status, 'circle')
    
    @property
    def payment_status_display(self):
        """Get formatted payment status"""
        if self.payment_status == 'pending':
            return f"Awaiting ${self.deposit_amount:.0f} deposit"
        elif self.payment_status == 'deposit_paid':
            remaining = (self.final_amount or self.total_estimated_cost) - self.deposit_amount
            return f"${remaining:.0f} balance due"
        elif self.payment_status == 'balance_paid':
            return "Paid in full"
        elif self.payment_status == 'refunded':
            return "Refunded"
        return self.payment_status.replace('_', ' ').title()
    
    @property
    def is_same_day(self):
        """Check if booking is for same day"""
        return self.scheduled_date == datetime.now().date()
    
    @property
    def is_urgent(self):
        """Check if booking needs urgent attention"""
        if not self.appointment_datetime:
            return False
        
        now = datetime.now()
        time_until = self.appointment_datetime - now
        
        # Urgent if within 2 hours and not confirmed
        return time_until.total_seconds() < 7200 and self.status == 'pending'
    
    def update_status(self, new_status, updated_by_user_id=None):
        """Update booking status with tracking"""
        if new_status != self.status:
            self.previous_status = self.status
            self.status = new_status
            self.status_updated_at = datetime.utcnow()
            self.status_updated_by = updated_by_user_id
            
            if new_status == 'completed':
                self.completed_at = datetime.utcnow()
    
    def get_photo_list(self):
        """Get list of uploaded photo filenames"""
        if self.photo_filenames:
            import json
            try:
                return json.loads(self.photo_filenames)
            except:
                return []
        return []
    
    def add_photo(self, filename):
        """Add photo filename to the list"""
        import json
        photos = self.get_photo_list()
        photos.append(filename)
        self.photo_filenames = json.dumps(photos)
        self.photos_uploaded = True
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'device_model': self.device_model,
            'issue_description': self.issue_description,
            'scheduled_date': self.scheduled_date.isoformat() if self.scheduled_date else None,
            'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
            'service_address': self.service_address,
            'service_zip_code': self.service_zip_code,
            'status': self.status,
            'status_color': self.status_color,
            'status_icon': self.status_icon,
            'payment_status': self.payment_status,
            'payment_status_display': self.payment_status_display,
            'deposit_amount': self.deposit_amount,
            'total_estimated_cost': self.total_estimated_cost,
            'final_amount': self.final_amount,
            'is_same_day': self.is_same_day,
            'is_urgent': self.is_urgent,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# Booking status constants
BOOKING_STATUSES = [
    'pending',
    'confirmed', 
    'in_progress',
    'completed',
    'cancelled'
]

PAYMENT_STATUSES = [
    'pending',
    'deposit_paid',
    'balance_paid',
    'refunded'
] 