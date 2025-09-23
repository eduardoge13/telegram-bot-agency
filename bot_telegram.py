import os
import logging
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List

# Import Flask first - critical for Vercel
from flask import Flask, request, jsonify

# Then import Telegram and other libraries
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import pytz

MEXICO_CITY_TZ = pytz.timezone("America/Mexico_City")

# CRITICAL: Initialize Flask app FIRST for Vercel
app = Flask(__name__)

# Simple logging setup for Vercel (no file logging)
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s | %(name)s | %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Global variables for bot components
application = None
sheets_manager = None
bot_ready = False

class SimpleGoogleSheetsManager:
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
            credentials_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
            spreadsheet_id = os.getenv('SPREADSHEET_ID')
            
            if not credentials_json:
                raise ValueError("GOOGLE_CREDENTIALS_JSON not found")
            if not spreadsheet_id:
                raise ValueError("SPREADSHEET_ID not found")
                
            logger.info("🔑 Loading Google credentials...")
            credentials_data = json.loads(credentials_json)
            self.creds = Credentials.from_service_account_info(
                credentials_data, 
                scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
            )
            
            self.service = build('sheets', 'v4', credentials=self.creds)
            logger.info("✅ Google Sheets connected successfully")
            
        except Exception as e:
            logger.error(f"❌ Google Sheets authentication failed: {e}")
            raise
    
    def _find_client_column(self):
        """Find which column contains client numbers"""
        try:
            spreadsheet_id = os.getenv('SPREADSHEET_ID')
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range='Sheet1!1:1'
            ).execute()
            
            self.headers = result.get('values', [[]])[0]
            
            # Look for client number column
            client_keywords = ['client', 'number', 'id', 'code']
            for i, header in enumerate(self.headers):
                header_lower = header.lower().strip()
                for keyword in client_keywords:
                    if keyword in header_lower:
                        self.client_column = i
                        logger.info(f"📋 Client column found: {header} at position {i}")
                        return
            
            self.client_column = 0  # Default to first column
            logger.info("📋 Using first column as client column")
            
        except Exception as e:
            logger.error(f"❌ Error finding client column: {e}")
            self.client_column = 0
    
    def get_client_data(self, client_number: str) -> Optional[Dict[str, Any]]:
        """Search for client data"""
        try:
            spreadsheet_id = os.getenv('SPREADSHEET_ID')
            logger.info(f"🔍 Searching for client: {client_number}")
            
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range='Sheet1!A:Z'
            ).execute()
            
            values = result.get('values', [])
            if len(values) < 2:
                logger.warning("⚠️ Not enough data in spreadsheet")
                return None
            
            # Search through data rows
            for row_index, row in enumerate(values[1:], start=2):
                if not row or len(row) <= self.client_column:
                    continue
                
                cell_value = str(row[self.client_column]).strip().lower()
                search_value = str(client_number).strip().lower()
                
                if cell_value == search_value:
                    logger.info(f"✅ Client found at row {row_index}")
                    
                    client_data = {}
                    for i, header in enumerate(self.headers):
                        if i < len(row) and row[i].strip():
                            client_data[header] = row[i].strip()
                    
                    return client_data
            
            logger.info(f"❌ Client '{client_number}' not found")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error searching for client: {e}")
            return None

# Bot command handlers
async def start_command(update: Update, context):
    """Handle /start command"""
    user = update.effective_user
    logger.info(f"📱 /start command from {user.first_name}")
    
    welcome_message = (
        f"👋 Hola {user.first_name}! Bienvenido a **Client Data Bot**!\n\n"
        f"🔍 Te puedo ayudar a buscar cualquier cliente :).\n"
        f"💡 **Uso rápido:** Manda un número y te contestaré si lo encuentro!\n\n"
        f"**Comandos disponibles:**\n"
        f"• `/help` - Instrucciones\n"
        f"• `/status` - Estado del bot"
    )
    
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def help_command(update: Update, context):
    """Handle /help command"""
    logger.info(f"📱 /help command from {update.effective_user.first_name}")
    
    help_message = (
        "📖 **Como usar este bot:**\n\n"
        "**Buscar clientes:**\n"
        "• Envía cualquier número de cliente (ej. `12345`)\n"
        "• La búsqueda ignora mayúsculas y espacios\n"
        "• Te mostraré toda la información disponible\n\n"
        "**Comandos:**\n"
        "• `/start` - Mensaje de bienvenida\n"
        "• `/help` - Esta ayuda\n"
        "• `/status` - Verificar si todo funciona\n\n"
        "❓ **¿Necesitas ayuda?** Contacta al administrador."
    )
    
    await update.message.reply_text(help_message, parse_mode='Markdown')

async def status_command(update: Update, context):
    """Check bot status"""
    logger.info(f"📱 /status command from {update.effective_user.first_name}")
    
    try:
        # Test Google Sheets connection
        if sheets_manager and sheets_manager.service:
            sheets_status = "✅ Conectado"
            # Quick test
            test_result = sheets_manager.service.spreadsheets().values().get(
                spreadsheetId=os.getenv('SPREADSHEET_ID'),
                range='Sheet1!A1:A1'
            ).execute()
            client_count = "Disponible"
        else:
            sheets_status = "❌ Error de conexión"
            client_count = "No disponible"
    except Exception as e:
        logger.error(f"Status check error: {e}")
        sheets_status = f"❌ Error: {str(e)[:50]}"
        client_count = "Error"
    
    status_message = (
        "🔧 **Estado del Bot:**\n\n"
        f"🤖 **Bot:** ✅ Ejecutándose\n"
        f"📊 **Google Sheets:** {sheets_status}\n"
        f"📋 **Clientes:** {client_count}\n"
        f"🔍 **Búsqueda:** {'✅ Lista' if sheets_status == '✅ Conectado' else '❌ No disponible'}\n\n"
        f"**Hora México:** {datetime.now(MEXICO_CITY_TZ).strftime('%H:%M:%S')}"
    )
    
    await update.message.reply_text(status_message, parse_mode='Markdown')

async def handle_message(update: Update, context):
    """Handle client number searches"""
    message_text = update.message.text.strip()
    user = update.effective_user
    
    logger.info(f"📨 Message from {user.first_name}: '{message_text}'")
    
    # Validate client number (only digits)
    if not message_text.isdigit():
        await update.message.reply_text(
            "❌ Por favor envía solo números de cliente.\n💡 Ejemplo: `12345`",
            parse_mode='Markdown'
        )
        return
    
    try:
        # Search for client
        logger.info(f"🔍 Searching for client: {message_text}")
        client_data = sheets_manager.get_client_data(message_text)
        
        if client_data:
            logger.info(f"✅ Client found with {len(client_data)} fields")
            
            # Format response
            response = f"✅ **Cliente encontrado: `{message_text}`**\n\n"
            
            field_mappings = {
                'client phone number': 'Número 📞',
                'cliente': 'Cliente 🙋🏻‍♀️',
                'correo': 'Correo ✉️',
                'other info': 'Otra Información ℹ️'
            }
            
            for key, value in client_data.items():
                if value and str(value).strip():
                    key_lower = key.lower().strip()
                    if key_lower in field_mappings:
                        response += f"**{field_mappings[key_lower]}** {value}\n"
                    else:
                        response += f"**{key}:** {value}\n"
            
            # Add user info
            user_display = f"@{user.username}" if user.username else user.first_name
            response += f"**Closer 🙋🏻‍♂️** {user_display}\n"
            response += f"\n📋 *{len(client_data)} campos encontrados*"
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
        else:
            logger.info(f"❌ Client not found: {message_text}")
            
            error_msg = (
                f"❌ **No se encontró cliente:** `{message_text}`\n\n"
                f"**Sugerencias:**\n"
                f"• Verifica el número e intenta de nuevo\n"
                f"• Usa `/status` para verificar la conexión\n"
                f"• Contacta al administrador si el problema persiste"
            )
            await update.message.reply_text(error_msg, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"❌ Search error: {e}")
        await update.message.reply_text(
            f"❌ Error al buscar cliente: `{message_text}`\n\nIntenta de nuevo en un momento.",
            parse_mode='Markdown'
        )

def initialize_bot():
    """Initialize the Telegram bot - called once on startup"""
    global application, sheets_manager, bot_ready
    
    try:
        logger.info("🚀 Initializing bot for Vercel...")
        
        # Check required environment variables
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found")
        
        # Initialize Google Sheets Manager
        logger.info("📊 Initializing Google Sheets...")
        sheets_manager = SimpleGoogleSheetsManager()
        
        # Initialize Telegram Application
        logger.info("🤖 Initializing Telegram application...")
        application = Application.builder().token(bot_token).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("status", status_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        bot_ready = True
        logger.info("✅ Bot initialization completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Bot initialization failed: {e}")
        bot_ready = False
        return False

# Initialize bot on module load
logger.info("🔄 Starting bot initialization...")
init_success = initialize_bot()

if init_success:
    logger.info("🎉 Bot ready for requests!")
else:
    logger.error("💥 Bot initialization failed!")

# Flask routes
@app.route('/')
def health_check():
    """Health check endpoint"""
    status = "✅ Ready" if bot_ready else "❌ Not Ready"
    return {
        "status": "Bot is running",
        "bot_ready": bot_ready,
        "bot_status": status,
        "timestamp": datetime.now(MEXICO_CITY_TZ).isoformat()
    }

@app.route('/api/telegram', methods=['POST'])
def webhook():
    """Telegram webhook endpoint"""
    try:
        if not bot_ready or not application:
            logger.error("❌ Bot not ready for requests")
            return jsonify({"error": "Bot not initialized"}), 500
        
        # Get update data
        update_data = request.get_json(force=True)
        logger.info(f"📥 Received webhook: {update_data.get('message', {}).get('text', 'No text')}")
        
        # Create Update object
        update = Update.de_json(update_data, application.bot)
        
        # Process update in async context
        import asyncio
        try:
            # For Vercel, we need to handle async properly
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(application.process_update(update))
            loop.close()
        except Exception as e:
            logger.error(f"❌ Error in async processing: {e}")
            return jsonify({"error": "Processing failed"}), 500
        
        logger.info("✅ Update processed successfully")
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/debug')
def debug_info():
    """Debug information endpoint"""
    return {
        "bot_ready": bot_ready,
        "application_exists": application is not None,
        "sheets_manager_exists": sheets_manager is not None,
        "environment_vars": {
            "TELEGRAM_BOT_TOKEN": "✅ Set" if os.getenv('TELEGRAM_BOT_TOKEN') else "❌ Missing",
            "SPREADSHEET_ID": "✅ Set" if os.getenv('SPREADSHEET_ID') else "❌ Missing",
            "GOOGLE_CREDENTIALS_JSON": "✅ Set" if os.getenv('GOOGLE_CREDENTIALS_JSON') else "❌ Missing"
        },
        "timestamp": datetime.now(MEXICO_CITY_TZ).isoformat()
    }

# For local testing
if __name__ == '__main__':
    app.run(debug=True, port=5000)