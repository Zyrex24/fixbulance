from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect, generate_csrf
from config.config import config

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
mail = Mail()
csrf = CSRFProtect()

def create_app(config_name='development'):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    csrf.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Import models to register with SQLAlchemy
    from app.models.user import User
    from app.models.service import Service
    from app.models.service_category import ServiceCategory
    from app.models.booking import Booking
    from app.models.booking_service import BookingService
    from app.models.price_history import PriceHistory
    from app.models.service_area import ServiceZipCode, AddressValidationCache
    from app.models.payment import Payment
    from app.models.review import Review
    from app.models.waiver import ServiceWaiver
    from app.models.device_pricing import DevicePricing, WaterDamageService, LaptopTabletService
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    from app.blueprints.main import main_bp
    from app.blueprints.auth import auth_bp
    from app.blueprints.booking import booking_bp
    from app.blueprints.admin import admin_bp
    from app.blueprints.api import api_bp
    from app.blueprints.payment import payment_bp
    from app.blueprints.review import review_bp
    from app.blueprints.device_pricing import device_pricing_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(booking_bp, url_prefix='/booking')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(payment_bp, url_prefix='/payment')
    app.register_blueprint(review_bp)
    app.register_blueprint(device_pricing_bp)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        from flask import render_template
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    # Context processors
    @app.context_processor
    def inject_config():
        return {
            'GOOGLE_MAPS_API_KEY': app.config.get('GOOGLE_MAPS_API_KEY'),
            'STRIPE_PUBLISHABLE_KEY': app.config.get('STRIPE_PUBLISHABLE_KEY'),
            'csrf_token': generate_csrf
        }
    
    return app 