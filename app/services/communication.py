"""
Communication service for email and SMS messaging
Handles customer notifications for booking updates and emergency communications
"""

import logging
from flask import current_app
from datetime import datetime
import re

class CommunicationService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def send_email(self, to_email, subject, html_content, text_content=None, from_email=None):
        """Send email using SendGrid"""
        try:
            # Use appropriate sender email based on context
            if not from_email:
                from_email = current_app.config.get('MAIL_DEFAULT_SENDER', 'info@fixbulance.com')
            
            # For now, simulate email sending
            # In production, would integrate with SendGrid API
            
            self.logger.info(f"Email sent from {from_email} to {to_email}: {subject}")
            
            return {
                'success': True,
                'message': 'Email sent successfully',
                'message_id': f"email_{datetime.utcnow().timestamp()}",
                'delivery_status': 'sent',
                'from_email': from_email
            }
            
        except Exception as e:
            self.logger.error(f"Email sending error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'delivery_status': 'failed'
            }
    
    def send_sms(self, to_phone, message):
        """Send SMS using Twilio"""
        try:
            # Clean phone number
            cleaned_phone = self.clean_phone_number(to_phone)
            
            if not cleaned_phone:
                raise ValueError("Invalid phone number format")
            
            # For now, simulate SMS sending
            # In production, would integrate with Twilio API
            
            self.logger.info(f"SMS sent to {cleaned_phone}: {message[:50]}...")
            
            return {
                'success': True,
                'message': 'SMS sent successfully',
                'message_id': f"sms_{datetime.utcnow().timestamp()}",
                'delivery_status': 'sent',
                'phone_number': cleaned_phone
            }
            
        except Exception as e:
            self.logger.error(f"SMS sending error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'delivery_status': 'failed'
            }
    
    def clean_phone_number(self, phone):
        """Clean and validate phone number"""
        if not phone:
            return None
        
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)
        
        # Handle US phone numbers
        if len(digits) == 10:
            return f"+1{digits}"
        elif len(digits) == 11 and digits.startswith('1'):
            return f"+{digits}"
        else:
            return None
    
    def send_booking_confirmation(self, booking):
        """Send booking confirmation via email and SMS"""
        try:
            results = {}
            
            # Email confirmation
            if booking.customer_email:
                email_subject = f"Booking Confirmed - Fixbulance #{booking.booking_reference}"
                email_html = self.get_confirmation_email_html(booking)
                email_text = self.get_confirmation_email_text(booking)
                
                email_result = self.send_email(
                    booking.customer_email,
                    email_subject,
                    email_html,
                    email_text,
                    from_email=current_app.config.get('MAIL_APPOINTMENTS', 'appointments@fixbulance.com')
                )
                results['email'] = email_result
            
            # SMS confirmation
            if booking.customer_phone:
                sms_message = self.get_confirmation_sms_text(booking)
                
                sms_result = self.send_sms(
                    booking.customer_phone,
                    sms_message
                )
                results['sms'] = sms_result
            
            return {
                'success': True,
                'results': results,
                'booking_id': booking.id
            }
            
        except Exception as e:
            self.logger.error(f"Booking confirmation error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_technician_enroute(self, booking, technician_name, eta_minutes):
        """Send technician en route notification"""
        try:
            results = {}
            
            # SMS notification (preferred for urgent updates)
            if booking.customer_phone:
                sms_message = f"Your Fixbulance technician {technician_name} is en route! ETA: {eta_minutes} min. Booking #{booking.booking_reference}"
                
                sms_result = self.send_sms(
                    booking.customer_phone,
                    sms_message
                )
                results['sms'] = sms_result
            
            # Email notification
            if booking.customer_email:
                email_subject = f"Technician En Route - Fixbulance #{booking.booking_reference}"
                email_html = self.get_enroute_email_html(booking, technician_name, eta_minutes)
                
                email_result = self.send_email(
                    booking.customer_email,
                    email_subject,
                    email_html,
                    from_email=current_app.config.get('MAIL_SUPPORT', 'support@fixbulance.com')
                )
                results['email'] = email_result
            
            return {
                'success': True,
                'results': results,
                'booking_id': booking.id
            }
            
        except Exception as e:
            self.logger.error(f"En route notification error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_completion_notification(self, booking, total_cost):
        """Send repair completion notification"""
        try:
            results = {}
            
            # Email with detailed completion info
            if booking.customer_email:
                email_subject = f"Repair Completed - Fixbulance #{booking.booking_reference}"
                email_html = self.get_completion_email_html(booking, total_cost)
                
                email_result = self.send_email(
                    booking.customer_email,
                    email_subject,
                    email_html,
                    from_email=current_app.config.get('MAIL_SUPPORT', 'support@fixbulance.com')
                )
                results['email'] = email_result
            
            # SMS notification
            if booking.customer_phone:
                sms_message = f"Repair complete! Your {booking.device_type} is ready. Total: ${total_cost}. Thank you for choosing Fixbulance!"
                
                sms_result = self.send_sms(
                    booking.customer_phone,
                    sms_message
                )
                results['sms'] = sms_result
            
            return {
                'success': True,
                'results': results,
                'booking_id': booking.id
            }
            
        except Exception as e:
            self.logger.error(f"Completion notification error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_confirmation_email_html(self, booking):
        """Generate HTML email content for booking confirmation"""
        return f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #1e3a5f; color: white; padding: 20px; text-align: center;">
                <h1>Booking Confirmed!</h1>
                <p>Your emergency repair appointment is scheduled</p>
            </div>
            
            <div style="padding: 20px;">
                <h2>Booking Details</h2>
                <p><strong>Booking Reference:</strong> {booking.booking_reference}</p>
                <p><strong>Device:</strong> {booking.device_type} {booking.device_model}</p>
                <p><strong>Service:</strong> {booking.service.name if booking.service else 'Device Repair'}</p>
                <p><strong>Date:</strong> {booking.preferred_date}</p>
                <p><strong>Time:</strong> {booking.preferred_time}</p>
                <p><strong>Location:</strong> {booking.customer_address}, {booking.city}, {booking.state} {booking.zip_code}</p>
                
                <h3>Service Cost</h3>
                <p><strong>Service Price:</strong> ${booking.service_price}</p>
                <p><strong>Deposit Paid:</strong> ${booking.deposit_amount}</p>
                <p><strong>Remaining Balance:</strong> ${float(booking.service_price) - float(booking.deposit_amount)}</p>
                
                <div style="background: #f8f9fa; padding: 15px; margin: 20px 0; border-left: 4px solid #1e3a5f;">
                    <h4>What's Next?</h4>
                    <p>Our technician will arrive 15 minutes before your scheduled time and will call you upon arrival.</p>
                    <p>For any changes or questions, call us at <strong>+1 (708) 737-2873</strong></p>
                </div>
            </div>
            
            <div style="background: #f8f9fa; padding: 20px; text-align: center;">
                <p>Thank you for choosing Fixbulance!</p>
                <p>Your phone's emergency service</p>
            </div>
        </div>
        """
    
    def get_confirmation_email_text(self, booking):
        """Generate plain text email content for booking confirmation"""
        return f"""
        BOOKING CONFIRMED - FIXBULANCE
        
        Your emergency repair appointment is scheduled!
        
        Booking Reference: {booking.booking_reference}
        Device: {booking.device_type} {booking.device_model}
        Service: {booking.service.name if booking.service else 'Device Repair'}
        Date: {booking.preferred_date}
        Time: {booking.preferred_time}
        Location: {booking.customer_address}, {booking.city}, {booking.state} {booking.zip_code}
        
        Service Cost: ${booking.service_price}
        Deposit Paid: ${booking.deposit_amount}
        Remaining Balance: ${float(booking.service_price) - float(booking.deposit_amount)}
        
        Our technician will arrive 15 minutes before your scheduled time and will call you upon arrival.
        
        For any changes or questions, call us at +1 (708) 737-2873
        
        Thank you for choosing Fixbulance!
        """
    
    def get_confirmation_sms_text(self, booking):
        """Generate SMS text for booking confirmation"""
        return f"Fixbulance booking confirmed! {booking.device_type} repair on {booking.preferred_date} at {booking.preferred_time}. Ref: {booking.booking_reference}. Questions? Call +1 (708) 737-2873"
    
    def get_enroute_email_html(self, booking, technician_name, eta_minutes):
        """Generate HTML email for en route notification"""
        return f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #dc2626; color: white; padding: 20px; text-align: center;">
                <h1>🚐 Technician En Route!</h1>
                <p>Your Fixbulance repair van is on the way</p>
            </div>
            
            <div style="padding: 20px;">
                <h2>Arrival Information</h2>
                <p><strong>Technician:</strong> {technician_name}</p>
                <p><strong>Estimated Arrival:</strong> {eta_minutes} minutes</p>
                <p><strong>Booking:</strong> {booking.booking_reference}</p>
                
                <div style="background: #fef2f2; padding: 15px; margin: 20px 0; border-left: 4px solid #dc2626;">
                    <h4>Please Prepare</h4>
                    <p>• Have your {booking.device_type} ready for inspection</p>
                    <p>• Ensure the repair location is accessible</p>
                    <p>• Your technician will call upon arrival</p>
                </div>
                
                <p>For real-time updates, call <strong>+1 (708) 737-2873</strong></p>
            </div>
        </div>
        """
    
    def get_completion_email_html(self, booking, total_cost):
        """Generate HTML email for completion notification"""
        return f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #10b981; color: white; padding: 20px; text-align: center;">
                <h1>✅ Repair Completed!</h1>
                <p>Your device has been successfully repaired</p>
            </div>
            
            <div style="padding: 20px;">
                <h2>Service Summary</h2>
                <p><strong>Device:</strong> {booking.device_type} {booking.device_model}</p>
                <p><strong>Service:</strong> {booking.service.name if booking.service else 'Device Repair'}</p>
                <p><strong>Completed:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                <p><strong>Total Cost:</strong> ${total_cost}</p>
                
                <div style="background: #f0fdf4; padding: 15px; margin: 20px 0; border-left: 4px solid #10b981;">
                    <h4>Warranty Information</h4>
                    <p>Your repair comes with a 30-day warranty. If you experience any issues, contact us immediately.</p>
                </div>
                
                <p>Thank you for choosing Fixbulance for your emergency repair needs!</p>
            </div>
        </div>
        """

# Global communication service instance
communication_service = CommunicationService() 