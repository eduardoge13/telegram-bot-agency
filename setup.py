#!/usr/bin/env python3
"""
Setup script for Telegram Bot with Google Sheets integration
"""

import os
import subprocess
import sys

def install_requirements():
    """Install required packages"""
    print("📦 Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully!")
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies. Please install manually:")
        print("   pip install -r requirements.txt")
        return False
    return True

def create_env_file():
    """Create .env file from template"""
    if os.path.exists('.env'):
        print("⚠️  .env file already exists, skipping...")
        return True
    
    print("🔧 Creating .env file...")
    try:
        with open('.env', 'w') as f:
            f.write("# Telegram Bot Configuration\n")
            f.write("TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here\n\n")
            f.write("# Google Sheets Configuration\n")
            f.write("SPREADSHEET_ID=your_google_spreadsheet_id_here\n")
        print("✅ .env file created! Please edit it with your actual values.")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def check_files():
    """Check if required files exist"""
    print("🔍 Checking required files...")
    
    missing_files = []
    
    if not os.path.exists('bot_telegram.py'):
        missing_files.append('bot_telegram.py')
    
    if not os.path.exists('requirements.txt'):
        missing_files.append('requirements.txt')
    
    if missing_files:
        print(f"❌ Missing required files: {', '.join(missing_files)}")
        return False
    
    print("✅ All required files found!")
    return True

def main():
    """Main setup function"""
    print("🚀 Setting up Telegram Bot with Google Sheets integration...\n")
    
    # Check files
    if not check_files():
        print("\n❌ Setup failed. Please ensure all files are present.")
        return
    
    # Install requirements
    if not install_requirements():
        print("\n❌ Setup failed. Please install dependencies manually.")
        return
    
    # Create env file
    if not create_env_file():
        print("\n❌ Setup failed. Please create .env file manually.")
        return
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit .env file with your actual values")
    print("2. Download credentials.json from Google Cloud Console")
    print("3. Place credentials.json in this directory")
    print("4. Run: python bot_telegram.py")
    print("\n📖 See README.md for detailed instructions")

if __name__ == "__main__":
    main()

