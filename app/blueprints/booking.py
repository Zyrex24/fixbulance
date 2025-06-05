from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date, time, timedelta
from app import db
from app.models.service import Service, DEVICE_TYPES, ISSUE_TYPES
from app.models.booking import Booking
from app.models.service_area import ServiceZipCode

booking_bp = Blueprint('booking', __name__)

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
    
    # Get services for this device type
    services = Service.query.filter_by(
        device_type=device_type,
        is_active=True
    ).order_by(Service.sort_order, Service.name).all()
    
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
        
        service = Service.query.get(service_id)
        if not service:
            flash('Invalid service selected.', 'danger')
            return redirect(url_for('booking.start'))
        
        # Store step 2 data in session
        booking_data = session.get('booking_data', {})
        booking_data['service_id'] = service_id
        booking_data['issue_type'] = issue_type or service.issue_type
        session['booking_data'] = booking_data
    else:
        # Handle GET request (back button navigation)
        booking_data = session.get('booking_data', {})
        service_id = booking_data.get('service_id')
        
        if not service_id:
            flash('Please start from the beginning.', 'warning')
            return redirect(url_for('booking.start'))
        
        service = Service.query.get(service_id)
        if not service:
            flash('Service information not found.', 'danger')
            return redirect(url_for('booking.start'))
    
    return render_template('booking/step3_details.html',
                         service=service,
                         issue_type=booking_data.get('issue_type', service.issue_type))

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
    service = None
    if booking_data.get('service_id'):
        service = Service.query.get(booking_data['service_id'])
    
    return render_template('booking/step4_location.html', 
                         service=service,
                         booking_data=booking_data,
                         device_type=booking_data.get('device_type', ''),
                         device_model=device_model,
                         device_details=issue_description)

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
    service = None
    if booking_data.get('service_id'):
        service = Service.query.get(booking_data['service_id'])
    
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
    service = Service.query.get(booking_data.get('service_id'))
    if not service:
        flash('Service information not found.', 'danger')
        return redirect(url_for('booking.start'))
    
    return render_template('booking/step6_payment.html',
                         booking_data=booking_data,
                         service=service,
                         scheduled_date=scheduled_date,
                         scheduled_time=scheduled_time)

@booking_bp.route('/confirm', methods=['POST'])
def confirm_booking():
    """Confirm and create the booking"""
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
    
    try:
        # Parse date and time
        scheduled_date = datetime.strptime(booking_data['scheduled_date'], '%Y-%m-%d').date()
        scheduled_time = datetime.strptime(booking_data['scheduled_time'], '%H:%M').time()
        
        # Get service
        service = Service.query.get(booking_data['service_id'])
        
        # Handle guest vs authenticated users
        user_id = current_user.id if current_user.is_authenticated else None
        
        # Create booking
        booking = Booking(
            user_id=user_id,
            service_id=service.id,
            device_model=booking_data['device_model'],
            issue_description=booking_data.get('issue_description', ''),
            scheduled_date=scheduled_date,
            scheduled_time=scheduled_time,
            service_address=booking_data['service_address'],
            service_city=booking_data.get('service_city', ''),
            service_state=booking_data.get('service_state', 'IL'),
            service_zip_code=booking_data['service_zip_code'],
            total_estimated_cost=service.base_price,
            address_validated=True,
            within_service_area=True
        )
        
        db.session.add(booking)
        db.session.commit()
        
        # Clear booking session data
        session.pop('booking_data', None)
        
        flash('Booking created successfully! Please proceed to payment.', 'success')
        return redirect(url_for('booking.payment', booking_id=booking.id))
        
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while creating your booking. Please try again.', 'danger')
        return redirect(url_for('booking.step6_review'))

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
    
    return render_template('booking/payment.html', booking=booking)

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
    """View specific booking details"""
    booking = Booking.query.get_or_404(booking_id)
    
    # Check if user owns this booking or is admin
    if booking.user_id != current_user.id and not current_user.is_admin:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('auth.dashboard'))
    
    return render_template('booking/booking_detail.html', booking=booking)

# API endpoint for checking available time slots
@booking_bp.route('/api/available-slots')
def api_available_slots():
    """Get available time slots for a specific date"""
    date_str = request.args.get('date')
    if not date_str:
        return jsonify({'error': 'Date is required'}), 400
    
    try:
        requested_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400
    
    # Get existing bookings for this date
    existing_bookings = Booking.query.filter_by(scheduled_date=requested_date).all()
    booked_times = [booking.scheduled_time.strftime('%H:%M') for booking in existing_bookings]
    
    # Available time slots
    all_slots = ['09:00', '10:00', '11:00', '13:00', '14:00', '15:00', '16:00']
    available_slots = [slot for slot in all_slots if slot not in booked_times]
    
    return jsonify({
        'date': date_str,
        'available_slots': available_slots,
        'booked_slots': booked_times
    }) 