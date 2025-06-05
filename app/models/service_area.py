from datetime import datetime
from app import db

class ServiceZipCode(db.Model):
    """Service area ZIP code model for location validation"""
    __tablename__ = 'service_zip_codes'
    
    id = db.Column(db.Integer, primary_key=True)
    zip_code = db.Column(db.String(5), unique=True, nullable=False, index=True)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(2), default='IL')
    
    # Distance and coverage information
    distance_miles = db.Column(db.Float)  # Distance from business center
    coverage_level = db.Column(db.String(20), default='full')  # full, partial, edge
    
    # Service availability
    is_active = db.Column(db.Boolean, default=True)
    requires_confirmation = db.Column(db.Boolean, default=False)  # For edge cases
    
    # Validation tracking
    last_validated = db.Column(db.DateTime)
    validation_method = db.Column(db.String(20))  # manual, geocoding, database
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ServiceZipCode {self.zip_code} - {self.city}, {self.state}>'
    
    @property
    def display_name(self):
        """Get formatted display name"""
        return f"{self.city}, {self.state} {self.zip_code}"
    
    @property
    def coverage_color(self):
        """Get Bootstrap color class for coverage level"""
        coverage_colors = {
            'full': 'success',      # Green
            'partial': 'warning',   # Yellow  
            'edge': 'info'          # Blue
        }
        return coverage_colors.get(self.coverage_level, 'secondary')
    
    @property
    def coverage_icon(self):
        """Get icon for coverage level"""
        coverage_icons = {
            'full': 'check-circle-fill',
            'partial': 'dash-circle-fill',
            'edge': 'question-circle-fill'
        }
        return coverage_icons.get(self.coverage_level, 'circle')
    
    def update_validation(self, method='manual'):
        """Update validation timestamp and method"""
        self.last_validated = datetime.utcnow()
        self.validation_method = method
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'zip_code': self.zip_code,
            'city': self.city,
            'state': self.state,
            'distance_miles': self.distance_miles,
            'coverage_level': self.coverage_level,
            'display_name': self.display_name,
            'coverage_color': self.coverage_color,
            'coverage_icon': self.coverage_icon,
            'is_active': self.is_active,
            'requires_confirmation': self.requires_confirmation
        }

class AddressValidationCache(db.Model):
    """Cache for address validation results (privacy-preserving)"""
    __tablename__ = 'address_validation_cache'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Privacy-preserving hash of full address
    address_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    
    # Validation results
    within_range = db.Column(db.Boolean, nullable=False)
    distance_miles = db.Column(db.Float)
    validation_method = db.Column(db.String(20))  # zip_code, geocoding
    
    # Usage tracking
    hit_count = db.Column(db.Integer, default=1)
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Automatic cleanup
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)  # For automatic cache cleanup
    
    def __repr__(self):
        return f'<AddressValidation {self.address_hash[:8]}... within_range={self.within_range}>'
    
    @classmethod
    def get_validation_result(cls, address):
        """Get cached validation result for an address"""
        import hashlib
        address_hash = hashlib.sha256(address.lower().strip().encode()).hexdigest()
        
        cache_entry = cls.query.filter_by(address_hash=address_hash).first()
        if cache_entry:
            # Update access tracking
            cache_entry.hit_count += 1
            cache_entry.last_accessed = datetime.utcnow()
            db.session.commit()
            
            return {
                'within_range': cache_entry.within_range,
                'distance_miles': cache_entry.distance_miles,
                'method': cache_entry.validation_method,
                'cached': True
            }
        
        return None
    
    @classmethod
    def cache_validation_result(cls, address, within_range, distance_miles=None, method='unknown'):
        """Cache a validation result"""
        import hashlib
        from datetime import timedelta
        
        address_hash = hashlib.sha256(address.lower().strip().encode()).hexdigest()
        
        # Check if already exists
        existing = cls.query.filter_by(address_hash=address_hash).first()
        if existing:
            # Update existing entry
            existing.within_range = within_range
            existing.distance_miles = distance_miles
            existing.validation_method = method
            existing.hit_count += 1
            existing.last_accessed = datetime.utcnow()
            existing.expires_at = datetime.utcnow() + timedelta(days=30)
        else:
            # Create new entry
            cache_entry = cls(
                address_hash=address_hash,
                within_range=within_range,
                distance_miles=distance_miles,
                validation_method=method,
                expires_at=datetime.utcnow() + timedelta(days=30)
            )
            db.session.add(cache_entry)
        
        db.session.commit()
    
    @classmethod
    def cleanup_expired(cls):
        """Remove expired cache entries"""
        expired_entries = cls.query.filter(cls.expires_at < datetime.utcnow()).all()
        for entry in expired_entries:
            db.session.delete(entry)
        db.session.commit()
        return len(expired_entries)

# Coverage level constants
COVERAGE_LEVELS = [
    'full',     # Fully within service area
    'partial',  # Partially within service area  
    'edge'      # Edge case, requires confirmation
]

# Validation method constants
VALIDATION_METHODS = [
    'manual',      # Manually added
    'zip_code',    # ZIP code lookup
    'geocoding',   # Google Geocoding API
    'database'     # Database import
] 