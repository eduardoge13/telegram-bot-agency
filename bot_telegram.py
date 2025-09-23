import os
import logging
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# Import Flask first
from flask import Flask, request

# Import Telegram and other libraries
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import pytz
import asyncio

# --- Basic Setup ---
MEXICO_CITY_TZ = pytz.timezone("America/Mexico_City")
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s | %(name)s | %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# --- Global Variables for Lazy Initialization ---
application: Optional[Application] = None
sheets_manager: Optional[Any] = None

# --- Core Logic Classes (Simplified for clarity) ---
class SimpleGoogleSheetsManager:
    """Handles all Google Sheets API calls."""
    def __init__(self):
        self.service = None
        self.headers = []
        self.client_column = 0
        self._authenticate()
        if self.service:
            self._find_client_column()

    def _authenticate(self):
        try:
            credentials_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
            if not credentials_json:
                raise ValueError("Env var GOOGLE_CREDENTIALS_JSON is not set.")
            
            credentials_data = json.loads(credentials_json)
            creds = Credentials.from_service_account_info(
                credentials_data, scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
            )
            self.service = build('sheets', 'v4', credentials=creds)
            logger.info("✅ Google Sheets connected successfully.")
        except Exception as e:
            logger.error(f"❌ Google Sheets authentication failed: {e}")
            self.service = None

    def _find_client_column(self):
        try:
            spreadsheet_id = os.getenv('SPREADSHEET_ID')
            if not spreadsheet_id:
                raise ValueError("Env var SPREADSHEET_ID is not set.")
                
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id, range='Sheet1!1:1'
            ).execute()
            
            self.headers = result.get('values', [[]])[0]
            client_keywords = ['client', 'number', 'id', 'code']
            for i, header in enumerate(self.headers):
                if any(keyword in header.lower().strip() for keyword in client_keywords):
                    self.client_column = i
                    logger.info(f"📋 Client column found: '{header}' at position {i}")
                    return
            logger.info("📋 Using first column as client column by default.")
        except Exception as e:
            logger.error(f"❌ Error finding client column: {e}")

    def get_client_data(self, client_number: str) -> Optional[Dict[str, str]]:
        if not self.service: return None
        try:
            spreadsheet_id = os.getenv('SPREADSHEET_ID')
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id, range='Sheet1!A:Z'
            ).execute()
            
            values = result.get('values', [])
            if len(values) < 2: return None

            for row in values[1:]:
                if len(row) > self.client_column and str(row[self.client_column]).strip().lower() == str(client_number).strip().lower():
                    logger.info(f"✅ Client '{client_number}' found.")
                    return {header: row[i].strip() for i, header in enumerate(self.headers) if i < len(row) and row[i].strip()}
            
            logger.warning(f"❌ Client '{client_number}' not found.")
            return None
        except Exception as e:
            logger.error(f"❌ Error searching for client: {e}")
            return None

# --- Telegram Command Handlers ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_message = f"👋 Hola {user.first_name}! Envía un número de cliente para buscar sus datos."
    await update.message.reply_text(welcome_message)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text.strip()
    user = update.effective_user
    logger.info(f"📨 Message from {user.first_name}: '{message_text}'")

    if not message_text.isdigit():
        await update.message.reply_text("❌ Por favor, envía solo el número de cliente.")
        return

    client_data = sheets_manager.get_client_data(message_text)

    if client_data:
        response = f"✅ **Cliente encontrado: `{message_text}`**\n\n"
        for key, value in client_data.items():
            response += f"**{key.strip()}:** {value}\n"
        await update.message.reply_text(response, parse_mode='Markdown')
    else:
        await update.message.reply_text(f"❌ No se encontró ningún cliente con el número `{message_text}`.", parse_mode='Markdown')

# --- Initialization Function ---
async def initialize():
    """Initializes the bot on the first request."""
    global application, sheets_manager
    
    sheets_manager = SimpleGoogleSheetsManager()
    if not sheets_manager.service:
        raise RuntimeError("Failed to initialize Google Sheets Manager.")

    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN not found.")
        
    application = Application.builder().token(bot_token).build()
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # This is the critical step that was failing before
    await application.initialize()
    logger.info("🎉 Bot initialized successfully!")

# --- Flask App and Webhook ---
app = Flask(__name__)

@app.route('/api/telegram', methods=['POST'])
async def webhook():
    """This function is called by Vercel for every Telegram message."""
    global application
    
    # This block runs ONLY ONCE on the very first message
    if not application:
        try:
            await initialize()
        except Exception as e:
            logger.error(f"💥 CRITICAL: Bot initialization failed: {e}")
            return "Bot initialization failed", 500

    # This block runs for EVERY message
    try:
        update = Update.de_json(request.get_json(force=True), application.bot)
        await application.process_update(update)
        return "ok", 200
    except Exception as e:
        logger.error(f"❌ Error processing webhook: {e}")
        return "Error", 500

@app.route('/')
def index():
    """A simple health check page."""
    status = "✅ Bot is initialized and ready." if application else "⏳ Bot is not yet initialized. Send a message to the bot to trigger initialization."
    return f"<h1>Bot Status</h1><p>{status}</p>"