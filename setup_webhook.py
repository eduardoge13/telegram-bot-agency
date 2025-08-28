#!/usr/bin/env python3
"""
Script to manually set up Telegram webhook for the bot
Run this after deploying to Railway to ensure the webhook is properly configured
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_webhook():
    """Set up the Telegram webhook"""
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    webhook_url = os.getenv('WEBHOOK_URL')
    
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not found in environment variables")
        return False
    
    if not webhook_url:
        print("❌ WEBHOOK_URL not found in environment variables")
        print("Please set WEBHOOK_URL to your Railway domain + /webhook")
        return False
    
    # Set webhook
    telegram_api_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
    data = {
        'url': webhook_url,
        'allowed_updates': ['message', 'callback_query']
    }
    
    try:
        response = requests.post(telegram_api_url, json=data)
        result = response.json()
        
        if result.get('ok'):
            print(f"✅ Webhook set successfully!")
            print(f"📡 Webhook URL: {webhook_url}")
            
            # Get webhook info
            info_response = requests.get(f"https://api.telegram.org/bot{bot_token}/getWebhookInfo")
            info = info_response.json()
            
            if info.get('ok'):
                webhook_info = info['result']
                print(f"📊 Webhook Info:")
                print(f"   URL: {webhook_info.get('url', 'Not set')}")
                print(f"   Has custom certificate: {webhook_info.get('has_custom_certificate', False)}")
                print(f"   Pending update count: {webhook_info.get('pending_update_count', 0)}")
                print(f"   Last error date: {webhook_info.get('last_error_date', 'None')}")
                print(f"   Last error message: {webhook_info.get('last_error_message', 'None')}")
            
            return True
        else:
            print(f"❌ Failed to set webhook: {result.get('description', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error setting webhook: {e}")
        return False

def test_webhook():
    """Test if the webhook is working"""
    webhook_url = os.getenv('WEBHOOK_URL')
    
    if not webhook_url:
        print("❌ WEBHOOK_URL not found")
        return False
    
    try:
        # Test the health endpoint
        health_url = webhook_url.replace('/webhook', '/health')
        response = requests.get(health_url)
        
        if response.status_code == 200:
            print(f"✅ Health check passed: {health_url}")
            return True
        else:
            print(f"❌ Health check failed: {health_url} - Status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing webhook: {e}")
        return False

if __name__ == '__main__':
    print("🔧 Setting up Telegram webhook...")
    print("=" * 50)
    
    # Test webhook endpoint first
    print("\n1. Testing webhook endpoint...")
    if test_webhook():
        print("✅ Webhook endpoint is accessible")
    else:
        print("❌ Webhook endpoint is not accessible")
        print("   Make sure your Railway service is running and accessible")
        exit(1)
    
    # Set up webhook
    print("\n2. Setting up Telegram webhook...")
    if setup_webhook():
        print("\n🎉 Webhook setup completed successfully!")
        print("\n📱 Your bot should now respond to messages!")
        print("   Try sending /start to your bot on Telegram")
    else:
        print("\n❌ Webhook setup failed!")
        print("   Check your environment variables and try again")
