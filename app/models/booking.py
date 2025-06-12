from datetime import datetime
from app import db

class Booking(db.Model):
    """Booking model for repair appointments"""
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # NOTE: service_id is deprecated in favor of many-to-many relationship via BookingService
    # Keeping for backward compatibility during migration
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'))
    
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
    # pending -> deposit_paid -> confirmed -> in_progress -> completed -> cancelled
    
    previous_status = db.Column(db.String(20))
    status_updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    status_updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Multi-service information (NEW)
    total_services_count = db.Column(db.Integer, default=1)
    combined_estimated_duration = db.Column(db.Integer, default=60)  # Total time for all services
    
    # Payment information
    deposit_amount = db.Column(db.Float, default=15.00)
    total_estimated_cost = db.Column(db.Float)
    final_amount = db.Column(db.Float)
    payment_status = db.Column(db.String(20), default='pending')
    # pending -> deposit_paid -> balance_paid -> refunded
    
    # Tax information
    tax_rate = db.Column(db.Float, default=0.1025)  # Default IL sales tax rate 10.25%
    tax_amount = db.Column(db.Float, default=0.0)
    subtotal = db.Column(db.Float, default=0.0)  # Pre-tax amount
    total_with_tax = db.Column(db.Float, default=0.0)  # Final amount including tax
    tax_jurisdiction = db.Column(db.String(100), default='Illinois')  # Tax location
    
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
            'pending': 'warning',        # Orange
            'deposit_paid': 'success',   # Green - deposit received, clearly visible
            'confirmed': 'primary',      # Blue - confirmed by admin
            'in_progress': 'info',       # Light blue - work in progress
            'completed': 'dark',         # Dark - completed
            'cancelled': 'danger'        # Red
        }
        return status_colors.get(self.status, 'secondary')
    
    @property
    def status_icon(self):
        """Get icon for status display"""
        status_icons = {
            'pending': 'clock',
            'deposit_paid': 'credit-card',    # Credit card icon for paid
            'confirmed': 'check-circle',
            'in_progress': 'tools',
            'completed': 'check-square',
            'cancelled': 'x-circle'
        }
        return status_icons.get(self.status, 'circle')
    
    @property
    def status_display(self):
        """Get human-readable status display"""
        status_displays = {
            'pending': 'Pending Payment',
            'deposit_paid': 'Deposit Paid',
            'confirmed': 'Confirmed',
            'in_progress': 'In Progress',
            'completed': 'Completed',
            'cancelled': 'Cancelled'
        }
        return status_displays.get(self.status, self.status.replace('_', ' ').title())
    
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
        
        # Urgent if within 2 hours and not confirmed or deposit paid
        return time_until.total_seconds() < 7200 and self.status in ['pending', 'deposit_paid']
    
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
    
    # NEW: Multi-service methods
    @property
    def services(self):
        """Get all services associated with this booking"""
        return [bs.service for bs in self.booking_services if bs.service]
    
    @property
    def services_list(self):
        """Get list of BookingService objects"""
        return self.booking_services
    
    @property
    def services_count(self):
        """Get count of services in this booking"""
        return len(self.booking_services)
    
    @property
    def total_services_cost(self):
        """Calculate total cost of all services"""
        return sum(bs.total_cost for bs in self.booking_services)
    
    @property
    def services_display_names(self):
        """Get comma-separated list of service names"""
        return ', '.join([bs.service_display_name for bs in self.booking_services])
    
    @property
    def combined_duration_display(self):
        """Get formatted combined duration display"""
        if self.combined_estimated_duration < 60:
            return f"{self.combined_estimated_duration} min"
        else:
            hours = self.combined_estimated_duration // 60
            minutes = self.combined_estimated_duration % 60
            if minutes == 0:
                return f"{hours}h"
            else:
                return f"{hours}h {minutes}m"
    
    @property
    def is_multi_service(self):
        """Check if this booking has multiple services"""
        return len(self.booking_services) > 1
    
    @property
    def emergency_services_count(self):
        """Count emergency services in this booking"""
        return len([bs for bs in self.booking_services if bs.service and bs.service.is_emergency_service])
    
    @property
    def has_emergency_services(self):
        """Check if booking contains emergency services"""
        return self.emergency_services_count > 0
    
    def add_service(self, service, quantity=1):
        """Add a service to this booking"""
        from app.models.booking_service import BookingService
        
        # Check if service already exists in booking
        existing = next((bs for bs in self.booking_services if bs.service_id == service.id), None)
        if existing:
            existing.quantity += quantity
            existing.price_snapshot = service.base_price  # Update to current price
        else:
            booking_service = BookingService.create_from_service(self.id, service, quantity)
            db.session.add(booking_service)
        
        self._recalculate_totals()
    
    def remove_service(self, service_id):
        """Remove a service from this booking"""
        booking_service = next((bs for bs in self.booking_services if bs.service_id == service_id), None)
        if booking_service:
            db.session.delete(booking_service)
            self._recalculate_totals()
            return True
        return False
    
    def update_service_quantity(self, service_id, quantity):
        """Update quantity of a service in this booking"""
        booking_service = next((bs for bs in self.booking_services if bs.service_id == service_id), None)
        if booking_service:
            if quantity <= 0:
                return self.remove_service(service_id)
            else:
                booking_service.quantity = quantity
                self._recalculate_totals()
                return True
        return False
    
    def _recalculate_totals(self):
        """Recalculate total costs and durations for multi-service booking"""
        total_cost = sum(bs.total_cost for bs in self.booking_services)
        total_duration = sum(bs.estimated_duration for bs in self.booking_services)
        
        self.total_services_count = len(self.booking_services)
        self.total_estimated_cost = total_cost
        self.combined_estimated_duration = total_duration
        
        # Recalculate tax and final amounts
        self.calculate_tax()
    
    def calculate_tax(self, service_price=None):
        """Calculate tax based on location and service price"""
        if service_price is None:
            service_price = self.total_estimated_cost or 0
        
        # Set subtotal
        self.subtotal = service_price
        
        # Calculate tax based on location
        tax_rate = self.get_tax_rate_by_location()
        self.tax_rate = tax_rate
        self.tax_amount = service_price * tax_rate
        
        # Calculate total with tax (excluding deposit)
        self.total_with_tax = service_price + self.tax_amount
        
        # Update final amount (deposit + remaining balance with tax)
        self.final_amount = self.deposit_amount + self.total_with_tax
        
        return {
            'subtotal': self.subtotal,
            'tax_rate': self.tax_rate,
            'tax_amount': self.tax_amount,
            'total_with_tax': self.total_with_tax,
            'deposit': self.deposit_amount,
            'final_amount': self.final_amount
        }
    
    def get_tax_rate_by_location(self):
        """Get tax rate based on service location (zip code)"""
        # Illinois tax rates by major areas (simplified)
        il_tax_rates = {
            # Chicago area
            '606': 0.1025,  # Chicago downtown
            '607': 0.1025,  # Chicago north
            '608': 0.1025,  # Chicago south
            '609': 0.1025,  # Chicago west
            '604': 0.0925,  # DuPage County
            '605': 0.0875,  # Lake County
            '600': 0.0825,  # Suburban Cook County
            '601': 0.0825,  # Suburban Cook County
            
            # Default Illinois rate for other areas
            'default': 0.0625  # State base rate
        }
        
        if self.service_zip_code:
            # Check first 3 digits of zip code
            zip_prefix = self.service_zip_code[:3]
            return il_tax_rates.get(zip_prefix, il_tax_rates['default'])
        
        return il_tax_rates['default']
    
    @property
    def tax_breakdown(self):
        """Get formatted tax breakdown for display"""
        return {
            'subtotal_display': f"${self.subtotal:.2f}" if self.subtotal else "$0.00",
            'tax_rate_display': f"{self.tax_rate * 100:.2f}%" if self.tax_rate else "0.00%",
            'tax_amount_display': f"${self.tax_amount:.2f}" if self.tax_amount else "$0.00",
            'total_display': f"${self.total_with_tax:.2f}" if self.total_with_tax else "$0.00",
            'jurisdiction': self.tax_jurisdiction or "Illinois"
        }
    
    # For backward compatibility - return primary service if exists
    @property
    def primary_service(self):
        """Get primary service (for backward compatibility)"""
        if self.service_id and self.service:
            return self.service
        elif self.booking_services:
            return self.booking_services[0].service
        return None
    
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
            'status_display': self.status_display,
            'status_color': self.status_color,
            'status_icon': self.status_icon,
            'payment_status': self.payment_status,
            'payment_status_display': self.payment_status_display,
            'deposit_amount': self.deposit_amount,
            'total_estimated_cost': self.total_estimated_cost,
            'final_amount': self.final_amount,
            'is_same_day': self.is_same_day,
            'is_urgent': self.is_urgent,
            # Multi-service information
            'total_services_count': self.total_services_count,
            'services_count': self.services_count,
            'is_multi_service': self.is_multi_service,
            'services_display_names': self.services_display_names,
            'combined_estimated_duration': self.combined_estimated_duration,
            'combined_duration_display': self.combined_duration_display,
            'has_emergency_services': self.has_emergency_services,
            'emergency_services_count': self.emergency_services_count,
            'total_services_cost': self.total_services_cost,
            'services': [bs.to_dict() for bs in self.booking_services],
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# Booking status constants
BOOKING_STATUSES = [
    'pending',
    'deposit_paid',
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