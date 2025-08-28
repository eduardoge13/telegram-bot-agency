import os
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import json
from flask import Flask, request
import threading
import asyncio

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Google Sheets API configuration
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
CREDENTIALS_FILE = 'credentials.json'

# Flask app for webhook
app = Flask(__name__)

class GoogleSheetsManager:
    def __init__(self):
        self.creds = None
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Sheets API using service account"""
        try:
            if not os.path.exists(CREDENTIALS_FILE):
                # Try to get credentials from environment variable
                credentials_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
                if credentials_json:
                    # Parse the JSON string from environment variable
                    credentials_data = json.loads(credentials_json)
                    self.creds = Credentials.from_service_account_info(
                        credentials_data, scopes=SCOPES
                    )
                else:
                    raise FileNotFoundError(
                        f"Please either:\n"
                        f"1. Place your credentials.json file in the project directory, OR\n"
                        f"2. Set the GOOGLE_CREDENTIALS_JSON environment variable with your service account JSON content"
                    )
            else:
                # Use the credentials.json file
                self.creds = Credentials.from_service_account_file(
                    CREDENTIALS_FILE, scopes=SCOPES
                )
            
            self.service = build('sheets', 'v4', credentials=self.creds)
            logger.info("Successfully authenticated with Google Sheets API")
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise
    
    def get_client_data(self, client_number: str) -> Optional[Dict[str, Any]]:
        """Extract client data from Google Sheets based on client number"""
        try:
            if not SPREADSHEET_ID:
                raise ValueError("SPREADSHEET_ID not found in environment variables")
            
            # Assuming the first sheet contains client data
            # You may need to adjust the range based on your sheet structure
            range_name = 'Sheet1!A:Z'  # Adjust this range as needed
            
            result = self.service.spreadsheets().values().get(
                spreadsheetId=SPREADSHEET_ID,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            if not values:
                return None
            
            # Assuming first row contains headers
            headers = values[0]
            client_number_col = None
            
            # Find the column index for client number
            for i, header in enumerate(headers):
                if 'client' in header.lower() and 'number' in header.lower():
                    client_number_col = i
                    break
            
            if client_number_col is None:
                # If no specific client number column found, assume first column
                client_number_col = 0
            
            # Search for the client number
            for row in values[1:]:  # Skip header row
                if len(row) > client_number_col and str(row[client_number_col]).strip() == str(client_number).strip():
                    # Create a dictionary with headers and values
                    client_data = {}
                    for i, header in enumerate(headers):
                        if i < len(row):
                            client_data[header] = row[i]
                        else:
                            client_data[header] = ""
                    return client_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting client data: {e}")
            return None

class TelegramBot:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
        
        self.sheets_manager = GoogleSheetsManager()
        self.application = Application.builder().token(self.token).build()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup bot command and message handlers"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_message = (
            "🤖 Welcome to the Client Data Bot!\n\n"
            "I can help you extract client information from Google Sheets.\n\n"
            "📋 Available commands:\n"
            "/start - Show this welcome message\n"
            "/help - Show help information\n\n"
            "💡 Simply send me a client number and I'll fetch the data for you!"
        )
        await update.message.reply_text(welcome_message)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_message = (
            "🔍 How to use this bot:\n\n"
            "1. Send me a client number (e.g., '12345' or 'CLIENT-001')\n"
            "2. I'll search the Google Sheet for matching data\n"
            "3. If found, I'll display all the client information\n\n"
            "📝 Note: Make sure the client number matches exactly what's in the sheet\n\n"
            "❓ Need help? Contact your administrator."
        )
        await update.message.reply_text(help_message)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages (client numbers)"""
        client_number = update.message.text.strip()
        
        if not client_number:
            await update.message.reply_text("Please send me a client number to search for.")
            return
        
        # Show typing indicator
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        try:
            # Search for client data
            client_data = self.sheets_manager.get_client_data(client_number)
            
            if client_data:
                # Format the response
                response = f"✅ **Client Found!**\n\n"
                for key, value in client_data.items():
                    if value:  # Only show non-empty values
                        response += f"**{key}:** {value}\n"
                
                await update.message.reply_text(response, parse_mode='Markdown')
            else:
                await update.message.reply_text(
                    f"❌ No client found with number: `{client_number}`\n\n"
                    "Please check the number and try again.",
                    parse_mode='Markdown'
                )
        
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await update.message.reply_text(
                "❌ Sorry, I encountered an error while processing your request. "
                "Please try again later or contact support."
            )
    
    async def setup_webhook(self, webhook_url: str):
        """Setup webhook for the bot"""
        try:
            await self.application.bot.set_webhook(url=webhook_url)
            logger.info(f"Webhook set to: {webhook_url}")
        except Exception as e:
            logger.error(f"Failed to set webhook: {e}")
    
    def run_polling(self):
        """Start the bot in polling mode (for local development)"""
        logger.info("Starting Telegram bot in polling mode...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)
    
    def run_webhook(self, webhook_url: str, port: int = 8000):
        """Start the bot in webhook mode (for production)"""
        logger.info("Starting Telegram bot in webhook mode...")
        
        # Start Flask app in a separate thread
        def run_flask():
            app.run(host='0.0.0.0', port=port)
        
        flask_thread = threading.Thread(target=run_flask)
        flask_thread.daemon = True
        flask_thread.start()
        
        # Start webhook
        self.application.run_webhook(
            listen='0.0.0.0',
            port=port,
            webhook_url=webhook_url,
            secret_token=os.getenv('WEBHOOK_SECRET_TOKEN', 'your-secret-token')
        )

# Webhook endpoint
@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming webhook from Telegram"""
    try:
        update = Update.de_json(request.get_json(), bot.application.bot)
        bot.application.process_update(update)
        return 'OK'
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return 'Error', 500

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Railway"""
    return 'OK', 200

def main():
    """Main function to run the bot"""
    try:
        global bot
        bot = TelegramBot()
        
        # Use polling mode for both development and production (simpler and more reliable)
        logger.info("Starting Telegram bot in polling mode...")
        bot.run_polling()
            
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        print(f"Error: {e}")
        print("\nPlease check your environment variables and credentials.")

if __name__ == '__main__':
    main()
