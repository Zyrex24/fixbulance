#!/usr/bin/env python3
"""
Email Configuration Test Script
Tests Namecheap email settings for Fixbulance
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_smtp_connection():
    """Test SMTP connection and authentication with Namecheap"""
    
    # Get credentials
    username = os.environ.get('MAIL_USERNAME', 'info@fixbulance.com')
    password = os.environ.get('MAIL_PASSWORD')
    
    print(f"Testing SMTP connection for: {username}")
    print(f"Password provided: {'Yes' if password else 'No'}")
    
    if not password:
        print("❌ ERROR: MAIL_PASSWORD environment variable not set!")
        print("Please run: $env:MAIL_PASSWORD = 'your_actual_password'")
        return False
    
    try:
        # Create SMTP connection
        print("\n📧 Connecting to Namecheap SMTP server...")
        server = smtplib.SMTP('mail.privateemail.com', 587)
        server.set_debuglevel(1)  # Enable debug output
        
        print("\n🔒 Starting TLS...")
        server.starttls()
        
        print(f"\n🔑 Authenticating as {username}...")
        server.login(username, password)
        
        print("\n✅ Authentication successful!")
        
        # Test sending a simple email
        msg = MIMEMultipart()
        msg['From'] = username
        msg['To'] = 'ahmedniazi24a.b@gmail.com'  # Your test email
        msg['Subject'] = 'Fixbulance Email Test - Success!'
        
        body = """
        🎉 SUCCESS! 
        
        Your Fixbulance email configuration is working correctly!
        
        This test email confirms that:
        ✅ SMTP connection established
        ✅ TLS encryption working
        ✅ Authentication successful
        ✅ Email sending operational
        
        Your forgot password system should now work properly.
        
        Best regards,
        Fixbulance Email System
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        print("\n📤 Sending test email...")
        text = msg.as_string()
        server.sendmail(username, 'ahmedniazi24a.b@gmail.com', text)
        
        print("✅ Test email sent successfully!")
        server.quit()
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"\n❌ Authentication failed: {e}")
        print("💡 Check your email password. You might need to:")
        print("   - Verify the password is correct")
        print("   - Check if info@fixbulance.com exists in Namecheap")
        print("   - Enable SMTP access in Namecheap control panel")
        return False
        
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Fixbulance Email Configuration Test")
    print("=" * 50)
    
    success = test_smtp_connection()
    
    if success:
        print("\n🎉 Email system is ready!")
        print("You can now test the forgot password function in your Flask app.")
    else:
        print("\n❌ Email system needs configuration.")
        print("Please fix the issues above and try again.") 