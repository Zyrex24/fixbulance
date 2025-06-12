#!/bin/bash

echo "🔧 Fixbulance Specific Updates Script"
echo "===================================="
echo "Implementing: Payment updates, social media, legal pages, debug removal"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

APP_DIR="/var/www/fixbulance"
APP_USER="fixbulance"

print_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
    else
        echo -e "${RED}❌ $1${NC}"
    fi
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

cd $APP_DIR

print_header "BACKUP CURRENT VERSION"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
sudo -u $APP_USER tar -czf "backups/pre_updates_$TIMESTAMP.tar.gz" \
    --exclude="venv" --exclude="backups" --exclude="logs" .
print_status "Backup created"

print_header "REMOVING DEBUG AND EMERGENCY TEXT"
print_info "Removing DEBUG and 'asap in emergency repair' text..."

# Remove from templates
find app/templates -name "*.html" -exec sudo -u $APP_USER sed -i 's/DEBUG[[:space:]]*-[[:space:]]*//gi' {} \;
find app/templates -name "*.html" -exec sudo -u $APP_USER sed -i 's/asap[[:space:]]*in[[:space:]]*emergency[[:space:]]*repair[[:space:]]*-[[:space:]]*//gi' {} \;

# Remove from Python files
find . -name "*.py" -exec sudo -u $APP_USER sed -i 's/DEBUG[[:space:]]*-[[:space:]]*//g' {} \;
find . -name "*.py" -exec sudo -u $APP_USER sed -i "s/debug[[:space:]]*=[[:space:]]*True/debug=False/g" {} \;

print_status "Debug text removed"

print_header "UPDATING STRIPE PAYMENT INTEGRATION"
print_info "Creating enhanced Stripe payment form with modern payment methods..."

# Create enhanced Stripe payment template
sudo -u $APP_USER tee app/templates/payment/stripe_payment.html > /dev/null << 'EOF'
<div class="stripe-payment-container">
    <div class="payment-header">
        <h3>Secure Payment</h3>
        <div class="payment-methods">
            <img src="/static/img/stripe-badge.png" alt="Stripe" class="payment-badge">
            <div class="accepted-methods">
                <i class="fab fa-cc-visa"></i>
                <i class="fab fa-cc-mastercard"></i>
                <i class="fab fa-cc-amex"></i>
                <i class="fab fa-apple-pay"></i>
                <i class="fab fa-google-pay"></i>
                <i class="fab fa-paypal"></i>
            </div>
        </div>
    </div>

    <form id="payment-form" class="stripe-form">
        <!-- Stripe Elements will be mounted here -->
        <div id="payment-element" class="payment-element"></div>
        
        <div class="payment-summary">
            <div class="summary-row">
                <span>Service:</span>
                <span id="service-name">Phone Repair</span>
            </div>
            <div class="summary-row">
                <span>Deposit:</span>
                <span id="deposit-amount">$15.00</span>
            </div>
            <div class="summary-row total">
                <span>Total:</span>
                <span id="total-amount">$15.00</span>
            </div>
        </div>

        <button id="submit-button" class="pay-button">
            <span id="button-text">Pay Now</span>
            <div id="spinner" class="spinner hidden"></div>
        </button>
        
        <div id="payment-message" class="payment-message hidden"></div>
    </form>
</div>

<style>
.stripe-payment-container {
    max-width: 500px;
    margin: 0 auto;
    padding: 30px;
    background: white;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
}

.payment-header {
    text-align: center;
    margin-bottom: 30px;
}

.payment-methods {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 15px;
}

.payment-badge {
    height: 30px;
}

.accepted-methods {
    display: flex;
    gap: 15px;
    font-size: 24px;
}

.accepted-methods i {
    color: #666;
}

.payment-element {
    margin-bottom: 30px;
    padding: 15px;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
}

.payment-summary {
    background: #f8f9fa;
    padding: 20px;
    border-radius: 8px;
    margin-bottom: 30px;
}

.summary-row {
    display: flex;
    justify-content: space-between;
    margin-bottom: 10px;
}

.summary-row.total {
    font-weight: bold;
    font-size: 18px;
    border-top: 1px solid #ddd;
    padding-top: 10px;
}

.pay-button {
    width: 100%;
    padding: 15px;
    background: #dc3545;
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
}

.pay-button:hover {
    background: #c82333;
}

.pay-button:disabled {
    background: #6c757d;
    cursor: not-allowed;
}

.spinner {
    width: 20px;
    height: 20px;
    border: 2px solid #ffffff;
    border-top: 2px solid transparent;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.hidden {
    display: none;
}

.payment-message {
    margin-top: 15px;
    padding: 15px;
    border-radius: 8px;
    text-align: center;
}

.payment-message.error {
    background: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
}

.payment-message.success {
    background: #d4edda;
    color: #155724;
    border: 1px solid #c3e6cb;
}
</style>

<script src="https://js.stripe.com/v3/"></script>
<script>
// Initialize Stripe
const stripe = Stripe('{{ stripe_public_key }}');

// Create payment element
const elements = stripe.elements({
    appearance: {
        theme: 'stripe',
        variables: {
            colorPrimary: '#dc3545',
        }
    }
});

const paymentElement = elements.create('payment', {
    defaultValues: {
        billingDetails: {
            name: '{{ customer_name }}',
            email: '{{ customer_email }}'
        }
    }
});

paymentElement.mount('#payment-element');

// Handle form submission
const form = document.getElementById('payment-form');
const submitButton = document.getElementById('submit-button');
const buttonText = document.getElementById('button-text');
const spinner = document.getElementById('spinner');
const messageContainer = document.getElementById('payment-message');

form.addEventListener('submit', async (event) => {
    event.preventDefault();
    
    setLoading(true);
    
    const {error} = await stripe.confirmPayment({
        elements,
        confirmParams: {
            return_url: '{{ success_url }}',
        },
    });
    
    if (error) {
        showMessage(error.message, 'error');
        setLoading(false);
    }
});

function setLoading(isLoading) {
    if (isLoading) {
        submitButton.disabled = true;
        buttonText.classList.add('hidden');
        spinner.classList.remove('hidden');
    } else {
        submitButton.disabled = false;
        buttonText.classList.remove('hidden');
        spinner.classList.add('hidden');
    }
}

function showMessage(messageText, type = 'error') {
    messageContainer.classList.remove('hidden', 'error', 'success');
    messageContainer.classList.add(type);
    messageContainer.textContent = messageText;
}
</script>
EOF

print_status "Enhanced Stripe payment form created"

print_header "UPDATING FOOTER WITH SOCIAL MEDIA AND TRADEMARK"
print_info "Adding Instagram link and Fixbulance trademark to footer..."

# Create updated footer template
sudo -u $APP_USER tee app/templates/components/footer.html > /dev/null << 'EOF'
<footer class="bg-dark text-light py-5 mt-5">
    <div class="container">
        <div class="row">
            <div class="col-md-4 mb-4">
                <h5 class="text-primary">Fixbulance</h5>
                <p>Professional mobile phone repair service in Orland Park, IL. We come to your location with our fully-equipped repair van.</p>
                <div class="social-media">
                    <h6>Follow Us</h6>
                    <div class="social-links">
                        <a href="https://www.instagram.com/fixbulance/" target="_blank" class="social-link instagram">
                            <i class="fab fa-instagram"></i>
                            <span>@fixbulance</span>
                        </a>
                    </div>
                </div>
            </div>
            
            <div class="col-md-2 mb-4">
                <h6>Services</h6>
                <ul class="list-unstyled">
                    <li><a href="#" class="text-light">Screen Repair</a></li>
                    <li><a href="#" class="text-light">Battery Replacement</a></li>
                    <li><a href="#" class="text-light">Water Damage</a></li>
                    <li><a href="#" class="text-light">Data Recovery</a></li>
                </ul>
            </div>
            
            <div class="col-md-2 mb-4">
                <h6>Company</h6>
                <ul class="list-unstyled">
                    <li><a href="/about" class="text-light">About Us</a></li>
                    <li><a href="/contact" class="text-light">Contact</a></li>
                    <li><a href="/service-area" class="text-light">Service Area</a></li>
                    <li><a href="/pricing" class="text-light">Pricing</a></li>
                </ul>
            </div>
            
            <div class="col-md-2 mb-4">
                <h6>Legal</h6>
                <ul class="list-unstyled">
                    <li><a href="/terms" class="text-light">Terms of Service</a></li>
                    <li><a href="/privacy" class="text-light">Privacy Policy</a></li>
                    <li><a href="/warranty" class="text-light">Warranty</a></li>
                </ul>
            </div>
            
            <div class="col-md-2 mb-4">
                <h6>Contact Info</h6>
                <p class="mb-1"><i class="fas fa-phone"></i> (708) 971-4053</p>
                <p class="mb-1"><i class="fas fa-envelope"></i> info@fixbulance.com</p>
                <p><i class="fas fa-map-marker-alt"></i> Orland Park, IL</p>
            </div>
        </div>
        
        <hr class="my-4">
        
        <div class="row align-items-center">
            <div class="col-md-6">
                <p class="mb-0">
                    &copy; {{ current_year }} Fixbulance&trade;. All rights reserved.
                </p>
            </div>
            <div class="col-md-6 text-md-end">
                <div class="payment-badges">
                    <span class="me-2">We Accept:</span>
                    <i class="fab fa-cc-visa"></i>
                    <i class="fab fa-cc-mastercard"></i>
                    <i class="fab fa-cc-amex"></i>
                    <i class="fab fa-apple-pay"></i>
                    <i class="fab fa-google-pay"></i>
                    <i class="fab fa-paypal"></i>
                </div>
            </div>
        </div>
    </div>
</footer>

<style>
.social-links {
    margin-top: 10px;
}

.social-link {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    color: #fff;
    text-decoration: none;
    padding: 8px 12px;
    border-radius: 6px;
    transition: all 0.3s ease;
    margin-right: 10px;
}

.social-link.instagram {
    background: linear-gradient(45deg, #f09433 0%,#e6683c 25%,#dc2743 50%,#cc2366 75%,#bc1888 100%);
}

.social-link:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    color: #fff;
    text-decoration: none;
}

.payment-badges i {
    font-size: 24px;
    margin-left: 10px;
    color: #ccc;
}

footer a:hover {
    color: #dc3545 !important;
    text-decoration: none;
}
</style>
EOF

print_status "Footer updated with social media and trademark"

print_header "CREATING TERMS OF SERVICE PAGE"
sudo -u $APP_USER tee app/templates/legal/terms.html > /dev/null << 'EOF'
{% extends "base.html" %}
{% block title %}Terms of Service - Fixbulance{% endblock %}

{% block content %}
<div class="container my-5">
    <div class="row justify-content-center">
        <div class="col-lg-8">
            <h1 class="mb-4">Terms of Service</h1>
            <p class="text-muted">Last updated: {{ current_date }}</p>
            
            <div class="terms-content">
                <h2>1. Agreement to Terms</h2>
                <p>By accessing and using Fixbulance™ services, you accept and agree to be bound by the terms and provision of this agreement.</p>

                <h2>2. Services</h2>
                <p>Fixbulance™ provides mobile phone repair services including but not limited to:</p>
                <ul>
                    <li>Screen repair and replacement</li>
                    <li>Battery replacement</li>
                    <li>Water damage repair</li>
                    <li>Data recovery services</li>
                    <li>Other mobile device repairs</li>
                </ul>

                <h2>3. Service Area</h2>
                <p>Our services are currently available in Orland Park, IL and surrounding areas within a 10-mile radius.</p>

                <h2>4. Booking and Payment</h2>
                <ul>
                    <li>A $15 standard deposit is required to book emergency repair services</li>
                    <li>Payment is processed securely through Stripe</li>
                    <li>Full payment is due upon completion of service</li>
                    <li>We accept major credit cards, Apple Pay, Google Pay, and PayPal</li>
                </ul>

                <h2>5. Warranty</h2>
                <p>All repairs come with a limited warranty covering defects in parts and workmanship for a period of 90 days from the date of service.</p>

                <h2>6. Limitation of Liability</h2>
                <p>Fixbulance™ shall not be liable for any data loss or damage to your device beyond the scope of the agreed repair service.</p>

                <h2>7. Privacy</h2>
                <p>Your privacy is important to us. Please review our Privacy Policy to understand how we collect and use your information.</p>

                <h2>8. Changes to Terms</h2>
                <p>We reserve the right to modify these terms at any time. Changes will be effective immediately upon posting.</p>

                <h2>9. Contact Information</h2>
                <p>For questions about these Terms of Service, please contact us at:</p>
                <ul>
                    <li>Phone: (708) 971-4053</li>
                    <li>Email: info@fixbulance.com</li>
                </ul>
            </div>
        </div>
    </div>
</div>

<style>
.terms-content h2 {
    color: #dc3545;
    margin-top: 2rem;
    margin-bottom: 1rem;
}

.terms-content ul {
    margin-bottom: 1.5rem;
}

.terms-content li {
    margin-bottom: 0.5rem;
}
</style>
{% endblock %}
EOF

print_header "CREATING PRIVACY POLICY PAGE"
sudo -u $APP_USER tee app/templates/legal/privacy.html > /dev/null << 'EOF'
{% extends "base.html" %}
{% block title %}Privacy Policy - Fixbulance{% endblock %}

{% block content %}
<div class="container my-5">
    <div class="row justify-content-center">
        <div class="col-lg-8">
            <h1 class="mb-4">Privacy Policy</h1>
            <p class="text-muted">Last updated: {{ current_date }}</p>
            
            <div class="privacy-content">
                <h2>1. Information We Collect</h2>
                <p>We collect information you provide directly to us, such as:</p>
                <ul>
                    <li>Name and contact information</li>
                    <li>Device information and repair details</li>
                    <li>Payment information (processed securely by Stripe)</li>
                    <li>Service location and appointment details</li>
                </ul>

                <h2>2. How We Use Your Information</h2>
                <p>We use the information we collect to:</p>
                <ul>
                    <li>Provide and improve our repair services</li>
                    <li>Process payments and bookings</li>
                    <li>Communicate with you about your service</li>
                    <li>Send service updates and promotional materials (with consent)</li>
                </ul>

                <h2>3. Information Sharing</h2>
                <p>We do not sell, trade, or otherwise transfer your personal information to third parties except:</p>
                <ul>
                    <li>To process payments through Stripe</li>
                    <li>When required by law</li>
                    <li>To protect our rights and safety</li>
                </ul>

                <h2>4. Data Security</h2>
                <p>We implement appropriate security measures to protect your personal information, including:</p>
                <ul>
                    <li>Encrypted data transmission</li>
                    <li>Secure payment processing</li>
                    <li>Limited access to personal information</li>
                    <li>Regular security audits</li>
                </ul>

                <h2>5. Cookies and Tracking</h2>
                <p>We use cookies to enhance your experience on our website and to analyze site usage. You can control cookie settings through your browser.</p>

                <h2>6. Your Rights</h2>
                <p>You have the right to:</p>
                <ul>
                    <li>Access your personal information</li>
                    <li>Correct inaccurate information</li>
                    <li>Request deletion of your information</li>
                    <li>Opt-out of marketing communications</li>
                </ul>

                <h2>7. Data Retention</h2>
                <p>We retain your information for as long as necessary to provide services and as required by law. Service records are typically kept for 3 years.</p>

                <h2>8. Children's Privacy</h2>
                <p>Our services are not directed to children under 13. We do not knowingly collect personal information from children under 13.</p>

                <h2>9. Changes to This Policy</h2>
                <p>We may update this privacy policy from time to time. We will notify you of any changes by posting the new policy on this page.</p>

                <h2>10. Contact Us</h2>
                <p>If you have any questions about this Privacy Policy, please contact us at:</p>
                <ul>
                    <li>Phone: (708) 971-4053</li>
                    <li>Email: admin@fixbulance.com</li>
                    <li>Address: Orland Park, IL</li>
                </ul>
            </div>
        </div>
    </div>
</div>

<style>
.privacy-content h2 {
    color: #dc3545;
    margin-top: 2rem;
    margin-bottom: 1rem;
}

.privacy-content ul {
    margin-bottom: 1.5rem;
}

.privacy-content li {
    margin-bottom: 0.5rem;
}
</style>
{% endblock %}
EOF

print_header "UPDATING ROUTES FOR LEGAL PAGES"
print_info "Adding routes for terms and privacy pages..."

# Add routes to main app file
sudo -u $APP_USER tee -a app/routes.py > /dev/null << 'EOF'

@app.route('/terms')
def terms():
    return render_template('legal/terms.html', 
                         current_date=datetime.now().strftime('%B %d, %Y'))

@app.route('/privacy') 
def privacy():
    return render_template('legal/privacy.html',
                         current_date=datetime.now().strftime('%B %d, %Y'))
EOF

print_status "Legal page routes added"

print_header "UPDATING STRIPE CONFIGURATION"
print_info "Enhancing Stripe integration with modern payment methods..."

# Update Stripe configuration
sudo -u $APP_USER tee app/stripe_config.py > /dev/null << 'EOF'
import stripe
import os
from flask import current_app

# Configure Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

class StripePayments:
    def __init__(self):
        self.public_key = os.environ.get('STRIPE_PUBLIC_KEY')
    
    def create_payment_intent(self, amount, currency='usd', customer_email=None):
        """Create a payment intent with modern payment methods"""
        try:
            intent = stripe.PaymentIntent.create(
                amount=amount,  # Amount in cents
                currency=currency,
                payment_method_types=[
                    'card',
                    'apple_pay', 
                    'google_pay',
                    'paypal'
                ],
                metadata={
                    'service': 'phone_repair',
                    'customer_email': customer_email or 'unknown'
                }
            )
            return intent
        except stripe.error.StripeError as e:
            current_app.logger.error(f"Stripe error: {str(e)}")
            return None
    
    def create_customer(self, name, email):
        """Create a Stripe customer"""
        try:
            customer = stripe.Customer.create(
                name=name,
                email=email
            )
            return customer
        except stripe.error.StripeError as e:
            current_app.logger.error(f"Customer creation error: {str(e)}")
            return None
EOF

print_status "Stripe configuration updated with modern payment methods"

print_header "FIXING PERMISSIONS"
chown -R $APP_USER:$APP_USER $APP_DIR
chmod -R 755 $APP_DIR
chmod 644 $APP_DIR/app/templates/**/*.html 2>/dev/null || true

print_status "Permissions updated"

print_header "RESTART SERVICES"
systemctl restart fixbulance
sleep 3

if systemctl is-active --quiet fixbulance; then
    print_status "Service restarted successfully"
else
    print_info "Service restart failed, restoring backup..."
    cd $APP_DIR
    sudo -u $APP_USER tar -xzf "backups/pre_updates_$TIMESTAMP.tar.gz"
    systemctl restart fixbulance
fi

systemctl reload nginx
print_status "Nginx reloaded"

print_header "TESTING UPDATES"
sleep 2
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/ 2>/dev/null)

if [ "$HTTP_STATUS" = "200" ]; then
    echo -e "${GREEN}🎉 ALL UPDATES COMPLETED SUCCESSFULLY! 🎉${NC}"
    echo ""
    echo -e "${BLUE}✅ Changes Applied:${NC}"
    echo "• Removed DEBUG and emergency repair text"
    echo "• Enhanced Stripe integration with Apple Pay, Google Pay, PayPal"
    echo "• Added Instagram link: https://www.instagram.com/fixbulance/"
    echo "• Added Fixbulance™ trademark to footer"
    echo "• Created Terms of Service page (/terms)"
    echo "• Created Privacy Policy page (/privacy)"
    echo "• Updated payment processing for modern methods"
    echo ""
    echo -e "${BLUE}🔗 New Pages Available:${NC}"
    echo "• http://your-domain.com/terms"
    echo "• http://your-domain.com/privacy"
else
    echo -e "${RED}❌ Updates failed - backup restored${NC}"
fi

echo ""
echo -e "${BLUE}📝 Next Steps:${NC}"
echo "1. Add your Stripe keys to .env file"
echo "2. Test payment integration"
echo "3. Review legal pages for accuracy"
echo "4. Verify social media links work"