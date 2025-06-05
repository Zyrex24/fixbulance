from flask import Blueprint, render_template, request, jsonify, current_app
from app.models.service import Service, DEVICE_TYPES, ISSUE_TYPES
from app.models.service_area import ServiceZipCode

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Homepage with device selection (Step 1 of booking wizard)"""
    # Get featured services for each device type
    featured_services = {}
    for device_type in DEVICE_TYPES:
        services = Service.query.filter_by(
            device_type=device_type, 
            is_active=True, 
            is_featured=True
        ).order_by(Service.sort_order).limit(3).all()
        featured_services[device_type] = services
    
    # Get service statistics
    total_services = Service.query.filter_by(is_active=True).count()
    covered_zip_codes = ServiceZipCode.query.filter_by(is_active=True).count()
    
    return render_template('index.html',
                         device_types=DEVICE_TYPES,
                         featured_services=featured_services,
                         total_services=total_services,
                         covered_zip_codes=covered_zip_codes)

@main_bp.route('/about')
def about():
    """About page with service information"""
    return render_template('about.html')

@main_bp.route('/service-area')
def service_area():
    """Service area information page"""
    # Get all covered ZIP codes by coverage level
    zip_codes = ServiceZipCode.query.filter_by(is_active=True).order_by(
        ServiceZipCode.city, ServiceZipCode.zip_code
    ).all()
    
    # Group by coverage level
    coverage_groups = {
        'full': [],
        'partial': [],
        'edge': []
    }
    
    for zip_code in zip_codes:
        coverage_groups[zip_code.coverage_level].append(zip_code)
    
    return render_template('service_area.html', 
                         coverage_groups=coverage_groups,
                         service_radius=current_app.config.get('DEFAULT_SERVICE_RADIUS', 10))

@main_bp.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html')

@main_bp.route('/privacy')
def privacy():
    """Privacy policy page"""
    return render_template('privacy.html')

@main_bp.route('/terms')
def terms():
    """Terms of service page"""
    return render_template('terms.html')

# API routes for device selection
@main_bp.route('/api/services/<device_type>')
def get_services_by_device(device_type):
    """Get services for a specific device type (AJAX endpoint)"""
    if device_type not in DEVICE_TYPES:
        return jsonify({'error': 'Invalid device type'}), 400
    
    services = Service.query.filter_by(
        device_type=device_type,
        is_active=True
    ).order_by(Service.sort_order, Service.name).all()
    
    return jsonify({
        'device_type': device_type,
        'services': [service.to_dict() for service in services]
    })

@main_bp.route('/api/issue-types')
def get_issue_types():
    """Get all available issue types"""
    return jsonify({
        'issue_types': ISSUE_TYPES
    })

# Service area validation API
@main_bp.route('/api/validate-zip', methods=['POST'])
def validate_zip_code():
    """Validate ZIP code for service area (AJAX endpoint)"""
    data = request.get_json()
    zip_code = data.get('zip_code', '').strip()
    
    if not zip_code:
        return jsonify({'error': 'ZIP code is required'}), 400
    
    # Clean ZIP code (remove any extra characters)
    zip_code = ''.join(filter(str.isdigit, zip_code))[:5]
    
    if len(zip_code) != 5:
        return jsonify({'error': 'Invalid ZIP code format'}), 400
    
    # Check ZIP code in service area
    service_zip = ServiceZipCode.query.filter_by(
        zip_code=zip_code,
        is_active=True
    ).first()
    
    if service_zip:
        return jsonify({
            'valid': True,
            'coverage_level': service_zip.coverage_level,
            'city': service_zip.city,
            'state': service_zip.state,
            'distance_miles': service_zip.distance_miles,
            'requires_confirmation': service_zip.requires_confirmation,
            'message': f"Great! We service {service_zip.city}, {service_zip.state}."
        })
    else:
        return jsonify({
            'valid': False,
            'message': f"Sorry, we don't currently service ZIP code {zip_code}. Our service area covers within {current_app.config.get('DEFAULT_SERVICE_RADIUS', 10)} miles of Orland Park, IL.",
            'suggestion': "Contact us to see if we can expand service to your area."
        })

# Error handlers for this blueprint
@main_bp.app_errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('errors/404.html'), 404

@main_bp.app_errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return render_template('errors/500.html'), 500 