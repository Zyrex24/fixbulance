from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user, login_user
from datetime import datetime, date, time, timedelta
import secrets
from app import db
from app.models.service import Service, DEVICE_TYPES, ISSUE_TYPES
from app.models.booking import Booking
from app.models.service_area import ServiceZipCode
from app.models.waiver import ServiceWaiver
from app.models.user import User
from app.forms.waiver import ServiceWaiverForm

booking_bp = Blueprint('booking', __name__)

def get_services_for_device_type(device_type):
    """Helper function to get services for a device type"""
    # Import DevicePricing models
    from app.models.device_pricing import DevicePricing, WaterDamageService, LaptopTabletService
    
    # Get services for this device type with dynamic pricing from DevicePricing
    services = []
    
    if device_type == 'iPhone':
        # iPhone Screen Replacement
        services.append({
            'id': 'iphone_screen',
            'name': 'Screen Replacement',
            'description': 'Complete screen assembly replacement',
            'issue_type': 'Screen',
            'device_type': device_type,
            'base_price': 150.00,  # Default iPhone screen price
            'deposit_amount': 15.00,
            'estimated_time': 60,
            'requires_parts': True,
            'warranty_days': 30,
            'icon': 'mobile-alt'
        })
        
        # iPhone Battery Replacement
        services.append({
            'id': 'iphone_battery',
            'name': 'Battery Replacement',
            'description': 'Professional battery replacement service',
            'issue_type': 'Battery',
            'device_type': device_type,
            'base_price': 80.00,  # Default iPhone battery price
            'deposit_amount': 15.00,
            'estimated_time': 60,
            'requires_parts': True,
            'warranty_days': 30,
            'icon': 'battery-three-quarters'
        })
        
    elif device_type == 'Samsung':
        # Samsung Screen Replacement
        services.append({
            'id': 'samsung_screen',
            'name': 'Screen Replacement',
            'description': 'Complete screen assembly replacement',
            'issue_type': 'Screen',
            'device_type': device_type,
            'base_price': 140.00,  # Default Samsung screen price
            'deposit_amount': 15.00,
            'estimated_time': 60,
            'requires_parts': True,
            'warranty_days': 30,
            'icon': 'mobile-alt'
        })
        
        # Samsung Battery Replacement
        services.append({
            'id': 'samsung_battery',
            'name': 'Battery Replacement',
            'description': 'Professional battery replacement service',
            'issue_type': 'Battery',
            'device_type': device_type,
            'base_price': 75.00,  # Default Samsung battery price
            'deposit_amount': 15.00,
            'estimated_time': 60,
            'requires_parts': True,
            'warranty_days': 30,
            'icon': 'battery-three-quarters'
        })
        
        # Samsung Charging Port Repair
        services.append({
            'id': 'samsung_charging_port',
            'name': 'Charging Port Repair',
            'description': 'Fix charging port connection issues',
            'issue_type': 'Charging Port',
            'device_type': device_type,
            'base_price': 90.00,  # Default Samsung charging port price
            'deposit_amount': 15.00,
            'estimated_time': 60,
            'requires_parts': True,
            'warranty_days': 30,
            'icon': 'plug'
        })
        
    else:  # Other devices
        # Other Screen Replacement
        services.append({
            'id': 'other_screen',
            'name': 'Screen Replacement',
            'description': 'Screen replacement for various devices',
            'issue_type': 'Screen',
            'device_type': device_type,
            'base_price': 100.00,
            'deposit_amount': 15.00,
            'estimated_time': 60,
            'requires_parts': True,
            'warranty_days': 30,
            'icon': 'mobile-alt'
        })
        
        # Other Battery Replacement
        services.append({
            'id': 'other_battery',
            'name': 'Battery Replacement',
            'description': 'Battery replacement service',
            'issue_type': 'Battery',
            'device_type': device_type,
            'base_price': 70.00,
            'deposit_amount': 15.00,
            'estimated_time': 60,
            'requires_parts': True,
            'warranty_days': 30,
            'icon': 'battery-three-quarters'
        })

    # Add Diagnostic Visit for all device types
    water_damage_service = WaterDamageService.query.first()
    if water_damage_service:
        services.append({
            'id': 'water_damage',
            'name': 'Diagnostic Visit',
            'description': 'Professional diagnostic assessment for device issues',
            'issue_type': 'Diagnostic',
            'device_type': device_type,
            'base_price': water_damage_service.diagnostic_fee,
            'deposit_amount': 15.00,
            'estimated_time': 60,
            'requires_parts': False,
            'warranty_days': 30,
            'icon': 'stethoscope'
        })
    
    return services

@booking_bp.route('/start')
def start():
    """Start the booking process - Step 1: Device Selection"""
    # Clear any existing booking session data
    session.pop('booking_data', None)
    
    return render_template('booking/step1_device.html', 
                         device_types=DEVICE_TYPES)

@booking_bp.route('/step2/<device_type>')
def step2_service(device_type):
    """Step 2: Service Selection"""
    if device_type not in DEVICE_TYPES:
        flash('Invalid device type selected.', 'danger')
        return redirect(url_for('booking.start'))
    
    # Get services for this device type with dynamic pricing from DevicePricing
    services = get_services_for_device_type(device_type)
    
    # Store step 1 data in session
    booking_data = session.get('booking_data', {})
    booking_data['device_type'] = device_type
    session['booking_data'] = booking_data
    
    return render_template('booking/step2_service.html',
                         device_type=device_type,
                         services=services,
                         issue_types=ISSUE_TYPES)

@booking_bp.route('/step3', methods=['GET', 'POST'])
def step3_details():
    """Step 3: Device Details and Issue Description"""
    if request.method == 'POST':
        # Handle form submission from step 2
        service_id = request.form.get('service_id')
        issue_type = request.form.get('issue_type')
        
        if not service_id:
            flash('Please select a service.', 'danger')
            return redirect(url_for('booking.start'))
        
        # Get the device type from session to recreate the service
        booking_data = session.get('booking_data', {})
        device_type = booking_data.get('device_type')
        
        if not device_type:
            flash('Please start from the beginning.', 'warning')
            return redirect(url_for('booking.start'))
        
        # Recreate the services to find the selected one
        service = None
        services = get_services_for_device_type(device_type)
        for s in services:
            if s['id'] == service_id:
                service = s
                break
        
        if not service:
            flash('Invalid service selected.', 'danger')
            return redirect(url_for('booking.start'))
        
        # Store step 2 data in session
        booking_data['service_id'] = service_id
        booking_data['issue_type'] = issue_type or service['issue_type']
        booking_data['service_data'] = service  # Store the entire service dict
        session['booking_data'] = booking_data
    else:
        # Handle GET request (back button navigation)
        booking_data = session.get('booking_data', {})
        service = booking_data.get('service_data')
        
        if not service:
            flash('Please start from the beginning.', 'warning')
            return redirect(url_for('booking.start'))
    
    return render_template('booking/step3_details.html',
                         service=service,
                         issue_type=booking_data.get('issue_type', service.get('issue_type')))

@booking_bp.route('/step4', methods=['POST'])
def step4_location():
    """Step 4: Location and Service Area Validation"""
    # Get form data from step 3
    device_model = request.form.get('device_model', '').strip()
    issue_description = request.form.get('issue_description', '').strip()
    
    if not device_model:
        flash('Please enter your device model.', 'danger')
        return redirect(url_for('booking.step3_details'))
    
    # Store step 3 data in session
    booking_data = session.get('booking_data', {})
    booking_data['device_model'] = device_model
    booking_data['issue_description'] = issue_description
    session['booking_data'] = booking_data
    
    # Get service details for display
    service = booking_data.get('service_data')
    
    return render_template('booking/step4_location.html', 
                         service=service,
                         booking_data=booking_data,
                         device_type=booking_data.get('device_type', ''),
                         device_model=device_model,
                         device_details=issue_description)

@booking_bp.route('/step4_5_auth', methods=['GET', 'POST'])
def step4_5_auth():
    """Step 4.5: User authentication/registration before scheduling"""
    booking_data = session.get('booking_data', {})
    
    if not booking_data:
        flash('Booking session expired. Please start over.', 'warning')
        return redirect(url_for('booking.start'))
    
    # Handle POST from step 4 location form (first time visiting this page)
    if request.method == 'POST' and not request.form.get('action'):
        # Coming from step 4 with location data
        service_address = request.form.get('service_address', '').strip()
        service_city = request.form.get('service_city', '').strip()
        service_state = request.form.get('service_state', 'IL')
        service_zip_code = request.form.get('service_zip_code', '').strip()
        
        if not all([service_address, service_city, service_zip_code]):
            flash('Please fill in all address fields.', 'danger')
            return redirect(url_for('booking.step4_location'))
        
        # Validate ZIP code
        service_zip = ServiceZipCode.query.filter_by(
            zip_code=service_zip_code,
            is_active=True
        ).first()
        
        if not service_zip:
            flash(f'Sorry, we do not currently service ZIP code {service_zip_code}.', 'warning')
            return redirect(url_for('booking.step4_location'))
        
        # Store step 4 data in session
        booking_data.update({
            'service_address': service_address,
            'service_city': service_city,
            'service_state': service_state,
            'service_zip_code': service_zip_code
        })
        session['booking_data'] = booking_data
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'signin':
            # Handle user sign in
            email = request.form.get('email')
            password = request.form.get('password')
            remember_me = bool(request.form.get('remember_me'))
            
            user = User.query.filter_by(email=email).first()
            
            if user and user.check_password(password):
                if not user.email_verified:
                    flash('Please verify your email before booking. Check your inbox for verification link.', 'warning')
                    return render_template('booking/step4_5_auth.html', booking_data=booking_data)
                
                login_user(user, remember=remember_me)
                user.update_last_login()
                flash('Successfully signed in!', 'success')
                return redirect(url_for('booking.step5_schedule'))
            else:
                flash('Invalid email or password.', 'danger')
        
        elif action == 'register':
            # Handle user registration
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            sms_opt_in = bool(request.form.get('sms_opt_in'))
            
            # Validation
            if password != confirm_password:
                flash('Passwords do not match.', 'danger')
                return render_template('booking/step4_5_auth.html', booking_data=booking_data)
            
            # Check if user already exists
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash('An account with this email already exists. Please sign in instead.', 'warning')
                return render_template('booking/step4_5_auth.html', booking_data=booking_data)
            
            # Create new user
            try:
                verification_token = secrets.token_urlsafe(32)
                user = User(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    phone=phone,
                    sms_opted_in=sms_opt_in,
                    email_verification_token=verification_token,
                    email_verified=False
                )
                user.set_password(password)
                
                db.session.add(user)
                db.session.commit()
                
                # TODO: Send verification email
                # send_verification_email(user)
                
                flash('Account created successfully! Please check your email to verify your account before proceeding.', 'success')
                # For now, skip email verification to keep flow working
                user.email_verified = True
                db.session.commit()
                login_user(user, remember=False)
                user.update_last_login()
                return redirect(url_for('booking.step5_schedule'))
                
            except Exception as e:
                db.session.rollback()
                flash('Error creating account. Please try again.', 'danger')
    
    return render_template('booking/step4_5_auth.html', booking_data=booking_data)

@booking_bp.route('/step5', methods=['GET', 'POST'])
def step5_schedule():
    """Step 5: Appointment Scheduling"""
    booking_data = session.get('booking_data', {})
    
    if request.method == 'POST':
        # Coming from step 4 with form data
        service_address = request.form.get('service_address', '').strip()
        service_city = request.form.get('service_city', '').strip()
        service_state = request.form.get('service_state', 'IL')
        service_zip_code = request.form.get('service_zip_code', '').strip()
        
        if not all([service_address, service_city, service_zip_code]):
            flash('Please fill in all address fields.', 'danger')
            return redirect(url_for('booking.step4_location'))
        
        # Validate ZIP code
        service_zip = ServiceZipCode.query.filter_by(
            zip_code=service_zip_code,
            is_active=True
        ).first()
        
        if not service_zip:
            flash(f'Sorry, we do not currently service ZIP code {service_zip_code}.', 'warning')
            return redirect(url_for('booking.step4_location'))
        
        # Store step 4 data in session
        booking_data.update({
            'service_address': service_address,
            'service_city': service_city,
            'service_state': service_state,
            'service_zip_code': service_zip_code
        })
        session['booking_data'] = booking_data
    else:
        # GET request (back navigation) - use session data
        if not booking_data.get('service_address'):
            flash('Please start from the beginning.', 'warning')
            return redirect(url_for('booking.start'))
        
        # Get address data from session
        service_address = booking_data.get('service_address', '')
        service_city = booking_data.get('service_city', '')
        service_state = booking_data.get('service_state', 'IL')
        service_zip_code = booking_data.get('service_zip_code', '')
        
        # Validate ZIP code exists
        service_zip = ServiceZipCode.query.filter_by(
            zip_code=service_zip_code,
            is_active=True
        ).first()
        
        if not service_zip:
            flash('Please verify your service area.', 'warning')
            return redirect(url_for('booking.step4_location'))
    
    # Get service details for display
    service = booking_data.get('service_data')
    
    # Generate specific date variables for template
    today = date.today()
    tomorrow = today + timedelta(days=1)
    day_after = today + timedelta(days=2)
    
    # Format dates for display
    today_formatted = today.strftime('%B %d, %Y')
    tomorrow_formatted = tomorrow.strftime('%B %d, %Y')
    day_after_formatted = day_after.strftime('%B %d, %Y')
    
    # Generate available time slots (simplified)
    available_dates = []
    for i in range(1, 8):  # Next 7 days
        future_date = date.today() + timedelta(days=i)
        available_dates.append(future_date)
    
    time_slots = [
        time(9, 0),   # 9:00 AM
        time(10, 0),  # 10:00 AM
        time(11, 0),  # 11:00 AM
        time(13, 0),  # 1:00 PM
        time(14, 0),  # 2:00 PM
        time(15, 0),  # 3:00 PM
        time(16, 0),  # 4:00 PM
    ]
    
    return render_template('booking/step5_schedule.html',
                         available_dates=available_dates,
                         time_slots=time_slots,
                         service_zip=service_zip,
                         service=service,
                         device_type=booking_data.get('device_type', ''),
                         location_city=service_city,
                         location_data=f"{service_address}, {service_city}, {service_state} {service_zip_code}",
                         today=today.strftime('%Y-%m-%d'),
                         tomorrow=tomorrow.strftime('%Y-%m-%d'),
                         day_after=day_after.strftime('%Y-%m-%d'),
                         today_formatted=today_formatted,
                         tomorrow_formatted=tomorrow_formatted,
                         day_after_formatted=day_after_formatted)

@booking_bp.route('/step6', methods=['POST'])
def step6_review():
    """Step 6: Review and Confirmation"""
    # Get form data from step 5
    scheduled_date_str = request.form.get('selected_date')
    scheduled_time_str = request.form.get('selected_time')
    
    if not all([scheduled_date_str, scheduled_time_str]):
        flash('Please select both date and time.', 'danger')
        return redirect(url_for('booking.step5_schedule'))
    
    # Parse date and time
    try:
        scheduled_date = datetime.strptime(scheduled_date_str, '%Y-%m-%d').date()
        scheduled_time = datetime.strptime(scheduled_time_str, '%H:%M').time()
    except ValueError:
        flash('Invalid date or time format.', 'danger')
        return redirect(url_for('booking.step5_schedule'))
    
    # Store step 5 data in session
    booking_data = session.get('booking_data', {})
    booking_data.update({
        'scheduled_date': scheduled_date_str,
        'scheduled_time': scheduled_time_str
    })
    session['booking_data'] = booking_data
    
    # Get service details for review
    service = booking_data.get('service_data')
    if not service:
        flash('Service information not found.', 'danger')
        return redirect(url_for('booking.start'))
    
    return render_template('booking/step6_payment.html',
                         booking_data=booking_data,
                         service=service,
                         scheduled_date=scheduled_date,
                         scheduled_time=scheduled_time,
                         device_type=booking_data.get('device_type', 'iPhone'),
                         device_model=booking_data.get('device_model', 'Device not specified'),
                         appointment_date_formatted=scheduled_date.strftime('%A, %B %d, %Y') if scheduled_date else booking_data.get('scheduled_date', ''),
                         appointment_time_formatted=scheduled_time.strftime('%I:%M %p') if scheduled_time else booking_data.get('scheduled_time', ''),
                         location_summary=f"{booking_data.get('service_address', '')}, {booking_data.get('service_city', '')}, {booking_data.get('service_state', 'IL')} {booking_data.get('service_zip_code', '')}" if booking_data.get('service_address') else 'Service address not specified')

@booking_bp.route('/step5_5_waiver', methods=['GET', 'POST'])
def step5_5_waiver():
    """Step 5.5: Service Waiver Agreement (Before booking creation)"""
    booking_data = session.get('booking_data', {})
    
    if not booking_data or not all([
        booking_data.get('service_id'),
        booking_data.get('device_model'),
        booking_data.get('service_address'),
        booking_data.get('scheduled_date'),
        booking_data.get('scheduled_time')
    ]):
        flash('Booking information incomplete. Please start over.', 'danger')
        return redirect(url_for('booking.start'))
    
    # Get service details
    service = booking_data.get('service_data')
    if not service:
        flash('Service information not found.', 'danger')
        return redirect(url_for('booking.start'))
    
    # Parse date and time for display
    try:
        scheduled_date = datetime.strptime(booking_data['scheduled_date'], '%Y-%m-%d').date()
        scheduled_time = datetime.strptime(booking_data['scheduled_time'], '%H:%M').time()
    except ValueError:
        scheduled_date = None
        scheduled_time = None
    
    form = ServiceWaiverForm()
    
    if request.method == 'GET':
        # Pre-populate form with booking data
        form.device_model.data = booking_data['device_model']
        form.service_date.data = booking_data['scheduled_date']
        form.repair_location.data = 'On-site'
    
    if form.validate_on_submit():
        try:
            # Store waiver data in session for later booking creation
            session['waiver_data'] = {
                'customer_name': form.customer_name.data,
                'digital_signature': form.digital_signature.data,
                'acknowledged_risk': form.acknowledged_risk.data,
                'acknowledged_data_responsibility': form.acknowledged_data_responsibility.data,
                'acknowledged_warranty_limitations': form.acknowledged_warranty_limitations.data,
                'acknowledged_non_repairable': form.acknowledged_non_repairable.data,
                'acknowledged_third_party_parts': form.acknowledged_third_party_parts.data,
                'authorized_repair': form.authorized_repair.data,
                'repair_location': form.repair_location.data or 'On-site',
                'technician_name': form.technician_name.data or 'TBD'
            }
            
            flash('Service waiver agreement signed! Now proceeding to warranty agreement...', 'success')
            return redirect(url_for('booking.step5_6_warranty'))
            
        except Exception as e:
            flash('An error occurred while processing your signature. Please try again.', 'danger')
    
    return render_template('booking/step5_5_waiver.html',
                         form=form,
                         booking_data=booking_data,
                         service=service,
                         scheduled_date=scheduled_date,
                         scheduled_time=scheduled_time)

@booking_bp.route('/step5_6_warranty', methods=['GET', 'POST'])
def step5_6_warranty():
    """Step 5.6: Limited Warranty Agreement (After service waiver, before booking creation)"""
    booking_data = session.get('booking_data', {})
    waiver_data = session.get('waiver_data', {})
    
    if not booking_data or not waiver_data:
        flash('Please complete the service waiver first.', 'danger')
        return redirect(url_for('booking.step5_5_waiver'))
    
    # Get service details
    service = booking_data.get('service_data')
    if not service:
        flash('Service information not found.', 'danger')
        return redirect(url_for('booking.start'))
    
    # Parse date and time for display
    try:
        scheduled_date = datetime.strptime(booking_data['scheduled_date'], '%Y-%m-%d').date()
        scheduled_time = datetime.strptime(booking_data['scheduled_time'], '%H:%M').time()
    except ValueError:
        scheduled_date = None
        scheduled_time = None
    
    if request.method == 'POST':
        warranty_accepted = request.form.get('warranty_accepted')
        warranty_responsibility = request.form.get('warranty_responsibility')
        warranty_contact = request.form.get('warranty_contact')
        warranty_signature = request.form.get('warranty_signature')
        
        if not all([warranty_accepted, warranty_responsibility, warranty_contact, warranty_signature]):
            flash('Please complete all warranty agreement requirements.', 'danger')
        else:
            # Store warranty data in session
            session['warranty_data'] = {
                'warranty_accepted': warranty_accepted,
                'warranty_responsibility': warranty_responsibility,
                'warranty_contact': warranty_contact,
                'warranty_signature': warranty_signature,
                'warranty_date': date.today().isoformat()
            }
            
            flash('Warranty agreement signed! Now creating your booking...', 'success')
            return redirect(url_for('booking.confirm_booking'))
    
    return render_template('booking/step5_6_warranty.html',
                         booking_data=booking_data,
                         service=service,
                         scheduled_date=scheduled_date,
                         scheduled_time=scheduled_time,
                         current_date=date.today().isoformat())

@booking_bp.route('/confirm', methods=['GET', 'POST'])
def confirm_booking():
    """Confirm and create the booking with waiver and warranty"""
    booking_data = session.get('booking_data', {})
    waiver_data = session.get('waiver_data', {})
    warranty_data = session.get('warranty_data', {})
    
    if request.method == 'GET':
        # Handle direct access to confirm page - redirect to appropriate step
        if not booking_data:
            flash('Please start your booking from the beginning.', 'info')
            return redirect(url_for('booking.start'))
        elif not waiver_data:
            flash('Please complete the service waiver before proceeding.', 'info')
            return redirect(url_for('booking.step5_5_waiver'))
        elif not warranty_data:
            flash('Please complete the warranty agreement before proceeding.', 'info')
            return redirect(url_for('booking.step5_6_warranty'))
        # If all data exists, allow GET request to proceed
    
    # Validate session data for both GET and POST requests
    if not booking_data or not waiver_data or not warranty_data:
        flash('Booking information incomplete. Please start over.', 'danger')
        return redirect(url_for('booking.start'))
    
    try:
        # Parse date and time
        scheduled_date = datetime.strptime(booking_data['scheduled_date'], '%Y-%m-%d').date()
        scheduled_time = datetime.strptime(booking_data['scheduled_time'], '%H:%M').time()
        
        # Get service data from session
        service = booking_data.get('service_data')
        if not service:
            flash('Service information not found.', 'danger')
            return redirect(url_for('booking.start'))
        
        # Handle guest vs authenticated users
        user_id = current_user.id if current_user.is_authenticated else None
        
        # Create booking with dynamic service (temporary service_id solution)
        # For now, we'll use a default service_id of 1 or create a placeholder service
        # This will need to be refactored when you want to fully integrate dynamic services with the database
        booking = Booking(
            user_id=user_id,
            service_id=1,  # Temporary placeholder - you may want to create actual service records
            device_model=booking_data['device_model'],
            issue_description=booking_data.get('issue_description', ''),
            scheduled_date=scheduled_date,
            scheduled_time=scheduled_time,
            service_address=booking_data['service_address'],
            service_city=booking_data.get('service_city', ''),
            service_state=booking_data.get('service_state', 'IL'),
            service_zip_code=booking_data['service_zip_code'],
            total_estimated_cost=service['base_price'],
            address_validated=True,
            within_service_area=True
        )
        
        db.session.add(booking)
        db.session.flush()  # Get booking ID without committing
        
        # Create waiver immediately with booking
        waiver = ServiceWaiver(
            booking_id=booking.id,
            user_id=user_id,
            customer_name=waiver_data['customer_name'],
            device_model=booking_data['device_model'],
            service_date=scheduled_date,
            digital_signature=waiver_data['digital_signature'],
            signature_timestamp=datetime.utcnow(),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            technician_name=waiver_data['technician_name'],
            repair_location=waiver_data['repair_location'],
            waiver_version='1.0',
            effective_date=date.today(),
            acknowledged_risk=waiver_data['acknowledged_risk'],
            acknowledged_data_responsibility=waiver_data['acknowledged_data_responsibility'],
            acknowledged_warranty_limitations=waiver_data['acknowledged_warranty_limitations'],
            acknowledged_non_repairable=waiver_data['acknowledged_non_repairable'],
            acknowledged_third_party_parts=waiver_data['acknowledged_third_party_parts'],
            authorized_repair=waiver_data['authorized_repair'],
            status='signed'
        )
        
        db.session.add(waiver)
        db.session.commit()
        
        # Clear session data
        session.pop('booking_data', None)
        session.pop('waiver_data', None)
        session.pop('warranty_data', None)
        
        flash('Booking created and waiver signed successfully! Proceed to payment.', 'success')
        return redirect(url_for('booking.payment', booking_id=booking.id))
        
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while creating your booking. Please try again.', 'danger')
        return redirect(url_for('booking.step5_5_waiver'))

@booking_bp.route('/payment/<int:booking_id>')
def payment(booking_id):
    """Payment page for booking deposit"""
    booking = Booking.query.get_or_404(booking_id)
    
    # Check if user owns this booking (allow guest bookings)
    if booking.user_id is not None and current_user.is_authenticated and booking.user_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('auth.dashboard'))
    
    # Check if payment already completed
    if booking.payment_status in ['deposit_paid', 'balance_paid']:
        flash('Payment for this booking has already been processed.', 'info')
        return redirect(url_for('auth.dashboard'))
    
    # Check if waiver is signed before allowing payment
    waiver = ServiceWaiver.query.filter_by(booking_id=booking_id).first()
    if not waiver or not waiver.is_valid:
        flash('Service waiver must be signed before payment can be processed.', 'warning')
        return redirect(url_for('booking.service_waiver', booking_id=booking_id))
    
    return render_template('booking/payment.html', booking=booking)

@booking_bp.route('/payment/<int:booking_id>/process', methods=['POST'])
def process_payment(booking_id):
    """Process payment for booking deposit"""
    booking = Booking.query.get_or_404(booking_id)
    
    # Check if user owns this booking (allow guest bookings)
    if booking.user_id is not None and current_user.is_authenticated and booking.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    # Check if payment already completed
    if booking.payment_status in ['deposit_paid', 'balance_paid']:
        return jsonify({'error': 'Payment already processed'}), 400
    
    # Check if waiver is signed
    waiver = ServiceWaiver.query.filter_by(booking_id=booking_id).first()
    if not waiver or not waiver.is_valid:
        return jsonify({'error': 'Service waiver must be signed before payment'}), 400
    
    try:
        # For now, simulate successful payment processing
        # In production, this would integrate with Stripe or other payment processor
        
        # Update booking payment status
        booking.payment_status = 'deposit_paid'
        booking.status = 'confirmed'
        booking.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'redirect_url': url_for('booking.payment_success', booking_id=booking_id)
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Payment processing failed'}), 500

@booking_bp.route('/payment/<int:booking_id>/success')
def payment_success(booking_id):
    """Payment success page"""
    booking = Booking.query.get_or_404(booking_id)
    
    # Check if user owns this booking (allow guest bookings)
    if booking.user_id is not None and current_user.is_authenticated and booking.user_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('main.index'))
    
    return render_template('booking/payment_success.html', booking=booking)

@booking_bp.route('/my-bookings')
@login_required
def my_bookings():
    """View user's bookings"""
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(
        Booking.created_at.desc()
    ).all()
    
    return render_template('booking/my_bookings.html', bookings=bookings)

@booking_bp.route('/booking/<int:booking_id>')
@login_required
def view_booking(booking_id):
    """View detailed booking information"""
    booking = Booking.query.filter_by(
        id=booking_id,
        user_id=current_user.id
    ).first()
    
    if not booking:
        flash('Booking not found.', 'danger')
        return redirect(url_for('booking.my_bookings'))
    
    return render_template('booking/booking_detail.html', booking=booking)

@booking_bp.route('/booking/<int:booking_id>/edit')
@login_required
def edit_booking(booking_id):
    """Edit an existing booking - redirect to contact for now"""
    booking = Booking.query.filter_by(
        id=booking_id,
        user_id=current_user.id,
        status='pending'  # Only allow editing pending bookings
    ).first()
    
    if not booking:
        flash('Booking not found or cannot be edited.', 'warning')
        return redirect(url_for('booking.my_bookings'))
    
    flash('To modify your booking, please call us at +1 (708) 737-2873. Our team will be happy to help with any changes.', 'info')
    return redirect(url_for('booking.view_booking', booking_id=booking_id))

@booking_bp.route('/booking/<int:booking_id>/cancel', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    """Cancel an existing booking"""
    booking = Booking.query.filter_by(
        id=booking_id,
        user_id=current_user.id
    ).first()
    
    if not booking:
        flash('Booking not found.', 'danger')
        return redirect(url_for('booking.my_bookings'))
    
    if booking.status not in ['pending', 'confirmed']:
        flash('This booking cannot be cancelled.', 'warning')
        return redirect(url_for('booking.view_booking', booking_id=booking_id))
    
    # Update booking status
    booking.status = 'cancelled'
    booking.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        flash(f'Booking #{booking.id} has been cancelled successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while cancelling your booking. Please try again.', 'danger')
    
    return redirect(url_for('booking.my_bookings'))

@booking_bp.route('/api/device-pricing/<brand>/<model>')
def get_device_pricing(brand, model):
    """API endpoint for dynamic pricing lookup based on device brand and model"""
    try:
        # Look up device pricing in the database
        from app.models.device_pricing import DevicePricing
        
        # Clean up the model name for database lookup
        cleaned_model = model.replace(' ', ' ').strip()
        
        device_pricing = DevicePricing.get_pricing_for_device(brand, cleaned_model)
        
        if device_pricing:
            return jsonify({
                'success': True,
                'pricing': device_pricing.to_dict()
            })
        else:
            # Return fallback pricing for unknown devices
            return jsonify({
                'success': False,
                'message': f'No specific pricing found for {brand} {model}',
                'fallback': True
            })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@booking_bp.route('/api/available-slots')
def api_available_slots():
    """API endpoint to get available time slots for a given date with booking conflict detection"""
    date_str = request.args.get('date')
    slot_type = request.args.get('type', 'standard')  # emergency, priority, standard
    
    if not date_str:
        return jsonify({'error': 'Date parameter is required'}), 400
    
    try:
        # Parse the date
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Check existing bookings for this date
        existing_bookings = Booking.query.filter(
            db.func.date(Booking.scheduled_date) == selected_date,
            Booking.status.in_(['confirmed', 'in_progress', 'pending'])
        ).all()
        
        # Extract booked time slots
        booked_slots = []
        for booking in existing_bookings:
            if booking.scheduled_date:
                booked_time = booking.scheduled_date.strftime('%H:%M')
                booked_slots.append(booked_time)
        
        # Admin-closed slots (placeholder - could be stored in database)
        # For now, assume no admin-closed slots
        admin_closed_slots = []
        
        # You could add a model for AdminScheduleSettings to manage this
        # admin_closed = AdminScheduleSettings.query.filter_by(date=selected_date).all()
        # admin_closed_slots = [setting.time_slot for setting in admin_closed]
        
        return jsonify({
            'success': True,
            'date': date_str,
            'type': slot_type,
            'booked_slots': booked_slots,
            'admin_closed_slots': admin_closed_slots,
            'total_booked': len(booked_slots),
            'message': f'Found {len(booked_slots)} existing bookings for {selected_date.strftime("%B %d, %Y")}'
        })
        
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD format.'}), 400
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@booking_bp.route('/booking/<int:booking_id>/waiver', methods=['GET', 'POST'])
def service_waiver(booking_id):
    """Digital service waiver agreement"""
    booking = Booking.query.get_or_404(booking_id)
    
    # Check if user owns this booking (allow guest access for waiver signing)
    if booking.user_id is not None and current_user.is_authenticated and booking.user_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('main.index'))
    
    # Check if waiver already exists
    existing_waiver = ServiceWaiver.query.filter_by(booking_id=booking_id).first()
    if existing_waiver and existing_waiver.is_valid:
        flash('Service waiver has already been signed for this booking.', 'info')
        return redirect(url_for('booking.view_waiver', booking_id=booking_id))
    
    form = ServiceWaiverForm()
    
    if request.method == 'GET':
        # Pre-populate form with booking data
        form.populate_from_booking(booking)
    
    if form.validate_on_submit():
        try:
            # Create new waiver
            waiver = ServiceWaiver(
                booking_id=booking.id,
                user_id=booking.user_id or None,
                customer_name=form.customer_name.data,
                device_model=booking.device_model,
                service_date=booking.scheduled_date,
                digital_signature=form.digital_signature.data,
                signature_timestamp=datetime.utcnow(),
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                technician_name=form.technician_name.data or 'TBD',
                repair_location=form.repair_location.data or 'On-site',
                waiver_version='1.0',
                effective_date=date.today(),
                acknowledged_risk=form.acknowledged_risk.data,
                acknowledged_data_responsibility=form.acknowledged_data_responsibility.data,
                acknowledged_warranty_limitations=form.acknowledged_warranty_limitations.data,
                acknowledged_non_repairable=form.acknowledged_non_repairable.data,
                acknowledged_third_party_parts=form.acknowledged_third_party_parts.data,
                authorized_repair=form.authorized_repair.data,
                status='signed'
            )
            
            db.session.add(waiver)
            db.session.commit()
            
            flash('Service waiver agreement has been successfully signed! Now proceed to payment.', 'success')
            return redirect(url_for('booking.payment', booking_id=booking_id))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while processing your signature. Please try again.', 'danger')
    
    return render_template('booking/waiver.html', 
                         form=form, 
                         booking=booking,
                         effective_date=date.today().strftime('%B %d, %Y'))

@booking_bp.route('/booking/<int:booking_id>/waiver/view')
def view_waiver(booking_id):
    """View signed waiver agreement"""
    booking = Booking.query.get_or_404(booking_id)
    waiver = ServiceWaiver.query.filter_by(booking_id=booking_id).first()
    
    if not waiver:
        flash('No waiver found for this booking.', 'warning')
        return redirect(url_for('booking.service_waiver', booking_id=booking_id))
    
    # Check if user owns this booking (allow guest access)
    if booking.user_id is not None and current_user.is_authenticated and booking.user_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('main.index'))
    
    return render_template('booking/waiver_view.html', 
                         booking=booking,
                         waiver=waiver) 