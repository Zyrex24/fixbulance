from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app import db

class User(UserMixin, db.Model):
    """User model for customers and admin"""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Personal information
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    
    # Address information (for service area validation)
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    state = db.Column(db.String(2), default='IL')
    zip_code = db.Column(db.String(10))
    
    # Communication preferences (Creative Decision: Email + SMS hybrid)
    sms_opted_in = db.Column(db.Boolean, default=False)
    email_notifications = db.Column(db.Boolean, default=True)
    marketing_emails = db.Column(db.Boolean, default=False)
    
    # Account management
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    email_verified = db.Column(db.Boolean, default=False)
    email_verification_token = db.Column(db.String(100))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    bookings = db.relationship('Booking', foreign_keys='Booking.user_id', backref='customer', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        """Get full name"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def total_bookings(self):
        """Get total number of bookings"""
        return len(self.bookings)
    
    def get_recent_bookings(self, limit=5):
        """Get recent bookings"""
        from app.models.booking import Booking
        return Booking.query.filter_by(user_id=self.id).order_by(Booking.created_at.desc()).limit(limit).all()
    
    def can_receive_sms(self):
        """Check if user can receive SMS notifications"""
        return self.sms_opted_in and self.phone
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'phone': self.phone,
            'city': self.city,
            'state': self.state,
            'zip_code': self.zip_code,
            'total_bookings': self.total_bookings,
            'created_at': self.created_at.isoformat() if self.created_at else None
        } 