from flask import Blueprint, render_template, request, jsonify, current_app, redirect, url_for, flash
from app.models.service import Service, DEVICE_TYPES, ISSUE_TYPES
from app.models.service_area import ServiceZipCode
from app.models.system_settings import SystemSettings
from datetime import datetime, timedelta

main_bp = Blueprint('main', __name__)

@main_bp.context_processor
def inject_current_year():
    return {'current_year': datetime.now().year}

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
    
    # Get current base deposit
    base_deposit = SystemSettings.get_base_deposit()
    
    return render_template('index.html',
                         device_types=DEVICE_TYPES,
                         featured_services=featured_services,
                         total_services=total_services,
                         covered_zip_codes=covered_zip_codes,
                         base_deposit=base_deposit)

@main_bp.route('/repair')
def repair():
    return render_template('repair.html')

@main_bp.route('/buy')
def buy():
    return render_template('buy.html')

@main_bp.route('/sell')
def sell():
    return render_template('sell.html')

@main_bp.route('/about')
def about():
    """About page with service information"""
    return render_template('about.html')

@main_bp.route('/location')
def location():
    return render_template('location.html')

@main_bp.route('/check-zip')
def check_zip():
    """ZIP code checker page"""
    return render_template('check_zip.html')

@main_bp.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html')

@main_bp.route('/quote')
def quote():
    return render_template('quote.html')

@main_bp.route('/privacy')
def privacy():
    """Privacy policy page"""
    return render_template('privacy.html')

@main_bp.route('/terms')
def terms():
    """Terms of service page"""
    return render_template('terms.html')

@main_bp.route('/refund')
def refund():
    """Refund policy page"""
    return render_template('refund.html')

@main_bp.route('/robots.txt')
def robots_txt():
    """Serve robots.txt file"""
    return current_app.send_static_file('robots.txt')

@main_bp.route('/sitemap.xml')
def sitemap_xml():
    """Generate dynamic sitemap.xml"""
    from flask import make_response
    
    pages = []
    ten_days_ago = (datetime.now() - timedelta(days=10)).date().isoformat()
    
    # Main pages
    for rule in current_app.url_map.iter_rules():
        if "GET" in rule.methods and len(rule.arguments) == 0:
            # Skip admin, API, and other internal routes
            if any(skip in str(rule) for skip in ['/admin', '/api', '/_debug', '/auth/logout']):
                continue
            
            pages.append({
                'loc': f"https://www.fixbulance.com{rule.rule}",
                'lastmod': ten_days_ago,
                'changefreq': 'weekly',
                'priority': '0.8' if rule.rule == '/' else '0.6'
            })
    
    sitemap_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    {"".join([f'''
    <url>
        <loc>{page['loc']}</loc>
        <lastmod>{page['lastmod']}</lastmod>
        <changefreq>{page['changefreq']}</changefreq>
        <priority>{page['priority']}</priority>
    </url>''' for page in pages])}
</urlset>"""
    
    response = make_response(sitemap_xml)
    response.headers["Content-Type"] = "application/xml"
    return response

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