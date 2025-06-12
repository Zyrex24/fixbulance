from app import db
from datetime import datetime

class SystemSettings(db.Model):
    """Global system settings and configuration"""
    __tablename__ = 'system_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(50), unique=True, nullable=False)
    setting_value = db.Column(db.String(255), nullable=False)
    setting_type = db.Column(db.String(20), default='string')  # string, float, int, boolean
    description = db.Column(db.Text)
    category = db.Column(db.String(50), default='general')
    is_editable = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationship
    updated_by_user = db.relationship('User', backref='system_settings_updates')
    
    @classmethod
    def get_setting(cls, key, default=None):
        """Get a setting value by key"""
        setting = cls.query.filter_by(setting_key=key).first()
        if not setting:
            return default
        
        # Convert value based on type
        if setting.setting_type == 'float':
            return float(setting.setting_value)
        elif setting.setting_type == 'int':
            return int(setting.setting_value)
        elif setting.setting_type == 'boolean':
            return setting.setting_value.lower() in ('true', '1', 'yes', 'on')
        else:
            return setting.setting_value
    
    @classmethod
    def set_setting(cls, key, value, setting_type='string', description='', category='general', user_id=None):
        """Set a setting value"""
        setting = cls.query.filter_by(setting_key=key).first()
        
        if setting:
            setting.setting_value = str(value)
            setting.setting_type = setting_type
            setting.updated_at = datetime.utcnow()
            setting.updated_by = user_id
        else:
            setting = cls(
                setting_key=key,
                setting_value=str(value),
                setting_type=setting_type,
                description=description,
                category=category,
                updated_by=user_id
            )
            db.session.add(setting)
        
        db.session.commit()
        return setting
    
    @classmethod
    def get_base_deposit(cls):
        """Get the current base deposit amount"""
        return cls.get_setting('base_deposit_amount', 15.00)
    
    @classmethod
    def set_base_deposit(cls, amount, user_id=None):
        """Set the base deposit amount"""
        return cls.set_setting(
            'base_deposit_amount', 
            amount, 
            'float',
            'Standard deposit amount for all bookings',
            'payment',
            user_id
        )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'setting_key': self.setting_key,
            'setting_value': self.setting_value,
            'setting_type': self.setting_type,
            'description': self.description,
            'category': self.category,
            'is_editable': self.is_editable,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'updated_by': self.updated_by
        }
    
    def __repr__(self):
        return f'<SystemSettings {self.setting_key}={self.setting_value}>' 