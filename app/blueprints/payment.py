from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
import stripe
import logging
from datetime import datetime, timezone
from app import db
from app.models.booking import Booking
from app.models.payment import Payment
from app.services.payment_service import init_payment_service
from app.services.email_service import EmailService

payment_bp = Blueprint('payment', __name__)
logger = logging.getLogger(__name__)

@payment_bp.route('/create-payment-intent', methods=['POST'])
@login_required
def create_payment_intent():
    """Create Stripe Payment Intent for booking deposit"""
    try:
        data = request.get_json()
        booking_id = data.get('booking_id')
        payment_type = data.get('payment_type', 'deposit')
        
        # Get booking
        booking = Booking.query.get(booking_id)
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        # Verify user owns booking
        if booking.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Create payment intent
        payment_service = init_payment_service()
        result = payment_service.create_payment_intent(booking, payment_type)
        
        return jsonify({
            'client_secret': result['client_secret'],
            'amount': result['amount'],
            'payment_intent_id': result['payment_intent'].id
        })
        
    except Exception as e:
        logger.error(f"Failed to create payment intent: {str(e)}")
        return jsonify({'error': 'Failed to create payment intent'}), 500

@payment_bp.route('/booking/<int:booking_id>/payment')
@login_required 
def booking_payment(booking_id):
    """Display payment page for booking"""
    booking = Booking.query.get_or_404(booking_id)
    
    # Verify user owns booking
    if booking.user_id != current_user.id:
        flash('You can only pay for your own bookings.', 'error')
        return redirect(url_for('booking.my_bookings'))
    
    # Check if deposit already paid
    if booking.payment_status in ['deposit_paid', 'balance_paid']:
        flash('Payment has already been processed for this booking.', 'info')
        return redirect(url_for('booking.view_booking', booking_id=booking.id))
    
    return render_template('booking/payment.html', 
                         booking=booking,
                         stripe_publishable_key=current_app.config.get('STRIPE_PUBLISHABLE_KEY'))

@payment_bp.route('/payment-success')
@login_required
def payment_success():
    """Payment success page"""
    payment_intent_id = request.args.get('payment_intent')
    
    if payment_intent_id:
        # Get payment from database
        payment = Payment.query.filter_by(
            stripe_payment_intent_id=payment_intent_id
        ).first()
        
        if payment and payment.user_id == current_user.id:
            # Auto-confirm payment in development mode (simulate webhook)
            if current_app.config.get('ENV') != 'production' and payment.status == 'pending':
                try:
                    payment_service = init_payment_service()
                    # Simulate payment confirmation (without Stripe API call)
                    payment.status = 'succeeded'
                    payment.processed_at = datetime.now(timezone.utc)
                    
                    # Update booking status
                    booking = payment.booking
                    if payment.payment_type == 'deposit':
                        booking.payment_status = 'deposit_paid'
                        if booking.status == 'pending':
                            booking.update_status('deposit_paid')
                    
                    db.session.commit()
                    logger.info(f"Auto-confirmed payment {payment.id} for booking {booking.id}")
                    
                    # Send deposit receipt email
                    try:
                        EmailService.send_deposit_receipt(booking, payment)
                        logger.info(f"Deposit receipt email sent for booking {booking.id}")
                    except Exception as e:
                        logger.error(f"Failed to send deposit receipt email: {str(e)}")
                    
                    # Send admin notification
                    try:
                        EmailService.send_admin_notification(booking, 'payment_received')
                        logger.info(f"Admin payment notification sent for booking {booking.id}")
                    except Exception as e:
                        logger.error(f"Failed to send admin payment notification: {str(e)}")
                    
                except Exception as e:
                    logger.error(f"Failed to auto-confirm payment: {str(e)}")
                    db.session.rollback()
            
            return render_template('booking/payment_success.html', 
                                 payment=payment, 
                                 booking=payment.booking)
    
    return render_template('booking/payment_success.html')

@payment_bp.route('/payment-cancel')
@login_required
def payment_cancel():
    """Payment cancelled page"""
    booking_id = request.args.get('booking_id')
    if booking_id:
        booking = Booking.query.get(booking_id)
        if booking and booking.user_id == current_user.id:
            return render_template('booking/payment_cancel.html', booking=booking)
    
    return render_template('booking/payment_cancel.html')

@payment_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks"""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    endpoint_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        logger.error("Invalid payload in webhook")
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid signature in webhook")
        return jsonify({'error': 'Invalid signature'}), 400
    
    # Handle the event
    try:
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            payment_service = init_payment_service()
            payment = payment_service.confirm_payment(payment_intent['id'])
            
            if payment:
                logger.info(f"Payment confirmed via webhook: {payment.id}")
                
                # Send deposit receipt email
                try:
                    EmailService.send_deposit_receipt(payment.booking, payment)
                    logger.info(f"Deposit receipt email sent for booking {payment.booking.id}")
                except Exception as e:
                    logger.error(f"Failed to send deposit receipt email: {str(e)}")
                
                # Send admin notification
                try:
                    EmailService.send_admin_notification(payment.booking, 'payment_received')
                    logger.info(f"Admin payment notification sent for booking {payment.booking.id}")
                except Exception as e:
                    logger.error(f"Failed to send admin payment notification: {str(e)}")
            
        elif event['type'] == 'payment_intent.payment_failed':
            payment_intent = event['data']['object']
            error_message = payment_intent.get('last_payment_error', {}).get('message', 'Payment failed')
            payment_service = init_payment_service()
            payment_service.handle_payment_failure(payment_intent['id'], error_message)
            
        else:
            logger.info(f"Unhandled webhook event type: {event['type']}")
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return jsonify({'error': 'Webhook processing failed'}), 500

@payment_bp.route('/admin/payments')
@login_required
def admin_payments():
    """Admin payment management page"""
    if not current_user.is_admin:
        flash('Admin access required.', 'error')
        return redirect(url_for('main.index'))
    
    payments = Payment.query.order_by(Payment.created_at.desc()).all()
    
    # Get payment analytics
    payment_service = init_payment_service()
    analytics = payment_service.get_payment_analytics()
    
    return render_template('admin/payments.html', 
                         payments=payments,
                         analytics=analytics)

@payment_bp.route('/admin/payment/<int:payment_id>/refund', methods=['POST'])
@login_required
def admin_refund_payment(payment_id):
    """Admin refund payment"""
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        amount = request.form.get('amount', type=float)
        reason = request.form.get('reason', 'requested_by_customer')
        
        payment_service = init_payment_service()
        refund = payment_service.create_refund(
            payment_id=payment_id,
            amount=amount,
            reason=reason
        )
        
        flash(f'Refund of ${amount:.2f} processed successfully.', 'success')
        
    except Exception as e:
        flash(f'Refund failed: {str(e)}', 'error')
    
    return redirect(url_for('payment.admin_payments'))

@payment_bp.route('/admin/payment/<int:payment_id>')
@login_required
def admin_payment_detail(payment_id):
    """Admin payment detail view"""
    if not current_user.is_admin:
        flash('Admin access required.', 'error')
        return redirect(url_for('main.index'))
    
    payment = Payment.query.get_or_404(payment_id)
    
    return render_template('admin/payment_detail.html', payment=payment) 