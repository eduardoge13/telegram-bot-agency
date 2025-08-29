import os
import logging
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import json

# Load environment variables
load_dotenv()

# Configure logging with better formatting
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
CREDENTIALS_FILE = 'credentials.json'

class GoogleSheetsManager:
    def __init__(self):
        self.creds = None
        self.service = None
        self.headers = []
        self.client_column = None
        self._authenticate()
        self._find_client_column()
    
    def _authenticate(self):
        """Authenticate with Google Sheets API"""
        try:
            # Try environment variable first (for production)
            credentials_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
            if credentials_json:
                logger.info("Using credentials from environment variable")
                credentials_data = json.loads(credentials_json)
                self.creds = Credentials.from_service_account_info(
                    credentials_data, scopes=SCOPES
                )
            # Fallback to credentials file (for local development)
            elif os.path.exists(CREDENTIALS_FILE):
                logger.info("Using credentials from file")
                self.creds = Credentials.from_service_account_file(
                    CREDENTIALS_FILE, scopes=SCOPES
                )
            else:
                raise FileNotFoundError(
                    "No credentials found! Please either:\n"
                    "1. Set GOOGLE_CREDENTIALS_JSON environment variable, OR\n"
                    "2. Place credentials.json file in the project directory"
                )
            
            self.service = build('sheets', 'v4', credentials=self.creds)
            logger.info("✅ Successfully connected to Google Sheets API")
            
        except json.JSONDecodeError:
            logger.error("❌ Invalid JSON in GOOGLE_CREDENTIALS_JSON")
            raise ValueError("GOOGLE_CREDENTIALS_JSON contains invalid JSON")
        except Exception as e:
            logger.error(f"❌ Authentication failed: {e}")
            raise
    
    def _find_client_column(self):
        """Find which column contains client numbers"""
        try:
            if not SPREADSHEET_ID:
                raise ValueError("❌ SPREADSHEET_ID not found in environment variables")
            
            # Get the first row to find headers
            result = self.service.spreadsheets().values().get(
                spreadsheetId=SPREADSHEET_ID,
                range='Sheet1!1:1'
            ).execute()
            
            self.headers = result.get('values', [[]])[0]
            
            if not self.headers:
                logger.warning("⚠️ No headers found in spreadsheet")
                return
            
            # Look for client number column
            client_keywords = ['client', 'number', 'id', 'code']
            
            for i, header in enumerate(self.headers):
                header_lower = header.lower().strip()
                for keyword in client_keywords:
                    if keyword in header_lower:
                        self.client_column = i
                        logger.info(f"📋 Found client column: '{header}' at position {i}")
                        return
            
            # Default to first column if no match found
            self.client_column = 0
            logger.info("📋 Using first column as client column (no specific match found)")
            
        except Exception as e:
            logger.error(f"❌ Error finding client column: {e}")
            self.client_column = 0
    
    def get_client_data(self, client_number: str) -> Optional[Dict[str, Any]]:
        """Search for client data by client number"""
        try:
            if not SPREADSHEET_ID:
                return None
            
            logger.info(f"🔍 Searching for client: {client_number}")
            
            # Get all data from the sheet
            result = self.service.spreadsheets().values().get(
                spreadsheetId=SPREADSHEET_ID,
                range='Sheet1!A:Z'
            ).execute()
            
            values = result.get('values', [])
            if len(values) < 2:  # Need at least headers + 1 data row
                logger.warning("⚠️ Not enough data in spreadsheet")
                return None
            
            # Skip header row and search through data
            for row_index, row in enumerate(values[1:], start=2):
                if not row or len(row) <= self.client_column:
                    continue
                
                # Check if client number matches (case-insensitive, stripped)
                cell_value = str(row[self.client_column]).strip().lower()
                search_value = str(client_number).strip().lower()
                
                if cell_value == search_value:
                    logger.info(f"✅ Found client at row {row_index}")
                    
                    # Create result dictionary
                    client_data = {}
                    for i, header in enumerate(self.headers):
                        if i < len(row) and row[i].strip():  # Only include non-empty values
                            client_data[header] = row[i].strip()
                    
                    return client_data
            
            logger.info(f"❌ Client '{client_number}' not found")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error searching for client: {e}")
            return None
    
    def get_sheet_info(self) -> Dict[str, Any]:
        """Get basic information about the spreadsheet"""
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=SPREADSHEET_ID,
                range='Sheet1!A:A'
            ).execute()
            
            values = result.get('values', [])
            total_rows = len(values) - 1  # Exclude header row
            
            return {
                'total_clients': max(0, total_rows),
                'headers': self.headers,
                'client_column': self.headers[self.client_column] if self.headers else 'Unknown'
            }
        except Exception as e:
            logger.error(f"Error getting sheet info: {e}")
            return {'total_clients': 0, 'headers': [], 'client_column': 'Unknown'}

class TelegramBot:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.token:
            raise ValueError("❌ TELEGRAM_BOT_TOKEN not found in environment variables")
        
        self.sheets_manager = GoogleSheetsManager()
        self.application = Application.builder().token(self.token).build()
        self._setup_handlers()
        
        # Get sheet info for bot status
        self.sheet_info = self.sheets_manager.get_sheet_info()
        logger.info(f"📊 Sheet loaded: {self.sheet_info['total_clients']} clients available")
    
    def _setup_handlers(self):
        """Setup bot command and message handlers"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("info", self.info_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_name = update.effective_user.first_name or "there"
        
        welcome_message = (
            f"👋 Hi {user_name}! Welcome to the **Client Data Bot**!\n\n"
            f"🔍 I can help you find client information from our database.\n"
            f"📊 Currently tracking **{self.sheet_info['total_clients']} clients**\n\n"
            f"**Available commands:**\n"
            f"• `/help` - Show detailed instructions\n"
            f"• `/info` - Show sheet information\n"
            f"• `/status` - Check bot status\n\n"
            f"💡 **Quick start:** Just send me any client number and I'll find their data!"
        )
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_message = (
            "📖 **How to use this bot:**\n\n"
            "**Finding clients:**\n"
            "• Send any client number (e.g., `12345`, `CLIENT-001`, `ABC123`)\n"
            "• Search is case-insensitive and ignores extra spaces\n"
            "• I'll show all available information for that client\n\n"
            "**Commands:**\n"
            "• `/start` - Welcome message\n"
            "• `/help` - This help message\n"
            "• `/info` - Show spreadsheet details\n"
            "• `/status` - Check if everything is working\n\n"
            "**Tips:**\n"
            "• Make sure the client number matches exactly\n"
            "• Try different formats if first attempt fails\n"
            "• Contact admin if you find issues\n\n"
            "❓ **Need help?** Contact your system administrator."
        )
        await update.message.reply_text(help_message, parse_mode='Markdown')
    
    async def info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show spreadsheet information"""
        info = self.sheet_info
        
        message = (
            "📋 **Spreadsheet Information:**\n\n"
            f"📊 **Total clients:** {info['total_clients']}\n"
            f"🔍 **Search column:** {info['client_column']}\n\n"
            f"**Available fields:**\n"
        )
        
        if info['headers']:
            for i, header in enumerate(info['headers'][:10], 1):  # Show first 10 headers
                message += f"• {header}\n"
            
            if len(info['headers']) > 10:
                message += f"• ... and {len(info['headers']) - 10} more fields\n"
        else:
            message += "• No headers found\n"
        
        message += f"\n💡 Send any client number to search!"
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check bot and system status"""
        try:
            # Test Google Sheets connection
            test_info = self.sheets_manager.get_sheet_info()
            sheets_status = "✅ Connected"
        except:
            sheets_status = "❌ Connection Error"
        
        status_message = (
            "🔧 **Bot Status Check:**\n\n"
            f"🤖 **Bot:** ✅ Running\n"
            f"📊 **Google Sheets:** {sheets_status}\n"
            f"📋 **Clients Available:** {test_info.get('total_clients', 'Unknown')}\n"
            f"🔍 **Search Ready:** {'✅ Yes' if sheets_status == '✅ Connected' else '❌ No'}\n\n"
            f"**Last Updated:** {self.sheet_info.get('last_check', 'On startup')}"
        )
        
        await update.message.reply_text(status_message, parse_mode='Markdown')
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle client number searches"""
        client_number = update.message.text.strip()
        
        if not client_number:
            await update.message.reply_text(
                "❌ Please send me a client number to search for.\n"
                "Example: `12345` or `CLIENT-001`",
                parse_mode='Markdown'
            )
            return
        
        # Show typing indicator while searching
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        try:
            # Search for client
            client_data = self.sheets_manager.get_client_data(client_number)
            
            if client_data:
                # Format successful response
                response = f"✅ **Client Found: `{client_number}`**\n\n"
                
                # Show data in a nice format
                for key, value in client_data.items():
                    if value and str(value).strip():  # Only show non-empty values
                        # Make key bold and value regular
                        response += f"**{key}:** {value}\n"
                
                # Add helpful footer
                response += f"\n📝 *Found {len(client_data)} fields with data*"
                
                await update.message.reply_text(response, parse_mode='Markdown')
                logger.info(f"✅ Successfully sent data for client: {client_number}")
            
            else:
                # Client not found
                suggestion_msg = (
                    f"❌ **No client found with number:** `{client_number}`\n\n"
                    f"**Suggestions:**\n"
                    f"• Check the spelling and try again\n"
                    f"• Try different formats (with/without prefixes)\n"
                    f"• Use `/info` to see available fields\n"
                    f"• Contact admin if the client should exist\n\n"
                    f"💡 *Search is case-insensitive*"
                )
                await update.message.reply_text(suggestion_msg, parse_mode='Markdown')
                logger.info(f"❌ Client not found: {client_number}")
        
        except Exception as e:
            error_msg = (
                f"❌ **Sorry, something went wrong!**\n\n"
                f"I encountered an error while searching for `{client_number}`.\n\n"
                f"**What to try:**\n"
                f"• Wait a moment and try again\n"
                f"• Check `/status` to see if systems are working\n"
                f"• Contact support if the problem persists\n\n"
                f"🔧 *Error logged for technical review*"
            )
            await update.message.reply_text(error_msg, parse_mode='Markdown')
            logger.error(f"❌ Error processing search for '{client_number}': {e}")
    
    def run(self):
        """Start the bot"""
        try:
            logger.info("🚀 Starting Telegram Bot...")
            logger.info(f"📊 Ready to serve {self.sheet_info['total_clients']} clients")
            logger.info("✅ Bot is running in polling mode")
            
            # Start polling
            self.application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True  # Clear old messages on startup
            )
            
        except KeyboardInterrupt:
            logger.info("👋 Bot stopped by user")
        except Exception as e:
            logger.error(f"❌ Bot crashed: {e}")
            raise

def main():
    """Main function"""
    try:
        print("🤖 Telegram Client Data Bot")
        print("=" * 40)
        print("🔧 Initializing...")
        
        bot = TelegramBot()
        
        print("✅ Bot initialized successfully!")
        print(f"📊 {bot.sheet_info['total_clients']} clients loaded")
        print("🚀 Starting bot... (Press Ctrl+C to stop)")
        print("=" * 40)
        
        bot.run()
            
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\n🔧 Please check your .env file and make sure all required variables are set.")
    except Exception as e:
        print(f"\n❌ Failed to start bot: {e}")
        print("\n📖 Check the logs above for more details.")
        print("💡 Make sure your Google Sheets credentials and bot token are correct.")

if __name__ == '__main__':
    main()