from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from functools import wraps
from app import db
from app.models.device_pricing import DevicePricing, WaterDamageService, LaptopTabletService
import json

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

device_pricing_bp = Blueprint('device_pricing', __name__, url_prefix='/admin/device-pricing')

@device_pricing_bp.route('/')
@login_required
@admin_required
def index():
    """Device pricing management dashboard"""
    # Get all iPhone models
    iphone_models = DevicePricing.query.filter_by(brand='iPhone', is_active=True).order_by(DevicePricing.model).all()
    
    # Get all Samsung models
    samsung_models = DevicePricing.query.filter_by(brand='Samsung', is_active=True).order_by(DevicePricing.model).all()
    
    # Get water damage service
    water_damage_service = WaterDamageService.query.first()
    
    # Get laptop/tablet services
    laptop_services = LaptopTabletService.query.filter_by(device_type='Laptop', is_active=True).all()
    ipad_services = LaptopTabletService.query.filter_by(device_type='iPad', is_active=True).all()
    tablet_services = LaptopTabletService.query.filter_by(device_type='Tablet', is_active=True).all()
    
    # Calculate statistics
    total_iphone_models = len(iphone_models)
    total_samsung_models = len(samsung_models)
    refurb_only_count = DevicePricing.query.filter_by(is_refurbished_only=True).count()
    
    # Get pricing ranges
    min_screen_price = db.session.query(db.func.min(DevicePricing.afm_screen)).filter(DevicePricing.afm_screen.isnot(None)).scalar() or 0
    max_screen_price = db.session.query(db.func.max(DevicePricing.original_screen)).filter(DevicePricing.original_screen.isnot(None)).scalar() or 0
    
    return render_template('admin/device_pricing.html',
                         iphone_models=iphone_models,
                         samsung_models=samsung_models,
                         water_damage_service=water_damage_service,
                         laptop_services=laptop_services,
                         ipad_services=ipad_services,
                         tablet_services=tablet_services,
                         total_iphone_models=total_iphone_models,
                         total_samsung_models=total_samsung_models,
                         refurb_only_count=refurb_only_count,
                         min_screen_price=min_screen_price,
                         max_screen_price=max_screen_price)

@device_pricing_bp.route('/device/<int:device_id>')
@login_required
@admin_required
def device_detail(device_id):
    """Get device pricing details"""
    device = DevicePricing.query.get_or_404(device_id)
    return jsonify(device.to_dict())

@device_pricing_bp.route('/device/<int:device_id>/update', methods=['POST'])
@login_required
@admin_required
def update_device_pricing(device_id):
    """Update device pricing"""
    device = DevicePricing.query.get_or_404(device_id)
    
    try:
        # Get form data
        data = request.get_json()
        
        # Update pricing fields
        if 'original_screen' in data:
            device.original_screen = float(data['original_screen']) if data['original_screen'] else None
        if 'original_battery' in data:
            device.original_battery = float(data['original_battery']) if data['original_battery'] else None
        if 'afm_screen' in data:
            device.afm_screen = float(data['afm_screen']) if data['afm_screen'] else None
        if 'afm_battery' in data:
            device.afm_battery = float(data['afm_battery']) if data['afm_battery'] else None
        if 'charger_port' in data:
            device.charger_port = float(data['charger_port']) if data['charger_port'] else None
        if 'charger_port_original' in data:
            device.charger_port_original = float(data['charger_port_original']) if data['charger_port_original'] else None
        if 'speaker' in data:
            device.speaker = float(data['speaker']) if data['speaker'] else None
        if 'camera_lens' in data:
            device.camera_lens = float(data['camera_lens']) if data['camera_lens'] else None
        if 'vibrator' in data:
            device.vibrator = float(data['vibrator']) if data['vibrator'] else None
        if 'original_back_glass' in data:
            device.original_back_glass = float(data['original_back_glass']) if data['original_back_glass'] else None
        if 'afm_back_glass' in data:
            device.afm_back_glass = float(data['afm_back_glass']) if data['afm_back_glass'] else None
        
        # Update metadata
        if 'is_active' in data:
            device.is_active = bool(data['is_active'])
        if 'is_refurbished_only' in data:
            device.is_refurbished_only = bool(data['is_refurbished_only'])
        if 'notes' in data:
            device.notes = data['notes']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Pricing updated for {device.display_name}',
            'device': device.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error updating pricing: {str(e)}'
        }), 400

@device_pricing_bp.route('/search')
@login_required
@admin_required
def search_devices():
    """Search devices by brand and model"""
    query = request.args.get('q', '').strip()
    brand = request.args.get('brand', '').strip()
    
    search_query = DevicePricing.query.filter_by(is_active=True)
    
    if brand:
        search_query = search_query.filter_by(brand=brand)
    
    if query:
        search_query = search_query.filter(
            db.or_(
                DevicePricing.model.ilike(f'%{query}%'),
                DevicePricing.model_display.ilike(f'%{query}%')
            )
        )
    
    devices = search_query.order_by(DevicePricing.brand, DevicePricing.model).limit(20).all()
    
    return jsonify({
        'devices': [device.to_dict() for device in devices]
    })

@device_pricing_bp.route('/device/create', methods=['POST'])
@login_required
@admin_required
def create_device():
    """Create a new device pricing entry"""
    try:
        # Get form data
        data = request.get_json()
        
        # Validate required fields
        if not data.get('device_name') or not data.get('brand'):
            return jsonify({
                'success': False,
                'message': 'Device name and brand are required'
            }), 400
        
        # Create new device
        device = DevicePricing(
            model=data.get('device_name'),
            brand=data.get('brand'),
            display_name=data.get('device_name'),
            original_screen=float(data.get('original_screen')) if data.get('original_screen') else None,
            afm_screen=float(data.get('afm_screen')) if data.get('afm_screen') else None,
            original_battery=float(data.get('original_battery')) if data.get('original_battery') else None,
            afm_battery=float(data.get('afm_battery')) if data.get('afm_battery') else None,
            charger_port=float(data.get('charger_port')) if data.get('charger_port') else None,
            speaker=float(data.get('speaker')) if data.get('speaker') else None,
            camera_lens=float(data.get('camera_lens')) if data.get('camera_lens') else None,
            is_active=bool(data.get('is_active', True)),
            is_refurbished_only=bool(data.get('is_refurbished_only', False)),
            notes=data.get('notes', '')
        )
        
        db.session.add(device)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Device {device.display_name} added successfully',
            'device': device.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error creating device: {str(e)}'
        }), 400

@device_pricing_bp.route('/export')
@login_required
@admin_required
def export_pricing_data():
    """Export device pricing data to CSV"""
    try:
        # Get all active devices
        devices = DevicePricing.query.filter_by(is_active=True).order_by(DevicePricing.brand, DevicePricing.model).all()
        
        # For now, just show a success message
        return jsonify({
            'success': True,
            'message': f'Found {len(devices)} devices for export. Export functionality coming soon!',
            'device_count': len(devices)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Export error: {str(e)}'
        }), 500

@device_pricing_bp.route('/pricing-lookup')
def pricing_lookup():
    """Public endpoint for pricing lookup - to be used by booking system"""
    brand = request.args.get('brand')
    model = request.args.get('model')
    
    if not brand or not model:
        return jsonify({'error': 'Brand and model are required'}), 400
    
    device = DevicePricing.query.filter_by(brand=brand, model=model, is_active=True).first()
    
    if not device:
        return jsonify({'error': 'Device not found'}), 404
    
    return jsonify({
        'device': device.to_dict(),
        'available_services': device.get_available_services()
    })
