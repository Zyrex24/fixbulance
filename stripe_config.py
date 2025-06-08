#!/usr/bin/env python3
"""
Stripe Configuration Setup for Fixbulance
Sets up environment variables for Stripe payment processing
"""

import os

def setup_stripe_environment():
    """Set up Stripe environment variables"""
    
    # Stripe keys should be loaded from environment variables or .env file
    # Never hardcode API keys in source code!
    stripe_config = {
        'STRIPE_PUBLISHABLE_KEY': os.environ.get('STRIPE_PUBLISHABLE_KEY', ''),
        'STRIPE_SECRET_KEY': os.environ.get('STRIPE_SECRET_KEY', ''),
        'STRIPE_WEBHOOK_SECRET': os.environ.get('STRIPE_WEBHOOK_SECRET', '')
    }
    
    print("🔧 Setting up Stripe environment variables...")
    
    # Set environment variables
    for key, value in stripe_config.items():
        os.environ[key] = value
        print(f"✅ Set {key}")
    
    print("🎉 Stripe environment configured successfully!")
    
    return stripe_config

if __name__ == "__main__":
    print("🚀 Fixbulance Stripe Configuration Setup")
    print("=" * 50)
    setup_stripe_environment()
    
    print("\n💡 Environment variables are now set for this session.")
    print("📝 For permanent setup, add these to your system environment variables:")
    print("   - Windows: System Properties > Environment Variables")
    print("   - Or create a .env file in your project root")
    
    print("\n🧪 You can now test Stripe payment processing!")
    print("🏃‍♂️ Run: python app.py or flask run") 