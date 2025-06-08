from datetime import datetime
from app import db

class Payment(db.Model):
    """Payment model for tracking Stripe transactions"""
    id = db.Column(db.Integer, primary_key=True)
    
    # Relationships
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Stripe information
    stripe_payment_intent_id = db.Column(db.String(255), unique=True, index=True)
    stripe_charge_id = db.Column(db.String(255), index=True)
    stripe_customer_id = db.Column(db.String(255), index=True)
    
    # Payment details
    amount = db.Column(db.Numeric(10, 2), nullable=False)  # Amount in dollars
    currency = db.Column(db.String(3), default='usd', nullable=False)
    payment_type = db.Column(db.String(20), nullable=False)  # 'deposit' or 'final'
    
    # Status tracking
    status = db.Column(db.String(50), default='pending', index=True)
    # pending -> processing -> succeeded -> failed -> canceled -> refunded
    
    # Payment method information
    payment_method_type = db.Column(db.String(50))  # card, ach_debit, etc.
    card_brand = db.Column(db.String(20))  # visa, mastercard, amex, discover
    card_last4 = db.Column(db.String(4))
    
    # Business information
    description = db.Column(db.String(255))
    receipt_email = db.Column(db.String(255))
    receipt_url = db.Column(db.String(500))
    
    # Metadata for business tracking
    device_type = db.Column(db.String(50))
    service_name = db.Column(db.String(100))
    customer_name = db.Column(db.String(100))
    customer_phone = db.Column(db.String(20))
    
    # Error handling
    error_code = db.Column(db.String(100))
    error_message = db.Column(db.Text)
    failure_reason = db.Column(db.String(255))
    
    # Refund information
    refunded_amount = db.Column(db.Numeric(10, 2), default=0.00)
    refund_reason = db.Column(db.String(255))
    refunded_at = db.Column(db.DateTime)
    refunded_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    
    # Relationships
    booking = db.relationship('Booking', backref='payments')
    user = db.relationship('User', foreign_keys=[user_id], backref='payments')
    refunded_by_user = db.relationship('User', foreign_keys=[refunded_by])
    
    def __repr__(self):
        return f'<Payment {self.id}: {self.payment_type} ${self.amount} - {self.status}>'
    
    @property
    def amount_dollars(self):
        """Get amount as float for display"""
        return float(self.amount) if self.amount else 0.00
    
    @property
    def is_successful(self):
        """Check if payment was successful"""
        return self.status == 'succeeded'
    
    @property
    def is_refundable(self):
        """Check if payment can be refunded"""
        return self.status == 'succeeded' and self.refunded_amount < self.amount
    
    @property
    def status_color(self):
        """Get Bootstrap color class for payment status"""
        status_colors = {
            'pending': 'warning',
            'processing': 'info',
            'succeeded': 'success',
            'failed': 'danger',
            'canceled': 'secondary',
            'refunded': 'dark'
        }
        return status_colors.get(self.status, 'secondary')
    
    @property
    def status_icon(self):
        """Get icon for payment status"""
        status_icons = {
            'pending': 'clock',
            'processing': 'spinner',
            'succeeded': 'check-circle',
            'failed': 'x-circle',
            'canceled': 'slash-circle',
            'refunded': 'arrow-counterclockwise'
        }
        return status_icons.get(self.status, 'circle')
    
    @property
    def display_card_info(self):
        """Get formatted card information for display"""
        if self.card_brand and self.card_last4:
            brand = self.card_brand.title()
            return f"{brand} ending in {self.card_last4}"
        return "Card"
    
    def update_status(self, new_status, error_message=None, processed_at=None):
        """Update payment status with tracking"""
        self.status = new_status
        self.updated_at = datetime.utcnow()
        
        if error_message:
            self.error_message = error_message
            
        if processed_at:
            self.processed_at = processed_at
        elif new_status in ['succeeded', 'failed']:
            self.processed_at = datetime.utcnow()
    
    def create_refund(self, amount, reason, refunded_by_user_id):
        """Track refund information"""
        self.refunded_amount = float(self.refunded_amount or 0) + float(amount)
        self.refund_reason = reason
        self.refunded_at = datetime.utcnow()
        self.refunded_by = refunded_by_user_id
        
        # Update status if fully refunded
        if self.refunded_amount >= self.amount:
            self.status = 'refunded'
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'booking_id': self.booking_id,
            'stripe_payment_intent_id': self.stripe_payment_intent_id,
            'amount': self.amount_dollars,
            'currency': self.currency,
            'payment_type': self.payment_type,
            'status': self.status,
            'status_color': self.status_color,
            'status_icon': self.status_icon,
            'payment_method_type': self.payment_method_type,
            'display_card_info': self.display_card_info,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }

# Payment status constants
PAYMENT_STATUSES = [
    'pending',
    'processing',
    'succeeded',
    'failed',
    'canceled',
    'refunded'
]

PAYMENT_TYPES = [
    'deposit',
    'final'
] 