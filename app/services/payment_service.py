import stripe
import logging
from flask import current_app
from datetime import datetime
from app import db
from app.models.payment import Payment
from app.models.booking import Booking
from app.models.user import User

# Configure logging
logger = logging.getLogger(__name__)

class StripePaymentService:
    """Service for handling Stripe payment operations"""
    
    def __init__(self):
        """Initialize service (Stripe configured on first use)"""
        self._stripe_configured = False
        
    def _ensure_stripe_configured(self):
        """Configure Stripe API key when needed"""
        if not self._stripe_configured:
            from flask import current_app
            stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')
            self._stripe_configured = True
        
    def get_or_create_customer(self, user):
        """Get or create Stripe customer for user"""
        self._ensure_stripe_configured()
        try:
            # Check if user already has a Stripe customer ID
            if hasattr(user, 'stripe_customer_id') and user.stripe_customer_id:
                try:
                    customer = stripe.Customer.retrieve(user.stripe_customer_id)
                    return customer
                except stripe.error.InvalidRequestError:
                    # Customer doesn't exist, create new one
                    pass
            
            # Create new Stripe customer
            customer_data = {
                'email': user.email,
                'name': f"{user.first_name} {user.last_name}",
                'phone': user.phone,
                'metadata': {
                    'user_id': user.id,
                    'business': 'Fixbulance',
                    'created_via': 'flask_app'
                }
            }
            
            # Add address if available
            if user.address:
                customer_data['address'] = {
                    'line1': user.address,
                    'city': user.city or '',
                    'state': user.state or 'IL',
                    'postal_code': user.zip_code or '',
                    'country': 'US'
                }
            
            customer = stripe.Customer.create(**customer_data)
            
            # Save customer ID to user record
            user.stripe_customer_id = customer.id
            db.session.commit()
            
            logger.info(f"Created Stripe customer {customer.id} for user {user.id}")
            return customer
            
        except Exception as e:
            logger.error(f"Failed to create Stripe customer for user {user.id}: {str(e)}")
            raise
    
    def create_payment_intent(self, booking, payment_type='deposit', amount=None):
        """Create Stripe Payment Intent for booking"""
        try:
            # Determine payment amount
            if payment_type == 'deposit':
                payment_amount = current_app.config.get('DEPOSIT_AMOUNT', 15.00)
            elif payment_type == 'final':
                if amount:
                    payment_amount = float(amount)
                else:
                    # Calculate final payment (service cost - deposit)
                    service_cost = float(booking.service.base_price) if booking.service else 50.00
                    deposit_paid = float(booking.deposit_amount or 15.00)
                    payment_amount = max(service_cost - deposit_paid, 0.00)
            else:
                raise ValueError(f"Invalid payment type: {payment_type}")
            
            # Convert to cents for Stripe
            amount_cents = int(payment_amount * 100)
            
            # Get or create Stripe customer
            customer = self.get_or_create_customer(booking.customer)
            
            # Create payment description
            device_info = f"{booking.device_model}" if booking.device_model else "Mobile Device"
            service_info = booking.service.display_name if booking.service else "Repair Service"
            description = f"Fixbulance {payment_type.title()} - {device_info} {service_info}"
            
            # Create Payment Intent
            intent_data = {
                'amount': amount_cents,
                'currency': 'usd',
                'customer': customer.id,
                'description': description,
                'receipt_email': booking.customer.email,
                'metadata': {
                    'booking_id': booking.id,
                    'user_id': booking.customer.id,
                    'payment_type': payment_type,
                    'device_type': getattr(booking, 'device_type', 'Unknown'),
                    'service_name': service_info,
                    'business': 'Fixbulance',
                    'ahmed_phone': current_app.config.get('BUSINESS_PHONE_DISPLAY', '+1 (708) 737-2873')
                },
                'automatic_payment_methods': {
                    'enabled': True,
                }
            }
            
            # Create Payment Intent
            payment_intent = stripe.PaymentIntent.create(**intent_data)
            
            # Create Payment record in database
            payment = Payment(
                booking_id=booking.id,
                user_id=booking.customer.id,
                stripe_payment_intent_id=payment_intent.id,
                stripe_customer_id=customer.id,
                amount=payment_amount,
                currency='usd',
                payment_type=payment_type,
                status='pending',
                description=description,
                receipt_email=booking.customer.email,
                device_type=getattr(booking, 'device_type', 'Unknown'),
                service_name=service_info,
                customer_name=f"{booking.customer.first_name} {booking.customer.last_name}",
                customer_phone=booking.customer.phone
            )
            
            db.session.add(payment)
            
            # Update booking with payment intent
            if payment_type == 'deposit':
                booking.stripe_deposit_payment_id = payment_intent.id
            else:
                booking.stripe_final_payment_id = payment_intent.id
            
            db.session.commit()
            
            logger.info(f"Created payment intent {payment_intent.id} for booking {booking.id}")
            
            return {
                'payment_intent': payment_intent,
                'payment': payment,
                'client_secret': payment_intent.client_secret,
                'amount': payment_amount
            }
            
        except Exception as e:
            logger.error(f"Failed to create payment intent for booking {booking.id}: {str(e)}")
            db.session.rollback()
            raise
    
    def confirm_payment(self, payment_intent_id):
        """Process payment confirmation from webhook"""
        try:
            # Retrieve payment intent from Stripe
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            # Find payment record in database
            payment = Payment.query.filter_by(
                stripe_payment_intent_id=payment_intent_id
            ).first()
            
            if not payment:
                logger.error(f"Payment record not found for intent {payment_intent_id}")
                return None
            
            # Update payment status
            payment.update_status(
                new_status='succeeded',
                processed_at=datetime.utcnow()
            )
            
            # Update payment method information
            if payment_intent.charges.data:
                charge = payment_intent.charges.data[0]
                payment.stripe_charge_id = charge.id
                payment.receipt_url = charge.receipt_url
                
                if charge.payment_method_details.card:
                    card = charge.payment_method_details.card
                    payment.payment_method_type = 'card'
                    payment.card_brand = card.brand
                    payment.card_last4 = card.last4
            
            # Update booking payment status
            booking = payment.booking
            if payment.payment_type == 'deposit':
                booking.payment_status = 'deposit_paid'
                # Update booking status to deposit_paid when deposit is received
                if booking.status == 'pending':
                    booking.update_status('deposit_paid')
            elif payment.payment_type == 'final':
                booking.payment_status = 'balance_paid'
                # Mark booking as completed when final payment is made
                if booking.status in ['deposit_paid', 'confirmed', 'in_progress']:
                    booking.update_status('completed')
            
            db.session.commit()
            
            logger.info(f"Confirmed payment {payment.id} for booking {booking.id}")
            
            return payment
            
        except Exception as e:
            logger.error(f"Failed to confirm payment {payment_intent_id}: {str(e)}")
            db.session.rollback()
            raise
    
    def handle_payment_failure(self, payment_intent_id, error_message=None):
        """Handle failed payment"""
        try:
            payment = Payment.query.filter_by(
                stripe_payment_intent_id=payment_intent_id
            ).first()
            
            if payment:
                payment.update_status(
                    new_status='failed',
                    error_message=error_message,
                    processed_at=datetime.utcnow()
                )
                db.session.commit()
                
                logger.info(f"Marked payment {payment.id} as failed")
                return payment
                
        except Exception as e:
            logger.error(f"Failed to handle payment failure {payment_intent_id}: {str(e)}")
            db.session.rollback()
            raise
    
    def create_refund(self, payment_id, amount=None, reason='requested_by_customer'):
        """Create refund for payment"""
        try:
            payment = Payment.query.get(payment_id)
            if not payment:
                raise ValueError(f"Payment {payment_id} not found")
            
            if not payment.is_refundable:
                raise ValueError(f"Payment {payment_id} is not refundable")
            
            # Determine refund amount
            refund_amount = amount or (payment.amount - payment.refunded_amount)
            refund_amount_cents = int(float(refund_amount) * 100)
            
            # Create refund in Stripe
            refund = stripe.Refund.create(
                payment_intent=payment.stripe_payment_intent_id,
                amount=refund_amount_cents,
                reason=reason,
                metadata={
                    'booking_id': payment.booking_id,
                    'refunded_by': 'admin',
                    'business': 'Fixbulance'
                }
            )
            
            # Update payment record
            payment.create_refund(
                amount=refund_amount,
                reason=reason,
                refunded_by_user_id=None  # Will be set by admin user
            )
            
            # Update booking status if fully refunded
            if payment.status == 'refunded':
                booking = payment.booking
                booking.payment_status = 'refunded'
                if booking.status not in ['completed', 'cancelled']:
                    booking.update_status('cancelled')
            
            db.session.commit()
            
            logger.info(f"Created refund for payment {payment.id}: ${refund_amount}")
            
            return refund
            
        except Exception as e:
            logger.error(f"Failed to create refund for payment {payment_id}: {str(e)}")
            db.session.rollback()
            raise
    
    def get_payment_methods(self, customer_id):
        """Get saved payment methods for customer"""
        try:
            payment_methods = stripe.PaymentMethod.list(
                customer=customer_id,
                type='card'
            )
            return payment_methods.data
        except Exception as e:
            logger.error(f"Failed to get payment methods for customer {customer_id}: {str(e)}")
            return []
    
    def get_payment_analytics(self, start_date=None, end_date=None):
        """Get payment analytics for admin dashboard"""
        try:
            query = Payment.query.filter(Payment.status == 'succeeded')
            
            if start_date:
                query = query.filter(Payment.processed_at >= start_date)
            if end_date:
                query = query.filter(Payment.processed_at <= end_date)
            
            payments = query.all()
            
            total_revenue = sum(float(p.amount) for p in payments)
            deposit_revenue = sum(float(p.amount) for p in payments if p.payment_type == 'deposit')
            final_revenue = sum(float(p.amount) for p in payments if p.payment_type == 'final')
            
            return {
                'total_payments': len(payments),
                'total_revenue': total_revenue,
                'deposit_revenue': deposit_revenue,
                'final_revenue': final_revenue,
                'average_payment': total_revenue / len(payments) if payments else 0,
                'payments': [p.to_dict() for p in payments]
            }
            
        except Exception as e:
            logger.error(f"Failed to get payment analytics: {str(e)}")
            return {}

# Lazy initialization - only create when needed
def get_payment_service():
    """Get payment service instance (lazy initialization)"""
    if not hasattr(get_payment_service, '_instance'):
        get_payment_service._instance = StripePaymentService()
    return get_payment_service._instance

# Export for convenience - lazy initialization
payment_service = None

def init_payment_service():
    global payment_service
    if payment_service is None:
        payment_service = StripePaymentService()
    return payment_service 