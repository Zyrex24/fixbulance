"""
Payment processing service using Stripe
Handles deposit payments and final payment processing for repair bookings
"""

import stripe
from flask import current_app, url_for
from decimal import Decimal
import logging

class PaymentService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def configure_stripe(self):
        """Configure Stripe with API keys"""
        try:
            stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')
            return True
        except Exception as e:
            self.logger.error(f"Stripe configuration error: {str(e)}")
            return False
    
    def create_deposit_payment_intent(self, booking, customer_email):
        """Create Stripe Payment Intent for $15 deposit"""
        try:
            if not self.configure_stripe():
                raise Exception("Stripe not configured")
            
            # Create payment intent for $15 deposit
            deposit_amount = int(booking.deposit_amount * 100)  # Convert to cents
            
            payment_intent = stripe.PaymentIntent.create(
                amount=deposit_amount,
                currency='usd',
                customer_email=customer_email,
                metadata={
                    'booking_id': booking.id,
                    'booking_reference': booking.booking_reference,
                    'payment_type': 'deposit',
                    'device_type': booking.device_type,
                    'service_name': booking.service.name if booking.service else 'Unknown'
                },
                description=f"Fixbulance Deposit - {booking.booking_reference}",
                receipt_email=customer_email,
                setup_future_usage='off_session'  # For potential future payments
            )
            
            return {
                'success': True,
                'client_secret': payment_intent.client_secret,
                'payment_intent_id': payment_intent.id,
                'amount': deposit_amount
            }
            
        except stripe.error.StripeError as e:
            self.logger.error(f"Stripe error creating payment intent: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'stripe_error'
            }
        except Exception as e:
            self.logger.error(f"Payment intent creation error: {str(e)}")
            return {
                'success': False,
                'error': 'Payment system temporarily unavailable',
                'error_type': 'system_error'
            }
    
    def create_final_payment_intent(self, booking, customer_email):
        """Create Stripe Payment Intent for final payment (service cost - deposit)"""
        try:
            if not self.configure_stripe():
                raise Exception("Stripe not configured")
            
            # Calculate final payment amount
            final_amount = float(booking.service_price) - float(booking.deposit_amount)
            final_amount_cents = int(final_amount * 100)
            
            if final_amount_cents <= 0:
                return {
                    'success': True,
                    'no_payment_required': True,
                    'message': 'No additional payment required'
                }
            
            payment_intent = stripe.PaymentIntent.create(
                amount=final_amount_cents,
                currency='usd',
                customer_email=customer_email,
                metadata={
                    'booking_id': booking.id,
                    'booking_reference': booking.booking_reference,
                    'payment_type': 'final',
                    'device_type': booking.device_type,
                    'service_name': booking.service.name if booking.service else 'Unknown',
                    'total_service_cost': str(booking.service_price),
                    'deposit_paid': str(booking.deposit_amount)
                },
                description=f"Fixbulance Final Payment - {booking.booking_reference}",
                receipt_email=customer_email
            )
            
            return {
                'success': True,
                'client_secret': payment_intent.client_secret,
                'payment_intent_id': payment_intent.id,
                'amount': final_amount_cents,
                'final_payment_amount': final_amount
            }
            
        except stripe.error.StripeError as e:
            self.logger.error(f"Stripe error creating final payment intent: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'stripe_error'
            }
        except Exception as e:
            self.logger.error(f"Final payment intent creation error: {str(e)}")
            return {
                'success': False,
                'error': 'Payment system temporarily unavailable',
                'error_type': 'system_error'
            }
    
    def confirm_payment(self, payment_intent_id):
        """Confirm payment was successful"""
        try:
            if not self.configure_stripe():
                raise Exception("Stripe not configured")
            
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            return {
                'success': True,
                'status': payment_intent.status,
                'paid': payment_intent.status == 'succeeded',
                'amount_received': payment_intent.amount_received,
                'metadata': payment_intent.metadata
            }
            
        except stripe.error.StripeError as e:
            self.logger.error(f"Stripe error confirming payment: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'stripe_error'
            }
        except Exception as e:
            self.logger.error(f"Payment confirmation error: {str(e)}")
            return {
                'success': False,
                'error': 'Unable to confirm payment',
                'error_type': 'system_error'
            }
    
    def create_checkout_session(self, booking, customer_email, success_url, cancel_url):
        """Create Stripe Checkout Session for deposit payment"""
        try:
            if not self.configure_stripe():
                raise Exception("Stripe not configured")
            
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': f'Fixbulance Emergency Repair Deposit',
                            'description': f'{booking.device_type} {booking.service.name if booking.service else "Repair"} - Booking {booking.booking_reference}',
                            'images': [current_app.config.get('LOGO_URL', '')]
                        },
                        'unit_amount': int(booking.deposit_amount * 100)
                    },
                    'quantity': 1
                }],
                mode='payment',
                customer_email=customer_email,
                success_url=success_url + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=cancel_url,
                metadata={
                    'booking_id': booking.id,
                    'booking_reference': booking.booking_reference,
                    'payment_type': 'deposit'
                }
            )
            
            return {
                'success': True,
                'checkout_url': session.url,
                'session_id': session.id
            }
            
        except stripe.error.StripeError as e:
            self.logger.error(f"Stripe error creating checkout session: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'stripe_error'
            }
        except Exception as e:
            self.logger.error(f"Checkout session creation error: {str(e)}")
            return {
                'success': False,
                'error': 'Payment system temporarily unavailable',
                'error_type': 'system_error'
            }
    
    def retrieve_checkout_session(self, session_id):
        """Retrieve checkout session details"""
        try:
            if not self.configure_stripe():
                raise Exception("Stripe not configured")
            
            session = stripe.checkout.Session.retrieve(session_id)
            
            return {
                'success': True,
                'session': session,
                'payment_status': session.payment_status,
                'customer_email': session.customer_email,
                'metadata': session.metadata
            }
            
        except stripe.error.StripeError as e:
            self.logger.error(f"Stripe error retrieving session: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'stripe_error'
            }
        except Exception as e:
            self.logger.error(f"Session retrieval error: {str(e)}")
            return {
                'success': False,
                'error': 'Unable to retrieve payment information',
                'error_type': 'system_error'
            }
    
    def process_webhook(self, payload, signature):
        """Process Stripe webhook events"""
        try:
            endpoint_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET')
            
            if endpoint_secret:
                event = stripe.Webhook.construct_event(
                    payload, signature, endpoint_secret
                )
            else:
                # For testing without webhook secret
                import json
                event = json.loads(payload)
            
            # Handle different event types
            if event['type'] == 'payment_intent.succeeded':
                payment_intent = event['data']['object']
                return self._handle_payment_success(payment_intent)
            
            elif event['type'] == 'payment_intent.payment_failed':
                payment_intent = event['data']['object']
                return self._handle_payment_failure(payment_intent)
            
            elif event['type'] == 'checkout.session.completed':
                session = event['data']['object']
                return self._handle_checkout_completion(session)
            
            else:
                self.logger.info(f"Unhandled webhook event: {event['type']}")
                return {'success': True, 'message': 'Event acknowledged'}
            
        except ValueError as e:
            self.logger.error(f"Invalid payload in webhook: {str(e)}")
            return {'success': False, 'error': 'Invalid payload'}
        
        except stripe.error.SignatureVerificationError as e:
            self.logger.error(f"Invalid signature in webhook: {str(e)}")
            return {'success': False, 'error': 'Invalid signature'}
        
        except Exception as e:
            self.logger.error(f"Webhook processing error: {str(e)}")
            return {'success': False, 'error': 'Webhook processing failed'}
    
    def _handle_payment_success(self, payment_intent):
        """Handle successful payment"""
        try:
            booking_id = payment_intent.metadata.get('booking_id')
            payment_type = payment_intent.metadata.get('payment_type', 'deposit')
            
            if booking_id:
                from app.models.booking import Booking
                booking = Booking.query.get(booking_id)
                
                if booking:
                    if payment_type == 'deposit':
                        booking.payment_status = 'deposit_paid'
                        booking.status = 'confirmed'
                    elif payment_type == 'final':
                        booking.payment_status = 'paid'
                        booking.status = 'ready_for_service'
                    
                    booking.payment_intent_id = payment_intent.id
                    
                    from app import db
                    db.session.commit()
                    
                    self.logger.info(f"Payment processed for booking {booking_id}: {payment_type}")
                    
                    return {
                        'success': True,
                        'booking_id': booking_id,
                        'payment_type': payment_type,
                        'new_status': booking.status
                    }
            
            return {'success': True, 'message': 'Payment processed'}
            
        except Exception as e:
            self.logger.error(f"Error handling payment success: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _handle_payment_failure(self, payment_intent):
        """Handle failed payment"""
        try:
            booking_id = payment_intent.metadata.get('booking_id')
            
            if booking_id:
                from app.models.booking import Booking
                booking = Booking.query.get(booking_id)
                
                if booking:
                    booking.payment_status = 'failed'
                    booking.status = 'payment_failed'
                    
                    from app import db
                    db.session.commit()
                    
                    self.logger.warning(f"Payment failed for booking {booking_id}")
            
            return {'success': True, 'message': 'Payment failure processed'}
            
        except Exception as e:
            self.logger.error(f"Error handling payment failure: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _handle_checkout_completion(self, session):
        """Handle completed checkout session"""
        try:
            booking_id = session.metadata.get('booking_id')
            
            if booking_id:
                from app.models.booking import Booking
                booking = Booking.query.get(booking_id)
                
                if booking and session.payment_status == 'paid':
                    booking.payment_status = 'deposit_paid'
                    booking.status = 'confirmed'
                    booking.stripe_session_id = session.id
                    
                    from app import db
                    db.session.commit()
                    
                    self.logger.info(f"Checkout completed for booking {booking_id}")
            
            return {'success': True, 'message': 'Checkout completion processed'}
            
        except Exception as e:
            self.logger.error(f"Error handling checkout completion: {str(e)}")
            return {'success': False, 'error': str(e)}

# Global payment service instance
payment_service = PaymentService() 