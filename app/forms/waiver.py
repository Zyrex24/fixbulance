from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length, Regexp, ValidationError
from wtforms.widgets import CheckboxInput, TextArea

class ServiceWaiverForm(FlaskForm):
    """Digital Service Waiver Agreement Form"""
    
    # Hidden fields for pre-populated data
    booking_id = HiddenField('Booking ID')
    device_model = HiddenField('Device Model')
    service_date = HiddenField('Service Date')
    
    # Customer signature (typed name)
    customer_name = StringField(
        'Full Legal Name', 
        validators=[
            DataRequired(message="Please enter your full legal name"),
            Length(min=2, max=100, message="Name must be between 2 and 100 characters"),
            Regexp(r'^[A-Za-z\s\'-]+$', message="Name can only contain letters, spaces, hyphens, and apostrophes")
        ],
        render_kw={
            'placeholder': 'Enter your full legal name exactly as it appears on your ID',
            'class': 'form-control'
        }
    )
    
    # Digital signature confirmation
    digital_signature = StringField(
        'Digital Signature', 
        validators=[
            DataRequired(message="Please type your name again to confirm your digital signature"),
            Length(min=2, max=100, message="Signature must match your name exactly")
        ],
        render_kw={
            'placeholder': 'Type your full name again to digitally sign this agreement',
            'class': 'form-control'
        }
    )
    
    # Agreement acknowledgments
    acknowledged_risk = BooleanField(
        'I acknowledge and understand the inherent risks in device repair, including potential worsening of pre-existing damage.',
        validators=[DataRequired(message="You must acknowledge the repair risks")],
        default=False
    )
    
    acknowledged_data_responsibility = BooleanField(
        'I understand it is my responsibility to back up personal data and that Fixbulance is not liable for data loss.',
        validators=[DataRequired(message="You must acknowledge data backup responsibility")],
        default=False
    )
    
    acknowledged_warranty_limitations = BooleanField(
        'I understand the 90-day limited warranty terms and exclusions.',
        validators=[DataRequired(message="You must acknowledge warranty limitations")],
        default=False
    )
    
    acknowledged_non_repairable = BooleanField(
        'I understand that some devices may not be repairable and diagnostic fees may still apply.',
        validators=[DataRequired(message="You must acknowledge non-repairable device policy")],
        default=False
    )
    
    acknowledged_third_party_parts = BooleanField(
        'I understand that replacement parts may be original or high-quality aftermarket.',
        validators=[DataRequired(message="You must acknowledge parts policy")],
        default=False
    )
    
    authorized_repair = BooleanField(
        'I authorize Fixbulance LLC to perform diagnostics and repairs on my device and release them from liability for unforeseen damages during standard repair procedures.',
        validators=[DataRequired(message="You must authorize the repair to proceed")],
        default=False
    )
    
    # Technician information (optional, filled by technician)
    technician_name = StringField(
        'Technician Name',
        render_kw={'class': 'form-control', 'readonly': True}
    )
    
    repair_location = StringField(
        'Repair Location',
        default='On-site',
        render_kw={'class': 'form-control'}
    )
    
    submit = SubmitField('Sign Service Waiver Agreement', render_kw={'class': 'btn btn-primary btn-lg'})
    
    def validate_digital_signature(self, field):
        """Custom validator to ensure digital signature matches customer name"""
        if self.customer_name.data and field.data:
            # Normalize both names for comparison (remove extra spaces, convert to lowercase)
            customer_name_normalized = ' '.join(self.customer_name.data.split()).lower()
            signature_normalized = ' '.join(field.data.split()).lower()
            
            if customer_name_normalized != signature_normalized:
                raise ValidationError('Digital signature must match your legal name exactly.')
    
    def populate_from_booking(self, booking):
        """Pre-populate form fields from booking data"""
        if booking:
            self.booking_id.data = str(booking.id)
            self.device_model.data = booking.device_model
            self.service_date.data = booking.scheduled_date.isoformat()
            
            # The customer name will be filled by the user during signing 