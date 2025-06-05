from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, date, timedelta
from app import db
from app.models.user import User
from app.models.service import Service
from app.models.booking import Booking, BOOKING_STATUSES
from app.models.service_area import ServiceZipCode

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Card-based admin dashboard for mobile van operations"""
    # Get today's bookings (most important for van operations)
    today = date.today()
    today_bookings = Booking.query.filter_by(scheduled_date=today).order_by(
        Booking.scheduled_time
    ).all()
    
    # Get urgent bookings (within 2 hours and not confirmed)
    urgent_bookings = [b for b in today_bookings if b.is_urgent]
    
    # Get pending bookings (need confirmation)
    pending_bookings = Booking.query.filter_by(status='pending').order_by(
        Booking.created_at.desc()
    ).limit(10).all()
    
    # Get recent bookings for overview
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(8).all()
    
    # Dashboard statistics
    stats = {
        'total_bookings': Booking.query.count(),
        'pending_bookings': Booking.query.filter_by(status='pending').count(),
        'today_bookings': len(today_bookings),
        'urgent_bookings': len(urgent_bookings),
        'completed_today': len([b for b in today_bookings if b.status == 'completed']),
    }
    
    return render_template('admin/dashboard.html',
                         today_bookings=today_bookings,
                         urgent_bookings=urgent_bookings,
                         pending_bookings=pending_bookings,
                         recent_bookings=recent_bookings,
                         stats=stats,
                         today=today)

@admin_bp.route('/bookings')
@login_required
@admin_required
def bookings():
    """All bookings management"""
    # Get filter parameters
    status_filter = request.args.get('status', 'all')
    date_filter = request.args.get('date', 'all')
    page = request.args.get('page', 1, type=int)
    
    # Build query
    query = Booking.query
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    if date_filter == 'today':
        query = query.filter_by(scheduled_date=date.today())
    elif date_filter == 'tomorrow':
        query = query.filter_by(scheduled_date=date.today() + timedelta(days=1))
    elif date_filter == 'this_week':
        start_week = date.today() - timedelta(days=date.today().weekday())
        end_week = start_week + timedelta(days=6)
        query = query.filter(Booking.scheduled_date.between(start_week, end_week))
    
    # Paginate results
    bookings = query.order_by(Booking.scheduled_date.desc(), Booking.scheduled_time.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/bookings.html',
                         bookings=bookings,
                         status_filter=status_filter,
                         date_filter=date_filter,
                         booking_statuses=BOOKING_STATUSES)

@admin_bp.route('/booking/<int:booking_id>')
@login_required
@admin_required
def booking_detail(booking_id):
    """Detailed booking view for admin"""
    booking = Booking.query.get_or_404(booking_id)
    
    return render_template('admin/booking_detail.html',
                         booking=booking,
                         booking_statuses=BOOKING_STATUSES)

@admin_bp.route('/booking/<int:booking_id>/update-status', methods=['POST'])
@login_required
@admin_required
def update_booking_status(booking_id):
    """Update booking status (AJAX endpoint for quick actions)"""
    booking = Booking.query.get_or_404(booking_id)
    new_status = request.json.get('status')
    
    if new_status not in BOOKING_STATUSES:
        return jsonify({'error': 'Invalid status'}), 400
    
    try:
        booking.update_status(new_status, current_user.id)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Booking status updated to {new_status}',
            'new_status': new_status,
            'status_color': booking.status_color,
            'status_icon': booking.status_icon
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update status'}), 500

@admin_bp.route('/booking/<int:booking_id>/add-notes', methods=['POST'])
@login_required
@admin_required
def add_booking_notes(booking_id):
    """Add technician notes to booking"""
    booking = Booking.query.get_or_404(booking_id)
    notes = request.form.get('notes', '').strip()
    
    if not notes:
        flash('Please enter some notes.', 'warning')
        return redirect(url_for('admin.booking_detail', booking_id=booking_id))
    
    try:
        booking.technician_notes = notes
        db.session.commit()
        flash('Notes added successfully.', 'success')
    
    except Exception as e:
        db.session.rollback()
        flash('Failed to add notes.', 'danger')
    
    return redirect(url_for('admin.booking_detail', booking_id=booking_id))

@admin_bp.route('/customers')
@login_required
@admin_required
def customers():
    """Customer management"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = User.query.filter_by(is_admin=False)
    
    if search:
        query = query.filter(
            db.or_(
                User.first_name.contains(search),
                User.last_name.contains(search),
                User.email.contains(search),
                User.phone.contains(search)
            )
        )
    
    customers = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/customers.html',
                         customers=customers,
                         search=search)

@admin_bp.route('/customer/<int:customer_id>')
@login_required
@admin_required
def customer_detail(customer_id):
    """Customer detail view"""
    customer = User.query.get_or_404(customer_id)
    
    # Get customer's bookings
    bookings = Booking.query.filter_by(user_id=customer_id).order_by(
        Booking.created_at.desc()
    ).all()
    
    return render_template('admin/customer_detail.html',
                         customer=customer,
                         bookings=bookings)

@admin_bp.route('/services')
@login_required
@admin_required
def services():
    """Service management"""
    services = Service.query.order_by(Service.device_type, Service.sort_order).all()
    
    return render_template('admin/services.html', services=services)

@admin_bp.route('/service/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_service():
    """Create new service"""
    if request.method == 'POST':
        try:
            service = Service(
                name=request.form['name'],
                description=request.form.get('description', ''),
                device_type=request.form['device_type'],
                issue_type=request.form['issue_type'],
                base_price=float(request.form['base_price']),
                estimated_time=int(request.form.get('estimated_time', 60)),
                difficulty_level=request.form.get('difficulty_level', 'medium'),
                requires_parts=request.form.get('requires_parts') == 'on',
                is_featured=request.form.get('is_featured') == 'on'
            )
            
            db.session.add(service)
            db.session.commit()
            
            flash('Service created successfully.', 'success')
            return redirect(url_for('admin.services'))
        
        except Exception as e:
            db.session.rollback()
            flash('Failed to create service.', 'danger')
    
    return render_template('admin/service_form.html', service=None)

@admin_bp.route('/service-area')
@login_required
@admin_required
def service_area():
    """Service area management"""
    zip_codes = ServiceZipCode.query.order_by(
        ServiceZipCode.distance_miles, ServiceZipCode.zip_code
    ).all()
    
    return render_template('admin/service_area.html', zip_codes=zip_codes)

@admin_bp.route('/service-area/add', methods=['POST'])
@login_required
@admin_required
def add_service_zip():
    """Add new ZIP code to service area"""
    try:
        zip_code = ServiceZipCode(
            zip_code=request.form['zip_code'],
            city=request.form['city'],
            state=request.form.get('state', 'IL'),
            distance_miles=float(request.form.get('distance_miles', 0)),
            coverage_level=request.form.get('coverage_level', 'full')
        )
        
        db.session.add(zip_code)
        db.session.commit()
        
        flash('ZIP code added to service area.', 'success')
    
    except Exception as e:
        db.session.rollback()
        flash('Failed to add ZIP code.', 'danger')
    
    return redirect(url_for('admin.service_area'))

@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    """Basic reporting dashboard"""
    # Revenue calculations
    completed_bookings = Booking.query.filter_by(status='completed').all()
    total_revenue = sum(b.final_amount or b.total_estimated_cost or 0 for b in completed_bookings)
    
    # This month's stats
    current_month = date.today().replace(day=1)
    next_month = (current_month + timedelta(days=32)).replace(day=1)
    
    monthly_bookings = Booking.query.filter(
        Booking.created_at >= current_month,
        Booking.created_at < next_month
    ).all()
    
    monthly_revenue = sum(
        b.final_amount or b.total_estimated_cost or 0 
        for b in monthly_bookings if b.status == 'completed'
    )
    
    # Service popularity
    service_stats = db.session.query(
        Service.name, Service.device_type, db.func.count(Booking.id).label('booking_count')
    ).join(Booking).group_by(Service.id).order_by(db.desc('booking_count')).limit(10).all()
    
    stats = {
        'total_revenue': total_revenue,
        'monthly_revenue': monthly_revenue,
        'total_customers': User.query.filter_by(is_admin=False).count(),
        'total_bookings': Booking.query.count(),
        'completion_rate': len(completed_bookings) / max(Booking.query.count(), 1) * 100,
        'monthly_bookings': len(monthly_bookings),
        'service_stats': service_stats
    }
    
    return render_template('admin/reports.html', stats=stats)

# API endpoints for quick actions
@admin_bp.route('/api/quick-action', methods=['POST'])
@login_required
@admin_required
def quick_action():
    """Handle quick actions from dashboard cards"""
    action = request.json.get('action')
    booking_id = request.json.get('booking_id')
    
    if not booking_id:
        return jsonify({'error': 'Booking ID required'}), 400
    
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({'error': 'Booking not found'}), 404
    
    try:
        if action == 'confirm':
            booking.update_status('confirmed', current_user.id)
        elif action == 'start':
            booking.update_status('in_progress', current_user.id)
        elif action == 'complete':
            booking.update_status('completed', current_user.id)
        elif action == 'cancel':
            booking.update_status('cancelled', current_user.id)
        else:
            return jsonify({'error': 'Invalid action'}), 400
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Booking {action}ed successfully',
            'new_status': booking.status,
            'status_color': booking.status_color
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Action failed'}), 500 