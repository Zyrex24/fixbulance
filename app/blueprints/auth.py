from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from app import db, mail
from app.models.user import User
import re

auth_bp = Blueprint('auth', __name__)

def is_valid_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_valid_phone(phone):
    """Validate phone number format"""
    # Remove non-digits
    digits = re.sub(r'\D', '', phone)
    # Should be 10 digits
    return len(digits) == 10

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration with email verification setup"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        # Get form data
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        phone = request.form.get('phone', '').strip()
        
        # Validation
        errors = []
        
        if not email or not is_valid_email(email):
            errors.append('Please enter a valid email address.')
        
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters long.')
        
        if password != confirm_password:
            errors.append('Passwords do not match.')
        
        if not first_name or len(first_name) < 2:
            errors.append('First name must be at least 2 characters long.')
        
        if not last_name or len(last_name) < 2:
            errors.append('Last name must be at least 2 characters long.')
        
        if phone and not is_valid_phone(phone):
            errors.append('Please enter a valid phone number (10 digits).')
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            errors.append('An account with this email already exists.')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('auth/register.html')
        
        # Create new user
        try:
            user = User(
                email=email,
                first_name=first_name,
                last_name=last_name,
                phone=phone if phone else None
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            # Auto-login after registration
            login_user(user)
            user.update_last_login()
            
            flash('Registration successful! Welcome to our service.', 'success')
            
            # Redirect to booking if they were trying to book
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/booking'):
                return redirect(next_page)
            else:
                return redirect(url_for('auth.profile'))
        
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'danger')
            return render_template('auth/register.html')
    
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember_me = request.form.get('remember_me') == 'on'
        
        if not email or not password:
            flash('Please enter both email and password.', 'danger')
            return render_template('auth/login.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact support.', 'warning')
                return render_template('auth/login.html')
            
            login_user(user, remember=remember_me)
            user.update_last_login()
            
            flash(f'Welcome back, {user.first_name}!', 'success')
            
            # Redirect to intended page or dashboard
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            elif user.is_admin:
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('auth.dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/dashboard')
@login_required
def dashboard():
    """Customer dashboard with recent bookings"""
    # Get user's recent bookings
    recent_bookings = current_user.get_recent_bookings(limit=5)
    
    # Get booking statistics
    total_bookings = current_user.total_bookings
    completed_bookings = len([b for b in current_user.bookings if b.status == 'completed'])
    
    return render_template('auth/dashboard.html',
                         recent_bookings=recent_bookings,
                         total_bookings=total_bookings,
                         completed_bookings=completed_bookings)

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile management"""
    if request.method == 'POST':
        # Get form data
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state', '').strip()
        zip_code = request.form.get('zip_code', '').strip()
        
        # Communication preferences
        sms_opted_in = request.form.get('sms_opted_in') == 'on'
        email_notifications = request.form.get('email_notifications') == 'on'
        marketing_emails = request.form.get('marketing_emails') == 'on'
        
        # Determine which section is being updated
        section = 'personal'  # default
        if any([address, city, state, zip_code]):
            section = 'address'
        elif any([request.form.get('sms_opted_in'), request.form.get('email_notifications'), request.form.get('marketing_emails')]):
            section = 'notifications'
        
        # Validation - only validate relevant fields
        errors = []
        
        # Only validate name fields if they are being submitted (personal info section)
        if section == 'personal' or (first_name or last_name):
            if not first_name or len(first_name) < 2:
                errors.append('First name must be at least 2 characters long.')
            
            if not last_name or len(last_name) < 2:
                errors.append('Last name must be at least 2 characters long.')
        
        # Validate phone if provided
        if phone and not is_valid_phone(phone):
            errors.append('Please enter a valid phone number (10 digits).')
        
        # Validate ZIP code if provided  
        if zip_code and len(zip_code) != 5:
            errors.append('ZIP code must be 5 digits.')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('auth/profile.html')
        
        # Update user profile - only update fields that were submitted
        try:
            if first_name:
                current_user.first_name = first_name
            if last_name:
                current_user.last_name = last_name
            if 'phone' in request.form:  # Check if field was submitted
                current_user.phone = phone if phone else None
            if 'address' in request.form:
                current_user.address = address if address else None
            if 'city' in request.form:
                current_user.city = city if city else None
            if 'state' in request.form:
                current_user.state = state if state else None
            if 'zip_code' in request.form:
                current_user.zip_code = zip_code if zip_code else None
            
            # Update communication preferences if submitted
            if 'sms_opted_in' in request.form or request.form.get('sms_opted_in') == 'on':
                current_user.sms_opted_in = sms_opted_in
            if 'email_notifications' in request.form or request.form.get('email_notifications') == 'on':
                current_user.email_notifications = email_notifications
            if 'marketing_emails' in request.form or request.form.get('marketing_emails') == 'on':
                current_user.marketing_emails = marketing_emails
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating your profile.', 'danger')
    
    return render_template('auth/profile.html')

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Change user password"""
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_new_password', '')  # Fixed field name
    
    # Validation
    if not current_user.check_password(current_password):
        flash('Current password is incorrect.', 'danger')
        return redirect(url_for('auth.profile') + '#security')
    
    if len(new_password) < 6:
        flash('New password must be at least 6 characters long.', 'danger')
        return redirect(url_for('auth.profile') + '#security')
    
    if new_password != confirm_password:
        flash('New passwords do not match.', 'danger')
        return redirect(url_for('auth.profile') + '#security')
    
    # Update password
    try:
        current_user.set_password(new_password)
        db.session.commit()
        flash('Password changed successfully!', 'success')
        return redirect(url_for('auth.profile') + '#security')
    
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while changing your password.', 'danger')
        return redirect(url_for('auth.profile') + '#security')

@auth_bp.route('/sms-opt-in/<int:booking_id>')
def sms_opt_in(booking_id):
    """SMS opt-in from booking confirmation email"""
    from app.models.booking import Booking
    
    booking = Booking.query.get_or_404(booking_id)
    
    # Check if user owns this booking
    if booking.user_id != current_user.id:
        flash('Invalid booking reference.', 'danger')
        return redirect(url_for('main.index'))
    
    # Opt user into SMS notifications
    current_user.sms_opted_in = True
    db.session.commit()
    
    flash('SMS notifications enabled! You\'ll receive arrival updates and completion notifications.', 'success')
    return redirect(url_for('auth.dashboard'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password form"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email or not is_valid_email(email):
            flash('Please enter a valid email address.', 'danger')
            return render_template('auth/forgot_password.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate reset token
            token = user.generate_password_reset_token()
            
            # Send reset email
            try:
                send_password_reset_email(user, token)
                flash('Password reset instructions have been sent to your email.', 'success')
            except Exception as e:
                flash(f'Unable to send reset email: {str(e)}. Please contact support at (708) 971-4053.', 'danger')
                current_app.logger.error(f'Failed to send password reset email: {str(e)}')
        else:
            # Don't reveal if email exists or not for security
            flash('If an account with that email exists, password reset instructions have been sent.', 'info')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    # Find user with this token
    user = User.query.filter_by(password_reset_token=token).first()
    
    if not user or not user.verify_password_reset_token(token):
        flash('Invalid or expired reset token.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not password or len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('auth/reset_password.html', token=token)
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/reset_password.html', token=token)
        
        # Reset password
        user.reset_password(password)
        flash('Your password has been reset successfully. You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', token=token)

def send_password_reset_email(user, token):
    """Send password reset email"""
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    
    msg = Message(
        subject='Reset Your Fixbulance Password',
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[user.email]
    )
    
    msg.html = render_template('auth/emails/password_reset.html', 
                              user=user, 
                              reset_url=reset_url)
    
    msg.body = f"""
Hi {user.first_name},

You requested a password reset for your Fixbulance account.

Click the link below to reset your password:
{reset_url}

This link will expire in 1 hour.

If you didn't request this reset, please ignore this email.

Best regards,
Ahmed Khalil
Fixbulance Emergency Phone Repair
(708) 971-4053
info@fixbulance.com
"""
    
    mail.send(msg)

# Context processor for authentication templates
@auth_bp.context_processor
def inject_auth_data():
    """Inject common authentication data into templates"""
    return {
        'user_bookings_count': current_user.total_bookings if current_user.is_authenticated else 0
    } 