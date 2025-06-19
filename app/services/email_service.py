from flask import current_app, render_template
from flask_mail import Message
from app import mail
from datetime import datetime
import os

class EmailService:
    """Email service for booking notifications and customer communications"""
    
    @staticmethod
    def _send_email(subject, recipients, template_name, template_data=None, sender=None):
        """Send email using Flask-Mail"""
        try:
            if template_data is None:
                template_data = {}
            
            # Use booking email as default sender
            if sender is None:
                sender = current_app.config.get('MAIL_BOOKING', 'booking@fixbulance.com')
            
            # Add common template data
            template_data.update({
                'business_name': 'Fixbulance',
                'business_phone': current_app.config.get('BUSINESS_PHONE_DISPLAY', '+1 (708) 737-2873'),
                'business_owner': f"{current_app.config.get('BUSINESS_OWNER_FIRST_NAME', 'Ahmed')} {current_app.config.get('BUSINESS_OWNER_LAST_NAME', 'Khalil')}",
                'support_email': current_app.config.get('MAIL_SUPPORT', 'support@fixbulance.com'),
                'current_year': datetime.now().year
            })
            
            # Render email templates
            html_body = render_template(f'emails/{template_name}.html', **template_data)
            text_body = render_template(f'emails/{template_name}.txt', **template_data)
            
            # Create and send message
            msg = Message(
                subject=subject,
                sender=sender,
                recipients=recipients if isinstance(recipients, list) else [recipients],
                html=html_body,
                body=text_body
            )
            
            mail.send(msg)
            current_app.logger.info(f"Email sent successfully: {subject} to {recipients}")
            return True
            
        except Exception as e:
            current_app.logger.error(f"Failed to send email: {str(e)}")
            return False
    
    @classmethod
    def send_booking_confirmation(cls, booking):
        """Send booking confirmation email to customer"""
        subject = f"Booking Confirmation #{booking.id} - Fixbulance Mobile Repair"
        recipient = booking.customer.email if booking.customer else booking.user.email
        
        template_data = {
            'booking': booking,
            'customer_name': booking.customer.first_name if booking.customer else booking.user.first_name,
            'services': booking.booking_services,
            'total_services': len(booking.booking_services),
            'estimated_total': booking.total_estimated_cost,
            'deposit_amount': booking.deposit_amount,
            'scheduled_date': booking.scheduled_date,
            'scheduled_time': booking.scheduled_time,
            'service_address': f"{booking.service_address}, {booking.service_city}, {booking.service_state} {booking.service_zip_code}"
        }
        
        return cls._send_email(subject, recipient, 'booking_confirmation', template_data)
    
    @classmethod
    def send_deposit_receipt(cls, booking, payment):
        """Send deposit payment receipt to customer"""
        subject = f"Payment Receipt - Deposit for Booking #{booking.id}"
        recipient = booking.customer.email if booking.customer else booking.user.email
        
        template_data = {
            'booking': booking,
            'payment': payment,
            'customer_name': booking.customer.first_name if booking.customer else booking.user.first_name,
            'amount_paid': payment.amount,
            'payment_method': payment.payment_method_type or 'Card',
            'transaction_id': payment.stripe_payment_intent_id,
            'services': booking.booking_services,
            'remaining_balance': float(booking.total_estimated_cost) - float(payment.amount),
            'service_date': booking.scheduled_date,
            'service_time': booking.scheduled_time
        }
        
        return cls._send_email(subject, recipient, 'deposit_receipt', template_data)
    
    @classmethod
    def send_admin_confirmation(cls, booking):
        """Send email when admin confirms the booking"""
        subject = f"Booking Confirmed - Ready for Service #{booking.id}"
        recipient = booking.customer.email if booking.customer else booking.user.email
        
        template_data = {
            'booking': booking,
            'customer_name': booking.customer.first_name if booking.customer else booking.user.first_name,
            'services': booking.booking_services,
            'scheduled_date': booking.scheduled_date,
            'scheduled_time': booking.scheduled_time,
            'technician_arrival_window': "within 30 minutes of scheduled time",
            'service_address': f"{booking.service_address}, {booking.service_city}, {booking.service_state} {booking.service_zip_code}",
            'estimated_duration': booking.combined_estimated_duration or 60,
            'final_amount_due': float(booking.total_estimated_cost) - float(booking.deposit_amount)
        }
        
        return cls._send_email(subject, recipient, 'admin_confirmation', template_data)
    
    @classmethod
    def send_service_completed(cls, booking):
        """Send email when service is completed with review request"""
        subject = f"Service Completed - Rate Your Experience #{booking.id}"
        recipient = booking.customer.email if booking.customer else booking.user.email
        
        # Generate review link (you'll need to implement this route)
        review_link = f"{current_app.config.get('BASE_URL', 'http://localhost:8000')}/review/new/{booking.id}"
        
        template_data = {
            'booking': booking,
            'customer_name': booking.customer.first_name if booking.customer else booking.user.first_name,
            'services': booking.booking_services,
            'completed_date': booking.completed_at,
            'work_performed': booking.work_performed,
            'parts_used': booking.parts_used,
            'final_amount': booking.final_amount or booking.total_estimated_cost,
            'review_link': review_link,
            'technician_notes': booking.technician_notes
        }
        
        return cls._send_email(subject, recipient, 'service_completed', template_data)
    
    @classmethod
    def send_reminder_email(cls, booking, reminder_type='appointment'):
        """Send reminder email (24h before appointment, etc.)"""
        if reminder_type == 'appointment':
            subject = f"Appointment Reminder - Tomorrow at {booking.scheduled_time}"
        else:
            subject = f"Service Reminder - Booking #{booking.id}"
            
        recipient = booking.customer.email if booking.customer else booking.user.email
        
        template_data = {
            'booking': booking,
            'customer_name': booking.customer.first_name if booking.customer else booking.user.first_name,
            'services': booking.booking_services,
            'scheduled_date': booking.scheduled_date,
            'scheduled_time': booking.scheduled_time,
            'service_address': f"{booking.service_address}, {booking.service_city}, {booking.service_state} {booking.service_zip_code}",
            'contact_phone': current_app.config.get('BUSINESS_PHONE_DISPLAY'),
            'reminder_type': reminder_type
        }
        
        return cls._send_email(subject, recipient, 'reminder', template_data)
    
    @classmethod
    def send_admin_notification(cls, booking, notification_type='new_booking'):
        """Send notifications to admin about booking events"""
        admin_email = current_app.config.get('MAIL_ADMIN', 'admin@fixbulance.com')
        
        if notification_type == 'new_booking':
            subject = f"New Booking Received #{booking.id}"
        elif notification_type == 'payment_received':
            subject = f"Deposit Payment Received #{booking.id}"
        elif notification_type == 'review_submitted':
            subject = f"New Review Submitted #{booking.id}"
        else:
            subject = f"Booking Update #{booking.id}"
        
        template_data = {
            'booking': booking,
            'customer': booking.customer or booking.user,
            'services': booking.booking_services,
            'notification_type': notification_type,
            'scheduled_date': booking.scheduled_date,
            'scheduled_time': booking.scheduled_time,
            'service_address': f"{booking.service_address}, {booking.service_city}, {booking.service_state} {booking.service_zip_code}",
            'admin_dashboard_link': f"{current_app.config.get('BASE_URL', 'http://localhost:8000')}/admin/booking/{booking.id}"
        }
        
        return cls._send_email(subject, admin_email, 'admin_notification', template_data)
    
    @classmethod
    def send_review_thank_you(cls, review):
        """Send thank you email after customer submits review"""
        subject = "Thank You for Your Review - Fixbulance"
        recipient = review.customer.email
        
        template_data = {
            'review': review,
            'customer_name': review.customer.first_name,
            'rating': review.rating,
            'star_display': review.star_display,
            'booking': review.booking,
            'services': review.booking.booking_services if review.booking else []
        }
        
        return cls._send_email(subject, recipient, 'review_thank_you', template_data)
    
    @classmethod
    def send_promotional_email(cls, recipient, promo_type='seasonal'):
        """Send promotional emails to customers"""
        if promo_type == 'seasonal':
            subject = "Special Offer - Professional Mobile Repair Services"
        else:
            subject = "Exclusive Offer from Fixbulance"
        
        template_data = {
            'promo_type': promo_type,
            'offer_details': "15% off your next repair service",
            'promo_code': "SAVE15",
            'valid_until': "End of month"
        }
        
        return cls._send_email(subject, recipient, 'promotional', template_data) 