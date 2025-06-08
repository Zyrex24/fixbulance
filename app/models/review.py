from datetime import datetime
from app import db

class Review(db.Model):
    """Customer review and feedback model"""
    __tablename__ = 'review'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign keys
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Rating (1-5 stars)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    
    # Review content
    title = db.Column(db.String(200))
    review_text = db.Column(db.Text)
    
    # Service quality ratings (1-5 each)
    technician_rating = db.Column(db.Integer)  # Technician professionalism
    timeliness_rating = db.Column(db.Integer)  # Punctuality and speed
    communication_rating = db.Column(db.Integer)  # Communication quality
    value_rating = db.Column(db.Integer)  # Value for money
    
    # Review details
    would_recommend = db.Column(db.Boolean, default=True)
    is_public = db.Column(db.Boolean, default=True)  # Can be displayed publicly
    is_verified = db.Column(db.Boolean, default=True)  # Verified customer
    
    # Service feedback
    service_issues = db.Column(db.Text)  # Any issues encountered
    suggestions = db.Column(db.Text)  # Improvement suggestions
    
    # Review metadata
    device_type = db.Column(db.String(100))  # What device was repaired
    service_type = db.Column(db.String(100))  # What service was provided
    
    # Admin response
    admin_response = db.Column(db.Text)
    admin_response_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    admin_response_at = db.Column(db.DateTime)
    
    # Status and moderation
    status = db.Column(db.String(20), default='active')  # active, hidden, flagged
    flagged_reason = db.Column(db.String(200))
    moderated_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    moderated_at = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    booking = db.relationship('Booking', backref='review')
    customer = db.relationship('User', foreign_keys=[user_id], backref='reviews_given')
    admin_responder = db.relationship('User', foreign_keys=[admin_response_by])
    moderator = db.relationship('User', foreign_keys=[moderated_by])
    
    def __repr__(self):
        return f'<Review {self.id}: {self.rating}★ for Booking #{self.booking_id}>'
    
    @property
    def star_display(self):
        """Get star display (★★★★☆)"""
        filled_stars = '★' * self.rating
        empty_stars = '☆' * (5 - self.rating)
        return filled_stars + empty_stars
    
    @property
    def average_detailed_rating(self):
        """Calculate average of detailed ratings"""
        ratings = [
            self.technician_rating,
            self.timeliness_rating,
            self.communication_rating,
            self.value_rating
        ]
        valid_ratings = [r for r in ratings if r is not None]
        return sum(valid_ratings) / len(valid_ratings) if valid_ratings else None
    
    @property
    def customer_name(self):
        """Get customer name for display"""
        if self.customer:
            return f"{self.customer.first_name} {self.customer.last_name}".strip()
        return "Anonymous Customer"
    
    @property
    def customer_initial(self):
        """Get customer initial for privacy (e.g., 'John D.')"""
        if self.customer and self.customer.first_name:
            first_name = self.customer.first_name
            last_initial = self.customer.last_name[0] + '.' if self.customer.last_name else ''
            return f"{first_name} {last_initial}".strip()
        return "Anonymous"
    
    @property
    def is_positive(self):
        """Check if review is positive (4-5 stars)"""
        return self.rating >= 4
    
    @property
    def is_negative(self):
        """Check if review is negative (1-2 stars)"""
        return self.rating <= 2
    
    @property
    def rating_color(self):
        """Get Bootstrap color class for rating"""
        if self.rating >= 4:
            return 'success'
        elif self.rating == 3:
            return 'warning'
        else:
            return 'danger'
    
    @property
    def service_summary(self):
        """Get service summary from booking"""
        if self.booking and self.booking.booking_services:
            services = [bs.service.name for bs in self.booking.booking_services if bs.service]
            return ', '.join(services) if services else self.service_type
        return self.service_type or 'Mobile Repair Service'
    
    def can_be_displayed_publicly(self):
        """Check if review can be displayed publicly"""
        return (
            self.is_public and 
            self.status == 'active' and 
            self.is_verified
        )
    
    @classmethod
    def get_public_reviews(cls, limit=10, rating_filter=None):
        """Get public reviews for display"""
        query = cls.query.filter_by(is_public=True, status='active', is_verified=True)
        
        if rating_filter:
            query = query.filter(cls.rating >= rating_filter)
        
        return query.order_by(cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def get_average_rating(cls):
        """Get overall average rating"""
        from sqlalchemy import func
        result = db.session.query(func.avg(cls.rating)).filter_by(
            status='active', is_verified=True
        ).scalar()
        return round(result, 1) if result else 0.0
    
    @classmethod
    def get_rating_distribution(cls):
        """Get distribution of ratings (1-5 stars)"""
        from sqlalchemy import func
        distribution = {}
        for star in range(1, 6):
            count = cls.query.filter_by(
                rating=star, status='active', is_verified=True
            ).count()
            distribution[star] = count
        return distribution
    
    @classmethod
    def get_recent_reviews(cls, days=30, limit=20):
        """Get recent reviews for admin dashboard"""
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return cls.query.filter(
            cls.created_at >= cutoff_date
        ).order_by(cls.created_at.desc()).limit(limit).all()
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'booking_id': self.booking_id,
            'customer_name': self.customer_initial if self.is_public else 'Anonymous',
            'rating': self.rating,
            'star_display': self.star_display,
            'title': self.title,
            'review_text': self.review_text,
            'technician_rating': self.technician_rating,
            'timeliness_rating': self.timeliness_rating,
            'communication_rating': self.communication_rating,
            'value_rating': self.value_rating,
            'average_detailed_rating': self.average_detailed_rating,
            'would_recommend': self.would_recommend,
            'device_type': self.device_type,
            'service_type': self.service_summary,
            'is_positive': self.is_positive,
            'is_negative': self.is_negative,
            'rating_color': self.rating_color,
            'admin_response': self.admin_response,
            'admin_response_at': self.admin_response_at.isoformat() if self.admin_response_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        } 