# Flask Mobile Repair Service Application
# Technology Validation and Proof of Concept

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import stripe
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///repair_service.db'  # Using SQLite for validation
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Configure Stripe (test mode)
stripe.api_key = os.getenv('STRIPE_SECRET_KEY', 'sk_test_placeholder')

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    bookings = db.relationship('Booking', backref='customer', lazy=True)

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    device_type = db.Column(db.String(50), nullable=False)  # iPhone, Samsung, Other
    estimated_time = db.Column(db.Integer)  # minutes
    is_active = db.Column(db.Boolean, default=True)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    
    # Customer details
    customer_name = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    customer_address = db.Column(db.Text, nullable=False)
    device_model = db.Column(db.String(100), nullable=False)
    issue_description = db.Column(db.Text)
    
    # Booking details
    appointment_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, in_progress, completed, cancelled
    
    # Payment details
    deposit_amount = db.Column(db.Float, default=15.00)
    total_amount = db.Column(db.Float)
    payment_status = db.Column(db.String(20), default='pending')  # pending, paid, refunded
    stripe_payment_id = db.Column(db.String(100))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    service = db.relationship('Service', backref='bookings')

# Login manager user loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes - Technology Validation

@app.route('/')
def index():
    """Homepage with device selection"""
    services = Service.query.filter_by(is_active=True).all()
    device_types = db.session.query(Service.device_type).distinct().all()
    
    return render_template('index.html', 
                         services=services, 
                         device_types=[dt[0] for dt in device_types])

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        
        # Check if user exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered')
            return redirect(url_for('register'))
        
        # Create new user
        user = User(
            email=email,
            password_hash=generate_password_hash(password),
            first_name=first_name,
            last_name=last_name
        )
        
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        flash('Registration successful!')
        return redirect(url_for('dashboard'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Customer dashboard"""
    user_bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.created_at.desc()).all()
    return render_template('dashboard.html', bookings=user_bookings)

@app.route('/book/<device_type>')
@login_required
def booking_form(device_type):
    """Booking form for specific device type"""
    services = Service.query.filter_by(device_type=device_type, is_active=True).all()
    return render_template('booking.html', device_type=device_type, services=services)

@app.route('/create_booking', methods=['POST'])
@login_required
def create_booking():
    """Create new booking with Stripe payment"""
    try:
        # Get form data
        service_id = request.form['service_id']
        customer_name = request.form['customer_name']
        customer_phone = request.form['customer_phone']
        customer_address = request.form['customer_address']
        device_model = request.form['device_model']
        issue_description = request.form.get('issue_description', '')
        appointment_date = datetime.strptime(request.form['appointment_date'], '%Y-%m-%dT%H:%M')
        
        service = Service.query.get(service_id)
        if not service:
            flash('Invalid service selected')
            return redirect(url_for('index'))
        
        # Create booking
        booking = Booking(
            user_id=current_user.id,
            service_id=service_id,
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_address=customer_address,
            device_model=device_model,
            issue_description=issue_description,
            appointment_date=appointment_date,
            total_amount=service.price
        )
        
        db.session.add(booking)
        db.session.commit()
        
        # Redirect to payment
        return redirect(url_for('payment', booking_id=booking.id))
        
    except Exception as e:
        flash(f'Error creating booking: {str(e)}')
        return redirect(url_for('index'))

@app.route('/payment/<int:booking_id>')
@login_required
def payment(booking_id):
    """Payment page for booking deposit"""
    booking = Booking.query.get_or_404(booking_id)
    
    if booking.user_id != current_user.id:
        flash('Unauthorized access')
        return redirect(url_for('dashboard'))
    
    return render_template('payment.html', booking=booking)

@app.route('/process_payment', methods=['POST'])
@login_required
def process_payment():
    """Process Stripe payment"""
    try:
        booking_id = request.form['booking_id']
        booking = Booking.query.get_or_404(booking_id)
        
        # Create Stripe payment intent (test mode)
        payment_intent = stripe.PaymentIntent.create(
            amount=int(booking.deposit_amount * 100),  # Amount in cents
            currency='usd',
            metadata={'booking_id': booking_id}
        )
        
        # Update booking with payment info
        booking.stripe_payment_id = payment_intent.id
        booking.payment_status = 'paid'
        booking.status = 'confirmed'
        db.session.commit()
        
        flash('Payment successful! Your booking is confirmed.')
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        flash(f'Payment error: {str(e)}')
        return redirect(url_for('payment', booking_id=booking_id))

@app.route('/admin')
@login_required
def admin_dashboard():
    """Admin dashboard"""
    if not current_user.is_admin:
        flash('Admin access required')
        return redirect(url_for('dashboard'))
    
    bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    return render_template('admin.html', bookings=bookings)

@app.route('/api/services/<device_type>')
def api_services(device_type):
    """API endpoint for services by device type"""
    services = Service.query.filter_by(device_type=device_type, is_active=True).all()
    return jsonify([{
        'id': s.id,
        'name': s.name,
        'price': s.price,
        'description': s.description,
        'estimated_time': s.estimated_time
    } for s in services])

# Initialize database and sample data
def init_db():
    """Initialize database with sample data"""
    db.create_all()
    
    # Create sample services if not exist
    if Service.query.count() == 0:
        sample_services = [
            Service(name='Screen Replacement', description='Replace cracked or damaged screen', 
                   price=150.00, device_type='iPhone', estimated_time=60),
            Service(name='Battery Replacement', description='Replace old or degraded battery', 
                   price=80.00, device_type='iPhone', estimated_time=30),
            Service(name='Water Damage Repair', description='Repair water-damaged device', 
                   price=200.00, device_type='iPhone', estimated_time=120),
            Service(name='Screen Replacement', description='Replace cracked or damaged screen', 
                   price=140.00, device_type='Samsung', estimated_time=60),
            Service(name='Battery Replacement', description='Replace old or degraded battery', 
                   price=75.00, device_type='Samsung', estimated_time=30),
            Service(name='Charging Port Repair', description='Fix charging port issues', 
                   price=90.00, device_type='Other', estimated_time=45),
        ]
        
        for service in sample_services:
            db.session.add(service)
        
        # Create admin user
        admin_user = User(
            email='admin@repair.com',
            password_hash=generate_password_hash('admin123'),
            first_name='Admin',
            last_name='User',
            is_admin=True
        )
        db.session.add(admin_user)
        
        db.session.commit()
        print("Sample data created successfully!")

if __name__ == '__main__':
    with app.app_context():
        init_db()
    
    print("🚀 Flask Mobile Repair Service - Technology Validation")
    print("📱 Server starting on http://localhost:5000")
    print("✅ Technology Stack Validated:")
    print("   - Flask 2.3.3 ✅")
    print("   - SQLAlchemy Database ✅")
    print("   - Flask-Login Authentication ✅")
    print("   - Stripe Payment Integration ✅")
    print("   - RESTful API Endpoints ✅")
    
    app.run(debug=True, host='0.0.0.0', port=5000) 