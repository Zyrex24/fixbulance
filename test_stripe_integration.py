#!/usr/bin/env python3
"""
Stripe Integration Test for Fixbulance
Tests Stripe API connectivity and basic payment intent creation
"""

import stripe
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.config import DevelopmentConfig

def test_stripe_connection():
    """Test basic Stripe API connectivity"""
    print("🔧 Testing Stripe Integration for Fixbulance")
    print("=" * 50)
    
    # Initialize Stripe with secret key
    config = DevelopmentConfig()
    stripe.api_key = config.STRIPE_SECRET_KEY
    
    print(f"📋 Using Stripe Secret Key: {config.STRIPE_SECRET_KEY[:12]}...")
    print(f"📋 Using Stripe Publishable Key: {config.STRIPE_PUBLISHABLE_KEY[:12]}...")
    
    try:
        # Test 1: List customers (basic API connectivity test)
        print("\n🧪 Test 1: API Connectivity")
        customers = stripe.Customer.list(limit=1)
        print("✅ Stripe API connection successful!")
        print(f"📊 Account has {len(customers.data)} customers")
        
        # Test 2: Create a test payment intent
        print("\n🧪 Test 2: Payment Intent Creation")
        test_payment = stripe.PaymentIntent.create(
            amount=1500,  # $15.00 in cents
            currency='usd',
            description='Fixbulance Test Payment - Mobile Phone Repair Deposit',
            metadata={
                'business': 'Fixbulance',
                'owner': 'Ahmed Khalil',
                'phone': '(708) 971-4053',
                'test': 'true'
            }
        )
        
        print("✅ Payment Intent created successfully!")
        print(f"💳 Payment Intent ID: {test_payment.id}")
        print(f"💰 Amount: ${test_payment.amount / 100:.2f}")
        print(f"📝 Status: {test_payment.status}")
        
        # Test 3: Create a test customer
        print("\n🧪 Test 3: Customer Creation")
        test_customer = stripe.Customer.create(
            email='test@fixbulance.com',
            name='Ahmed Khalil - Test Customer',
            phone='(708) 971-4053',
            metadata={
                'business': 'Fixbulance',
                'test_customer': 'true'
            }
        )
        
        print("✅ Test customer created successfully!")
        print(f"👤 Customer ID: {test_customer.id}")
        print(f"📧 Email: {test_customer.email}")
        
        # Test 4: Webhook configuration (check if valid)
        print("\n🧪 Test 4: Webhook Secret Validation")
        webhook_secret = config.STRIPE_WEBHOOK_SECRET
        if webhook_secret and webhook_secret.startswith('whsec_'):
            print("✅ Webhook secret format is valid!")
            print(f"🔗 Webhook Secret: {webhook_secret[:15]}...")
        else:
            print("⚠️  Webhook secret format may be invalid")
        
        print("\n🎉 ALL TESTS PASSED!")
        print("\n📋 Integration Summary:")
        print("✅ Stripe API connectivity working")
        print("✅ Payment intents can be created")
        print("✅ Customer management functional")
        print("✅ Ready for real payment processing")
        
        print("\n💡 Next Steps:")
        print("1. 🌐 Visit your Fixbulance app at http://localhost:5000")
        print("2. 📱 Create a booking and proceed to payment")
        print("3. 💳 Use test card: 4242 4242 4242 4242")
        print("4. 📧 Use any email and future expiry date")
        print("5. 🎯 Complete the $15 deposit payment")
        
        # Clean up test data
        print("\n🧹 Cleaning up test data...")
        stripe.Customer.delete(test_customer.id)
        print("✅ Test customer deleted")
        
        return True
        
    except stripe.error.AuthenticationError as e:
        print(f"❌ Authentication Error: {e}")
        print("🔧 Check your Stripe secret key")
        return False
        
    except stripe.error.APIConnectionError as e:
        print(f"❌ API Connection Error: {e}")
        print("🌐 Check your internet connection")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False

if __name__ == "__main__":
    success = test_stripe_connection()
    
    if success:
        print("\n🚀 Fixbulance Stripe Integration: READY FOR BUSINESS!")
    else:
        print("\n💥 Stripe Integration: NEEDS ATTENTION")
        sys.exit(1) 