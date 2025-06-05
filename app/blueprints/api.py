from flask import Blueprint, jsonify, request, current_app, session, url_for
from flask_login import login_required, current_user
from app.models.service import Service, DEVICE_TYPES, ISSUE_TYPES
from app.models.booking import Booking
from app.models.service_area import ServiceZipCode, AddressValidationCache
from app.models.user import User
from app.services.payment import payment_service
from app.services.communication import communication_service
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime, timedelta
import json
from sqlalchemy import and_, or_
from app import db
import hashlib
import re
from app.services.payment import payment_service

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/services')
def services():
    """Get all active services"""
    services = Service.query.filter_by(is_active=True).order_by(
        Service.device_type, Service.sort_order
    ).all()
    
    return jsonify({
        'services': [service.to_dict() for service in services],
        'device_types': DEVICE_TYPES,
        'issue_types': ISSUE_TYPES
    })

@api_bp.route('/services/<device_type>')
def services_by_device(device_type):
    """Get services for specific device type"""
    if device_type not in DEVICE_TYPES:
        return jsonify({'error': 'Invalid device type'}), 400
    
    services = Service.query.filter_by(
        device_type=device_type,
        is_active=True
    ).order_by(Service.sort_order).all()
    
    return jsonify({
        'device_type': device_type,
        'services': [service.to_dict() for service in services]
    })

@api_bp.route('/validate-address', methods=['POST'])
def validate_address():
    """Validate service address using ZIP code lookup and caching"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    zip_code = data.get('zip_code', '').strip()
    full_address = data.get('full_address', '').strip()
    
    if not zip_code:
        return jsonify({'error': 'ZIP code is required'}), 400
    
    # Clean ZIP code
    zip_code = ''.join(filter(str.isdigit, zip_code))[:5]
    
    if len(zip_code) != 5:
        return jsonify({'error': 'Invalid ZIP code format'}), 400
    
    # Check cache first if full address provided
    if full_address:
        cached_result = AddressValidationCache.get_validation_result(full_address)
        if cached_result:
            return jsonify({
                'valid': cached_result['within_range'],
                'distance_miles': cached_result['distance_miles'],
                'method': 'cached',
                'zip_code': zip_code
            })
    
    # Check ZIP code in service area
    service_zip = ServiceZipCode.query.filter_by(
        zip_code=zip_code,
        is_active=True
    ).first()
    
    if service_zip:
        result = {
            'valid': True,
            'zip_code': zip_code,
            'city': service_zip.city,
            'state': service_zip.state,
            'distance_miles': service_zip.distance_miles,
            'coverage_level': service_zip.coverage_level,
            'requires_confirmation': service_zip.requires_confirmation,
            'method': 'zip_lookup'
        }
        
        # Cache the result if full address provided
        if full_address:
            AddressValidationCache.cache_validation_result(
                full_address, True, service_zip.distance_miles, 'zip_lookup'
            )
        
        return jsonify(result)
    
    else:
        result = {
            'valid': False,
            'zip_code': zip_code,
            'message': f'Service not available in ZIP code {zip_code}',
            'method': 'zip_lookup'
        }
        
        # Cache negative result
        if full_address:
            AddressValidationCache.cache_validation_result(
                full_address, False, None, 'zip_lookup'
            )
        
        return jsonify(result)

@api_bp.route('/service-area')
def service_area_info():
    """Get service area information"""
    zip_codes = ServiceZipCode.query.filter_by(is_active=True).order_by(
        ServiceZipCode.distance_miles
    ).all()
    
    # Group by coverage level
    coverage_groups = {
        'full': [],
        'partial': [],
        'edge': []
    }
    
    for zip_code in zip_codes:
        coverage_groups[zip_code.coverage_level].append(zip_code.to_dict())
    
    return jsonify({
        'service_radius': current_app.config.get('DEFAULT_SERVICE_RADIUS', 10),
        'business_zip': current_app.config.get('BUSINESS_ZIP_CODE', '60462'),
        'coverage_areas': coverage_groups,
        'total_zip_codes': len(zip_codes)
    })

@api_bp.route('/available-slots')
def available_slots():
    """Get available appointment slots for a date"""
    date_str = request.args.get('date')
    if not date_str:
        return jsonify({'error': 'Date parameter is required'}), 400
    
    try:
        from datetime import datetime
        requested_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    
    # Get existing bookings for this date
    existing_bookings = Booking.query.filter_by(scheduled_date=requested_date).all()
    booked_times = [booking.scheduled_time.strftime('%H:%M') for booking in existing_bookings]
    
    # All possible time slots
    all_slots = [
        '09:00', '10:00', '11:00', '13:00', '14:00', '15:00', '16:00'
    ]
    
    available_slots = [slot for slot in all_slots if slot not in booked_times]
    
    return jsonify({
        'date': date_str,
        'available_slots': available_slots,
        'booked_slots': booked_times,
        'total_slots': len(all_slots),
        'available_count': len(available_slots)
    })

@api_bp.route('/booking/<int:booking_id>/status')
@login_required
def booking_status(booking_id):
    """Get current booking status"""
    booking = Booking.query.get_or_404(booking_id)
    
    # Check if user owns this booking or is admin
    if booking.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify({
        'booking_id': booking.id,
        'status': booking.status,
        'status_color': booking.status_color,
        'status_icon': booking.status_icon,
        'payment_status': booking.payment_status,
        'payment_display': booking.payment_status_display,
        'scheduled_date': booking.scheduled_date.isoformat(),
        'scheduled_time': booking.scheduled_time.isoformat(),
        'is_same_day': booking.is_same_day,
        'is_urgent': booking.is_urgent
    })

@api_bp.route('/user/communication-preferences', methods=['GET', 'POST'])
@login_required
def communication_preferences():
    """Get or update user communication preferences"""
    if request.method == 'POST':
        data = request.get_json()
        
        try:
            current_user.sms_opted_in = data.get('sms_opted_in', current_user.sms_opted_in)
            current_user.email_notifications = data.get('email_notifications', current_user.email_notifications)
            current_user.marketing_emails = data.get('marketing_emails', current_user.marketing_emails)
            
            from app import db
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Communication preferences updated',
                'preferences': {
                    'sms_opted_in': current_user.sms_opted_in,
                    'email_notifications': current_user.email_notifications,
                    'marketing_emails': current_user.marketing_emails
                }
            })
        
        except Exception as e:
            from app import db
            db.session.rollback()
            return jsonify({'error': 'Failed to update preferences'}), 500
    
    # GET request
    return jsonify({
        'preferences': {
            'sms_opted_in': current_user.sms_opted_in,
            'email_notifications': current_user.email_notifications,
            'marketing_emails': current_user.marketing_emails,
            'can_receive_sms': current_user.can_receive_sms()
        }
    })

@api_bp.route('/stats')
def public_stats():
    """Get public statistics for homepage"""
    total_services = Service.query.filter_by(is_active=True).count()
    total_zip_codes = ServiceZipCode.query.filter_by(is_active=True).count()
    total_customers = User.query.filter_by(is_admin=False).count()
    completed_repairs = Booking.query.filter_by(status='completed').count()
    
    return jsonify({
        'total_services': total_services,
        'covered_zip_codes': total_zip_codes,
        'total_customers': total_customers,
        'completed_repairs': completed_repairs,
        'service_radius': current_app.config.get('DEFAULT_SERVICE_RADIUS', 10)
    })

# Admin API endpoints
@api_bp.route('/admin/dashboard-stats')
@login_required
def admin_dashboard_stats():
    """Get dashboard statistics for admin"""
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    from datetime import date
    today = date.today()
    
    stats = {
        'total_bookings': Booking.query.count(),
        'pending_bookings': Booking.query.filter_by(status='pending').count(),
        'today_bookings': Booking.query.filter_by(scheduled_date=today).count(),
        'completed_bookings': Booking.query.filter_by(status='completed').count(),
        'total_customers': User.query.filter_by(is_admin=False).count(),
        'total_revenue': sum(
            b.final_amount or b.total_estimated_cost or 0 
            for b in Booking.query.filter_by(status='completed').all()
        )
    }
    
    return jsonify(stats)

@api_bp.route('/admin/recent-activity')
@login_required
def admin_recent_activity():
    """Get recent booking activity for admin dashboard"""
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    recent_bookings = Booking.query.order_by(
        Booking.created_at.desc()
    ).limit(10).all()
    
    return jsonify({
        'recent_bookings': [booking.to_dict() for booking in recent_bookings]
    })

# Error handlers for API
@api_bp.errorhandler(404)
def api_not_found(error):
    return jsonify({'error': 'API endpoint not found'}), 404

@api_bp.errorhandler(405)
def api_method_not_allowed(error):
    return jsonify({'error': 'Method not allowed'}), 405

@api_bp.errorhandler(500)
def api_internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# ===============================
# BOOKING WIZARD API ENDPOINTS
# ===============================

@api_bp.route('/validate-zip', methods=['POST'])
def validate_zip():
    """Validate ZIP code for service area coverage"""
    try:
        data = request.get_json()
        zip_code = data.get('zip_code', '').strip()
        
        if not zip_code:
            return jsonify({
                'success': False,
                'message': 'ZIP code is required'
            }), 400
        
        # Validate ZIP code format
        if not re.match(r'^\d{5}(-\d{4})?$', zip_code):
            return jsonify({
                'success': False,
                'message': 'Invalid ZIP code format'
            }), 400
        
        # Extract 5-digit ZIP
        zip_5 = zip_code[:5]
        
        # Check service area coverage
        service_area = ServiceZipCode.query.filter_by(zip_code=zip_5).first()
        
        if not service_area:
            return jsonify({
                'success': False,
                'coverage': 'none',
                'message': f'Sorry, we don\'t currently service {zip_code}. Our service area covers southwest Chicago suburbs within 16 miles of Orland Park, IL.',
                'distance': None,
                'coverage_level': 'none'
            })
        
        # Return coverage information
        coverage_info = {
            'success': True,
            'coverage': service_area.coverage_level,
            'distance': service_area.distance_miles,
            'coverage_level': service_area.coverage_level,
            'message': get_coverage_message(service_area)
        }
        
        return jsonify(coverage_info)
        
    except Exception as e:
        current_app.logger.error(f"ZIP validation error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Service temporarily unavailable. Please try again.'
        }), 500

def get_coverage_message(service_area):
    """Get appropriate message based on coverage level"""
    if service_area.coverage_level == 'full':
        return f"Great! We provide full emergency service to {service_area.zip_code}. Same-day emergency repairs available."
    elif service_area.coverage_level == 'partial':
        return f"We service {service_area.zip_code} with possible additional travel time. Emergency service available with extended ETA."
    elif service_area.coverage_level == 'edge':
        return f"We can service {service_area.zip_code} with confirmation required. Please call (555) 123-4567 to verify availability."
    else:
        return f"Coverage information unavailable for {service_area.zip_code}."

@api_bp.route('/services-by-device', methods=['POST'])
def get_services_by_device():
    """Get services filtered by device type"""
    try:
        data = request.get_json()
        device_type = data.get('device_type', '').strip()
        
        if not device_type:
            return jsonify({
                'success': False,
                'message': 'Device type is required'
            }), 400
        
        # Get services for the device type
        services = Service.query.filter_by(device_type=device_type, is_active=True).order_by(Service.base_price).all()
        
        services_data = []
        for service in services:
            services_data.append({
                'id': service.id,
                'name': service.name,
                'description': service.description,
                'base_price': float(service.base_price),
                'display_price': service.get_display_price(),
                'difficulty_level': service.difficulty_level,
                'estimated_time': service.estimated_time_minutes,
                'warranty_period': service.warranty_period_days,
                'device_type': service.device_type,
                'issue_type': service.issue_type
            })
        
        return jsonify({
            'success': True,
            'services': services_data,
            'count': len(services_data)
        })
        
    except Exception as e:
        current_app.logger.error(f"Services by device error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Unable to load services. Please try again.'
        }), 500

@api_bp.route('/booking/session', methods=['POST'])
def save_booking_session():
    """Save booking wizard session data"""
    try:
        data = request.get_json()
        step = data.get('step')
        step_data = data.get('data', {})
        
        if not step:
            return jsonify({
                'success': False,
                'message': 'Step is required'
            }), 400
        
        # Initialize booking session if not exists
        if 'booking_session' not in session:
            session['booking_session'] = {}
        
        # Save step data
        session['booking_session'][f'step_{step}'] = step_data
        session['booking_session']['last_step'] = step
        session['booking_session']['updated_at'] = datetime.utcnow().isoformat()
        
        # Mark session as modified
        session.modified = True
        
        return jsonify({
            'success': True,
            'message': 'Session data saved',
            'step': step
        })
        
    except Exception as e:
        current_app.logger.error(f"Booking session save error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Unable to save session data'
        }), 500

@api_bp.route('/booking/session', methods=['GET'])
def get_booking_session():
    """Get booking wizard session data"""
    try:
        booking_session = session.get('booking_session', {})
        
        return jsonify({
            'success': True,
            'session_data': booking_session
        })
        
    except Exception as e:
        current_app.logger.error(f"Booking session get error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Unable to retrieve session data'
        }), 500

@api_bp.route('/booking/create', methods=['POST'])
def create_booking():
    """Create a new booking from session data"""
    try:
        # Get session data
        booking_session = session.get('booking_session', {})
        
        if not booking_session:
            return jsonify({
                'success': False,
                'message': 'No booking session found'
            }), 400
        
        # Extract data from session
        device_data = booking_session.get('step_1', {})
        service_data = booking_session.get('step_2', {})
        details_data = booking_session.get('step_3', {})
        location_data = booking_session.get('step_4', {})
        schedule_data = booking_session.get('step_5', {})
        payment_data = booking_session.get('step_6', {})
        
        # Validate required data
        if not all([device_data.get('device_type'), service_data.get('service_id'), 
                   location_data.get('zip_code'), schedule_data.get('appointment_date')]):
            return jsonify({
                'success': False,
                'message': 'Incomplete booking information'
            }), 400
        
        # Get service
        service = Service.query.get(service_data.get('service_id'))
        if not service:
            return jsonify({
                'success': False,
                'message': 'Invalid service selected'
            }), 400
        
        # Create booking
        booking = Booking(
            # Device information
            device_type=device_data.get('device_type'),
            device_model=details_data.get('device_model', ''),
            device_color=details_data.get('device_color', ''),
            storage_capacity=details_data.get('storage_capacity', ''),
            purchase_date=details_data.get('purchase_date'),
            
            # Service information
            service_id=service.id,
            issue_description=details_data.get('issue_description', ''),
            symptoms=details_data.get('symptoms', []),
            previous_repairs=details_data.get('previous_repairs', ''),
            
            # Location information
            customer_address=location_data.get('address', ''),
            city=location_data.get('city', ''),
            state=location_data.get('state', ''),
            zip_code=location_data.get('zip_code'),
            
            # Scheduling
            preferred_date=datetime.strptime(schedule_data.get('appointment_date'), '%Y-%m-%d').date(),
            preferred_time=schedule_data.get('appointment_time'),
            appointment_type=schedule_data.get('appointment_type', 'standard'),
            
            # Pricing
            service_price=service.base_price,
            deposit_amount=15.00,  # Standard $15 deposit
            
            # Customer information
            customer_name=payment_data.get('customer_name', ''),
            customer_email=payment_data.get('customer_email', ''),
            customer_phone=payment_data.get('customer_phone', ''),
            
            # Status
            status='pending',
            payment_status='deposit_pending',
            
            # User association
            user_id=current_user.id if current_user.is_authenticated else None
        )
        
        # Generate unique booking reference
        booking.generate_reference()
        
        # Save to database
        db.session.add(booking)
        db.session.commit()
        
        # Clear booking session
        session.pop('booking_session', None)
        session.modified = True
        
        return jsonify({
            'success': True,
            'message': 'Booking created successfully',
            'booking_id': booking.id,
            'booking_reference': booking.booking_reference,
            'redirect_url': f'/booking/confirmation/{booking.booking_reference}'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Booking creation error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Unable to create booking. Please try again.'
        }), 500

# ===============================
# ADMIN DASHBOARD API ENDPOINTS
# ===============================

@api_bp.route('/admin/dashboard-data', methods=['GET'])
@login_required
def get_dashboard_data():
    """Get real-time dashboard data for admin interface"""
    try:
        if not current_user.is_admin:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        today = datetime.utcnow().date()
        
        # Get statistics
        stats = {
            'emergency_repairs': Booking.query.filter(
                and_(Booking.appointment_type == 'emergency',
                     Booking.preferred_date == today)
            ).count(),
            
            'todays_bookings': Booking.query.filter(
                Booking.preferred_date == today
            ).count(),
            
            'completed_today': Booking.query.filter(
                and_(Booking.status == 'completed',
                     Booking.preferred_date == today)
            ).count(),
            
            'total_bookings': Booking.query.count(),
            
            'pending_bookings': Booking.query.filter(
                Booking.status == 'pending'
            ).count(),
            
            'in_progress_bookings': Booking.query.filter(
                Booking.status == 'in_progress'
            ).count()
        }
        
        # Get recent bookings
        recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(10).all()
        bookings_data = []
        
        for booking in recent_bookings:
            bookings_data.append({
                'id': booking.id,
                'booking_reference': booking.booking_reference,
                'customer_name': booking.customer_name,
                'device_type': booking.device_type,
                'device_model': booking.device_model,
                'service_name': booking.service.name if booking.service else 'Unknown',
                'status': booking.status,
                'status_color': booking.get_status_color(),
                'appointment_type': booking.appointment_type,
                'preferred_date': booking.preferred_date.isoformat() if booking.preferred_date else None,
                'preferred_time': booking.preferred_time,
                'customer_phone': booking.customer_phone,
                'zip_code': booking.zip_code,
                'service_price': float(booking.service_price) if booking.service_price else 0,
                'created_at': booking.created_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'stats': stats,
            'recent_bookings': bookings_data,
            'updated_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Dashboard data error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Unable to load dashboard data'
        }), 500

@api_bp.route('/admin/bookings', methods=['GET'])
@login_required
def get_admin_bookings():
    """Get bookings for admin management with filtering"""
    try:
        if not current_user.is_admin:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        # Get query parameters
        status_filter = request.args.get('status', '')
        date_filter = request.args.get('date', '')
        search_term = request.args.get('search', '')
        appointment_type = request.args.get('type', '')
        
        # Base query
        query = Booking.query
        
        # Apply filters
        if status_filter:
            query = query.filter(Booking.status == status_filter)
        
        if date_filter == 'today':
            today = datetime.utcnow().date()
            query = query.filter(Booking.preferred_date == today)
        elif date_filter == 'tomorrow':
            tomorrow = datetime.utcnow().date() + timedelta(days=1)
            query = query.filter(Booking.preferred_date == tomorrow)
        elif date_filter == 'week':
            week_start = datetime.utcnow().date()
            week_end = week_start + timedelta(days=7)
            query = query.filter(and_(Booking.preferred_date >= week_start,
                                    Booking.preferred_date <= week_end))
        
        if appointment_type:
            query = query.filter(Booking.appointment_type == appointment_type)
        
        if search_term:
            search = f"%{search_term}%"
            query = query.filter(
                or_(Booking.customer_name.ilike(search),
                    Booking.customer_phone.ilike(search),
                    Booking.booking_reference.ilike(search),
                    Booking.device_model.ilike(search))
            )
        
        # Order by priority and date
        bookings = query.order_by(
            Booking.appointment_type.desc(),  # Emergency first
            Booking.preferred_date.asc(),
            Booking.preferred_time.asc()
        ).all()
        
        # Format data
        bookings_data = []
        for booking in bookings:
            bookings_data.append({
                'id': booking.id,
                'booking_reference': booking.booking_reference,
                'customer_name': booking.customer_name,
                'customer_phone': booking.customer_phone,
                'customer_email': booking.customer_email,
                'device_type': booking.device_type,
                'device_model': booking.device_model,
                'service_name': booking.service.name if booking.service else 'Unknown',
                'issue_description': booking.issue_description,
                'status': booking.status,
                'status_color': booking.get_status_color(),
                'appointment_type': booking.appointment_type,
                'preferred_date': booking.preferred_date.isoformat() if booking.preferred_date else None,
                'preferred_time': booking.preferred_time,
                'customer_address': booking.customer_address,
                'city': booking.city,
                'state': booking.state,
                'zip_code': booking.zip_code,
                'service_price': float(booking.service_price) if booking.service_price else 0,
                'deposit_amount': float(booking.deposit_amount) if booking.deposit_amount else 0,
                'payment_status': booking.payment_status,
                'created_at': booking.created_at.isoformat(),
                'updated_at': booking.updated_at.isoformat() if booking.updated_at else None
            })
        
        return jsonify({
            'success': True,
            'bookings': bookings_data,
            'count': len(bookings_data),
            'filters_applied': {
                'status': status_filter,
                'date': date_filter,
                'search': search_term,
                'type': appointment_type
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Admin bookings error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Unable to load bookings'
        }), 500

@api_bp.route('/admin/booking/<int:booking_id>/update-status', methods=['POST'])
@login_required
def update_booking_status(booking_id):
    """Update booking status"""
    try:
        if not current_user.is_admin:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        data = request.get_json()
        new_status = data.get('status')
        
        if not new_status:
            return jsonify({
                'success': False,
                'message': 'Status is required'
            }), 400
        
        # Valid statuses
        valid_statuses = ['pending', 'confirmed', 'in_progress', 'completed', 'cancelled']
        if new_status not in valid_statuses:
            return jsonify({
                'success': False,
                'message': 'Invalid status'
            }), 400
        
        # Get booking
        booking = Booking.query.get(booking_id)
        if not booking:
            return jsonify({
                'success': False,
                'message': 'Booking not found'
            }), 404
        
        # Update status
        old_status = booking.status
        booking.status = new_status
        booking.updated_at = datetime.utcnow()
        
        # If completed, set completion time
        if new_status == 'completed' and old_status != 'completed':
            booking.completed_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Booking status updated to {new_status}',
            'booking_id': booking_id,
            'new_status': new_status,
            'status_color': booking.get_status_color()
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Status update error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Unable to update status'
        }), 500

# ===============================
# FILE UPLOAD API ENDPOINTS
# ===============================

@api_bp.route('/upload/device-photo', methods=['POST'])
def upload_device_photo():
    """Upload device photos for damage assessment"""
    try:
        if 'photo' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No photo file provided'
            }), 400
        
        file = request.files['photo']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'No file selected'
            }), 400
        
        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        if not file.filename.lower().endswith(tuple(allowed_extensions)):
            return jsonify({
                'success': False,
                'message': 'Invalid file type. Please upload an image file.'
            }), 400
        
        # Validate file size (max 5MB)
        if len(file.read()) > 5 * 1024 * 1024:
            return jsonify({
                'success': False,
                'message': 'File too large. Maximum size is 5MB.'
            }), 400
        
        file.seek(0)  # Reset file pointer
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        
        # Create upload directory if not exists
        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'device_photos')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)
        
        # Generate URL
        file_url = f"/static/uploads/device_photos/{unique_filename}"
        
        # Store in session for booking process
        if 'booking_session' not in session:
            session['booking_session'] = {}
        
        if 'uploaded_photos' not in session['booking_session']:
            session['booking_session']['uploaded_photos'] = []
        
        session['booking_session']['uploaded_photos'].append({
            'filename': unique_filename,
            'original_name': filename,
            'url': file_url,
            'uploaded_at': datetime.utcnow().isoformat()
        })
        
        session.modified = True
        
        return jsonify({
            'success': True,
            'message': 'Photo uploaded successfully',
            'filename': unique_filename,
            'url': file_url
        })
        
    except Exception as e:
        current_app.logger.error(f"Photo upload error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Upload failed. Please try again.'
        }), 500

# ===============================
# COMMUNICATION API ENDPOINTS
# ===============================

@api_bp.route('/admin/send-message', methods=['POST'])
@login_required
def send_customer_message():
    """Send SMS or email message to customer"""
    try:
        if not current_user.is_admin:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        data = request.get_json()
        message_type = data.get('type', 'sms')  # sms, email, or both
        recipient = data.get('recipient')  # customer ID or booking ID
        message_content = data.get('message', '').strip()
        template_id = data.get('template_id')
        
        if not message_content:
            return jsonify({
                'success': False,
                'message': 'Message content is required'
            }), 400
        
        if not recipient:
            return jsonify({
                'success': False,
                'message': 'Recipient is required'
            }), 400
        
        # Import communication service locally to avoid circular imports
        try:
            from app.services.communication import communication_service
        except ImportError:
            # Fallback for basic messaging simulation
            current_app.logger.info(f"Message sent - Type: {message_type}, Recipient: {recipient}, Content: {message_content[:50]}...")
            return jsonify({
                'success': True,
                'message': f'{message_type.upper()} message sent successfully (simulated)',
                'message_id': str(uuid.uuid4()),
                'sent_at': datetime.utcnow().isoformat()
            })
        
        # Determine recipient details
        booking = None
        customer_email = None
        customer_phone = None
        
        # Try to find booking by ID or reference
        if recipient.isdigit():
            booking = Booking.query.get(int(recipient))
        else:
            booking = Booking.query.filter_by(booking_reference=recipient).first()
        
        if booking:
            customer_email = booking.customer_email
            customer_phone = booking.customer_phone
        
        results = {}
        
        # Send based on message type
        if message_type in ['email', 'both'] and customer_email:
            email_result = communication_service.send_email(
                customer_email,
                'Message from Fixbulance',
                f'<p>{message_content}</p>',
                message_content
            )
            results['email'] = email_result
        
        if message_type in ['sms', 'both'] and customer_phone:
            sms_result = communication_service.send_sms(
                customer_phone,
                message_content
            )
            results['sms'] = sms_result
        
        # Check if any messages were sent
        sent_count = sum(1 for result in results.values() if result.get('success'))
        
        return jsonify({
            'success': sent_count > 0,
            'message': f'{sent_count} message(s) sent successfully',
            'results': results,
            'sent_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Message sending error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Unable to send message. Please try again.'
        }), 500

# ===============================
# SERVICE AREA API ENDPOINTS
# ===============================

@api_bp.route('/admin/service-areas', methods=['GET'])
@login_required
def get_service_areas():
    """Get all service areas for admin management"""
    try:
        if not current_user.is_admin:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        service_areas = ServiceZipCode.query.order_by(ServiceZipCode.distance_miles).all()
        
        areas_data = []
        for area in service_areas:
            areas_data.append({
                'id': area.id,
                'zip_code': area.zip_code,
                'coverage_level': area.coverage_level,
                'distance_miles': float(area.distance_miles),
                'city_name': area.city_name,
                'is_active': area.is_active,
                'created_at': area.created_at.isoformat() if area.created_at else None
            })
        
        # Group by coverage level
        grouped_areas = {
            'full': [area for area in areas_data if area['coverage_level'] == 'full'],
            'partial': [area for area in areas_data if area['coverage_level'] == 'partial'],
            'edge': [area for area in areas_data if area['coverage_level'] == 'edge']
        }
        
        return jsonify({
            'success': True,
            'service_areas': areas_data,
            'grouped_areas': grouped_areas,
            'stats': {
                'total_areas': len(areas_data),
                'full_coverage': len(grouped_areas['full']),
                'partial_coverage': len(grouped_areas['partial']),
                'edge_coverage': len(grouped_areas['edge'])
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Service areas error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Unable to load service areas'
        }), 500

# ===============================
# PAYMENT PROCESSING API ENDPOINTS  
# ===============================

@api_bp.route('/payment/create-deposit-intent', methods=['POST'])
def create_deposit_payment_intent():
    """Create Stripe payment intent for deposit"""
    try:
        data = request.get_json()
        booking_id = data.get('booking_id')
        customer_email = data.get('customer_email')
        
        if not all([booking_id, customer_email]):
            return jsonify({
                'success': False,
                'message': 'Booking ID and customer email are required'
            }), 400
        
        # Get booking
        booking = Booking.query.get(booking_id)
        if not booking:
            return jsonify({
                'success': False,
                'message': 'Booking not found'
            }), 404
        
        # Check if user owns this booking (if authenticated) 
        if current_user.is_authenticated:
            if booking.user_id != current_user.id and not current_user.is_admin:
                return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        # Create payment intent
        result = payment_service.create_deposit_payment_intent(booking, customer_email)
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Create payment intent error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Unable to create payment intent'
        }), 500

@api_bp.route('/payment/create-checkout-session', methods=['POST'])
def create_checkout_session():
    """Create Stripe checkout session for deposit payment"""
    try:
        data = request.get_json()
        booking_id = data.get('booking_id')
        customer_email = data.get('customer_email')
        
        if not all([booking_id, customer_email]):
            return jsonify({
                'success': False,
                'message': 'Booking ID and customer email are required'
            }), 400
        
        # Get booking
        booking = Booking.query.get(booking_id)
        if not booking:
            return jsonify({
                'success': False,
                'message': 'Booking not found'
            }), 404
        
        # Create success and cancel URLs
        success_url = url_for('booking.payment_success', booking_id=booking_id, _external=True)
        cancel_url = url_for('booking.step6_payment', booking_id=booking_id, _external=True)
        
        # Create checkout session
        result = payment_service.create_checkout_session(
            booking, customer_email, success_url, cancel_url
        )
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Create checkout session error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Unable to create checkout session'
        }), 500

@api_bp.route('/payment/confirm', methods=['POST'])
def confirm_payment():
    """Confirm payment completion"""
    try:
        data = request.get_json()
        payment_intent_id = data.get('payment_intent_id')
        session_id = data.get('session_id')
        
        if not payment_intent_id and not session_id:
            return jsonify({
                'success': False,
                'message': 'Payment intent ID or session ID is required'
            }), 400
        
        if payment_intent_id:
            result = payment_service.confirm_payment(payment_intent_id)
        else:
            result = payment_service.retrieve_checkout_session(session_id)
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Confirm payment error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Unable to confirm payment'
        }), 500

@api_bp.route('/webhooks/stripe', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events"""
    try:
        payload = request.data
        signature = request.headers.get('Stripe-Signature')
        
        if not signature:
            return jsonify({'error': 'Missing signature'}), 400
        
        result = payment_service.process_webhook(payload.decode('utf-8'), signature)
        
        if result['success']:
            return jsonify({'status': 'success'}), 200
        else:
            return jsonify({'error': result['error']}), 400
        
    except Exception as e:
        current_app.logger.error(f"Webhook error: {str(e)}")
        return jsonify({'error': 'Webhook processing failed'}), 500

# ===============================
# ERROR HANDLERS
# ===============================

@api_bp.errorhandler(404)
def api_not_found(error):
    return jsonify({
        'success': False,
        'message': 'API endpoint not found'
    }), 404

@api_bp.errorhandler(500)
def api_internal_error(error):
    db.session.rollback()
    return jsonify({
        'success': False,
        'message': 'Internal server error'
    }), 500

@api_bp.errorhandler(403)
def api_forbidden(error):
    return jsonify({
        'success': False,
        'message': 'Access forbidden'
    }), 403 