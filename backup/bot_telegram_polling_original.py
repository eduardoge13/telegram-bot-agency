#!/usr/bin/env python3
"""
Telegram Bot for Client Data Management - Cloud Run Version
"""

import os
import logging
import asyncio
import sys
import json
import time
import pytz
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, date

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Telegram imports
from telegram import Update, Chat
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import telegram

# Google Sheets imports
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Configuration
MEXICO_CITY_TZ = pytz.timezone("America/Mexico_City")
logger = logging.getLogger(__name__)

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s | %(name)s | %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    # Log key runtime versions for diagnostics
    logging.getLogger(__name__).info(
        "Runtime versions -> python-telegram-bot=%s, python=%s",
        getattr(telegram, "__version__", "unknown"),
        sys.version.split()[0]
    )

setup_logging()

def get_secret(project_id: str, secret_id: str, version_id: str = "latest") -> Optional[str]:
    """
    Retrieves a secret from Google Cloud Secret Manager.
    """
    try:
        from google.cloud import secretmanager
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.error(f"❌ Failed to retrieve secret '{secret_id}': {e}")
        return None

class PersistentLogger:
    """Store all logs permanently in Google Sheets"""
    
    def __init__(self):
        self.logs_sheet_id = os.getenv('LOGS_SPREADSHEET_ID')
        self.service = None
        self._setup_sheets_service()
    
    def _setup_sheets_service(self):
        """Setup Google Sheets service for logging"""
        try:
            # GCP Project ID from environment
            project_id = os.getenv('GCP_PROJECT_ID')
            if not project_id:
                logger.warning("⚠️ GCP_PROJECT_ID not set. Cannot fetch secrets from Secret Manager.")
                return

            # Fetch credentials from Secret Manager
            credentials_json = get_secret(project_id, 'google-credentials-json')
            if credentials_json:
                logger.info("Using persistent logging credentials from Secret Manager")
                credentials_data = json.loads(credentials_json)
                creds = Credentials.from_service_account_info(
                    credentials_data, 
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
            else:
                logger.warning("⚠️ Could not fetch 'google-credentials-json' from Secret Manager.")
                self.service = None
                return
            
            # Disable discovery cache to avoid noisy logs in server environments
            self.service = build('sheets', 'v4', credentials=creds, cache_discovery=False)
            logger.info("✅ Persistent logger connected to Google Sheets")
            
        except json.JSONDecodeError:
            logger.warning("⚠️ Invalid JSON in 'google-credentials-json' secret")
            self.service = None
        except Exception as e:
            logger.warning(f"⚠️ Could not setup persistent logging: {e}")
            self.service = None
    
    def log_to_sheets(self, timestamp: str, level: str, user_id: str, username: str, 
                     action: str, details: str, chat_type: str = "", 
                     client_number: str = "", success: str = ""):
        """Save log entry permanently to Google Sheets"""
        if not self.service or not self.logs_sheet_id:
            return False
        
        try:
            # Prepare data row
            row_data = [
                timestamp,
                level,
                user_id,
                username,
                action,
                details,
                chat_type,
                client_number,
                success
            ]
            
            # Insert into sheet
            self.service.spreadsheets().values().append(
                spreadsheetId=self.logs_sheet_id,
                range='Sheet1!A:I',
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body={'values': [row_data]}
            ).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving to persistent log: {e}")
            return False

class EnhancedUserActivityLogger:
    """Enhanced logger with persistent storage"""
    
    @staticmethod
    def log_user_action(update: Update, action: str, details: str = "", client_number: str = "", success: str = ""):
        """Log user actions with local AND persistent storage"""
        user = update.effective_user
        chat = update.effective_chat
        timestamp = datetime.now(MEXICO_CITY_TZ).strftime('%Y-%m-%d %H:%M:%S')
        
        # Determine chat type
        chat_type = "Private" if chat.type == Chat.PRIVATE else f"Group ({chat.title})"
        
        # Create log message for local logging
        log_msg = (
            f"USER: @{user.username or 'NoUsername'} ({user.first_name} {user.last_name or ''}) "
            f"| ID: {user.id} | CHAT: {chat_type} | ACTION: {action}"
        )
        
        if details:
            log_msg += f" | DETAILS: {details}"
        
        if client_number:
            log_msg += f" | CLIENT: {client_number}"
        
        if success:
            log_msg += f" | RESULT: {success}"
        
        # Log locally
        logger.info(log_msg)
        
        # Log persistently to Google Sheets
        persistent_logger.log_to_sheets(
            timestamp=timestamp,
            level="INFO",
            user_id=str(user.id),
            username=f"@{user.username or 'NoUsername'} ({user.first_name})",
            action=action,
            details=details,
            chat_type=chat_type,
            client_number=client_number,
            success=success
        )
    
    @staticmethod
    def log_system_event(event: str, details: str = ""):
        """Log system events (startup, errors, etc.)"""
        timestamp = datetime.now(MEXICO_CITY_TZ).strftime('%Y-%m-%d %H:%M:%S')
        
        # Log locally
        logger.info(f"SYSTEM EVENT: {event} | {details}")
        
        # Log persistently
        persistent_logger.log_to_sheets(
            timestamp=timestamp,
            level="SYSTEM",
            user_id="SYSTEM",
            username="Bot System",
            action=event,
            details=details,
            chat_type="System"
        )

# Initialize persistent logger
persistent_logger = PersistentLogger()

class GoogleSheetsManager:
    def __init__(self):
        self.service = None
        self.headers = []
        self.client_column = 0
        self.spreadsheet_id = os.getenv('SPREADSHEET_ID')
        self._authenticate()
        if self.service:
            self._find_client_column()
    
    def _authenticate(self):
        try:
            project_id = os.getenv('GCP_PROJECT_ID')
            if not project_id:
                logger.error("❌ GCP_PROJECT_ID environment variable not set.")
                self.service = None
                return

            credentials_json = get_secret(project_id, 'google-credentials-json')
            if credentials_json:
                logger.info("Using Google Sheets credentials from Secret Manager")
                credentials_data = json.loads(credentials_json)
                creds = Credentials.from_service_account_info(
                    credentials_data, 
                    scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
                )
            else:
                raise ValueError("❌ Failed to fetch 'google-credentials-json' from Secret Manager.")
            
            # Disable discovery cache to avoid noisy logs in server environments
            self.service = build('sheets', 'v4', credentials=creds, cache_discovery=False)
            logger.info("✅ Google Sheets connected successfully")
        except Exception as e:
            logger.error(f"❌ Failed to authenticate with Google Sheets: {e}")
            self.service = None
    
    def _find_client_column(self):
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range='Sheet1!1:1'
            ).execute()
            
            self.headers = result.get('values', [[]])[0]
            
            # Look for client number column
            client_keywords = ['client', 'number', 'id', 'code']
            for i, header in enumerate(self.headers):
                if any(keyword in header.lower().strip() for keyword in client_keywords):
                    self.client_column = i
                    logger.info(f"📋 Client column found: '{header}' at position {i}")
                    return
            
            self.client_column = 0
            logger.info("📋 Using first column as client column by default")
        except Exception as e:
            logger.error(f"❌ Error finding client column: {e}")
    
    def get_client_data(self, client_number: str) -> Optional[Dict[str, str]]:
        if not self.service:
            return None
        
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id, 
                range='Sheet1!A:Z'
            ).execute()
            
            values = result.get('values', [])
            if len(values) < 2:
                return None
            
            for row_index, row in enumerate(values[1:], start=2):
                if not row or len(row) <= self.client_column:
                    continue
                
                cell_value = str(row[self.client_column]).strip().lower()
                search_value = str(client_number).strip().lower()
                
                if cell_value == search_value:
                    logger.info(f"✅ Found client at row {row_index}")
                    
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
    
    def get_sheet_info(self) -> Dict[str, Any]:
        try:
            if not self.service:
                return {'total_clients': 0, 'headers': [], 'client_column': 'Unknown'}
            
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range='Sheet1!A:A'
            ).execute()
            
            values = result.get('values', [])
            total_rows = len(values) - 1
            
            return {
                'total_clients': max(0, total_rows),
                'headers': self.headers,
                'client_column': self.headers[self.client_column] if self.headers and self.client_column < len(self.headers) else 'Unknown'
            }
        except Exception as e:
            logger.error(f"Error getting sheet info: {e}")
            return {'total_clients': 0, 'headers': [], 'client_column': 'Unknown'}

class TelegramBot:
    def __init__(self):
        logger.info("🔧 Starting TelegramBot initialization...")
        
        project_id = os.getenv('GCP_PROJECT_ID')
        logger.info(f"🔧 Project ID: {project_id}")
        if not project_id:
            raise ValueError("❌ GCP_PROJECT_ID not found in environment variables")
        
        logger.info("🔧 Fetching Telegram bot token from Secret Manager...")
        self.token = get_secret(project_id, 'telegram-bot-token')
        if not self.token:
            logger.error("❌ Could not fetch 'telegram-bot-token' from Secret Manager")
            raise ValueError("❌ Could not fetch 'telegram-bot-token' from Secret Manager")
        
        logger.info("🔧 Token retrieved successfully, initializing Google Sheets manager...")
        self.sheets_manager = GoogleSheetsManager()
        self.sheet_info = self.sheets_manager.get_sheet_info()
        self.application = None
        self.bot_info = None  # To cache bot info
        
        logger.info("✅ Bot initialized successfully")
    
    def _is_authorized_user(self, user_id: int) -> bool:
        authorized_users = os.getenv('AUTHORIZED_USERS', '').split(',')
        return str(user_id) in authorized_users if authorized_users != [''] else True
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            user = update.effective_user
            
            # Log the action
            EnhancedUserActivityLogger.log_user_action(update, "START_COMMAND")
            
            if update.effective_chat.type == Chat.PRIVATE:
                msg = (
                    f"👋 ¡Hola {user.first_name}! Bienvenido a **Client Data Bot**.\n\n"
                    "Envíame un número de cliente y te daré su información.\n\n"
                    "Usa /help para ver todos los comandos."
                )
            else:
                msg = (
                    f"👋 ¡Hola a todos! Soy **Client Data Bot**.\n\n"
                    "Para buscar un cliente en este grupo, mencióname o responde a uno de mis mensajes.\n"
                    "Ejemplo: @mi_bot_username 12345"
                )
            
            await update.message.reply_text(msg, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error in start_command: {e}")
            await update.message.reply_text("❌ Error interno del bot.")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            chat = update.effective_chat
            user = update.effective_user
            message_text = update.message.text.strip()
            
            logger.info(f"📨 Processing message from {user.first_name} in {chat.type}: '{message_text}'")
            
            # Determine if message should be processed
            is_addressed_to_bot = False
            message_to_process = ""
            
            if chat.type == Chat.PRIVATE:
                is_addressed_to_bot = True
                message_to_process = message_text
            elif chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
                if not self.bot_info:
                    self.bot_info = await context.bot.get_me()
                
                bot_username = self.bot_info.username.lower() if self.bot_info.username else ""
                
                # Check for mention
                if f"@{bot_username}" in message_text.lower():
                    is_addressed_to_bot = True
                    message_to_process = message_text.lower().replace(f"@{bot_username}", "").strip()
                # Check for reply
                elif (update.message.reply_to_message and 
                      update.message.reply_to_message.from_user.id == self.bot_info.id):
                    is_addressed_to_bot = True
                    message_to_process = message_text
            
            if not is_addressed_to_bot:
                # This case should ideally not be hit if filters are set up correctly
                return
            
            # Extract client number
            client_number = ''.join(filter(str.isdigit, message_to_process))
            
            if not client_number:
                # Only reply if the bot was directly addressed but no number was found
                if chat.type == Chat.PRIVATE or (f"@{self.bot_info.username.lower()}" in message_text.lower()):
                    await update.message.reply_text(
                        "❌ Por favor, envía un número de cliente válido.",
                        reply_to_message_id=update.message.message_id
                    )
                return
            
            # Search for client data
            client_data = self.sheets_manager.get_client_data(client_number)
            
            if client_data:
                # Log successful search
                EnhancedUserActivityLogger.log_user_action(update, "SEARCH", f"Client: {client_number}, Fields: {len(client_data)}", client_number, "SUCCESS")
                
                response = f"✅ **Cliente encontrado: `{client_number}`**\n\n"
                
                field_mappings = {
                    'client phone number': 'Número 📞',
                    'cliente': 'Cliente 🙋🏻‍♀️',
                    'correo': 'Correo ✉️',
                    'other info': 'Otra Información ℹ️'
                }
                
                for key, value in client_data.items():
                    display_key = field_mappings.get(key.lower().strip(), key.strip())
                    response += f"**{display_key}:** {value}\n"
                
                user_display = f"@{user.username}" if user.username else user.first_name
                response += f"\n**Buscado por:** {user_display}"
                
                await update.message.reply_text(
                    response, 
                    parse_mode='Markdown',
                    reply_to_message_id=update.message.message_id
                )
            else:
                # Log failed search
                EnhancedUserActivityLogger.log_user_action(update, "SEARCH", f"Client: {client_number}, Not found", client_number, "FAILURE")
                
                await update.message.reply_text(
                    f"❌ No se encontró información para el cliente: `{client_number}`",
                    parse_mode='Markdown',
                    reply_to_message_id=update.message.message_id
                )
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            try:
                await update.message.reply_text("❌ Error interno procesando el mensaje.")
            except:
                pass
    
    def setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self.start_command))
        
        # More efficient message handling
        # 1. Private chats (any text)
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, self.handle_message)
        )
        # 2. Replies to the bot in groups
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND & filters.REPLY & filters.ChatType.GROUPS, self.handle_message)
        )
        # 3. Mentions in groups
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Entity("mention") & filters.ChatType.GROUPS, self.handle_message)
        )
        
        logger.info("✅ All handlers setup complete")
    
    def run(self):
        try:
            self.application = Application.builder().token(self.token).build()
            self.setup_handlers()
            
            # Log system startup early
            EnhancedUserActivityLogger.log_system_event("BOT_STARTUP", "Bot starting in polling mode")
            
            logger.info("🚀 Starting bot with run_polling()...")
            logger.info("📊 Sheets connected: %s", "✅ Yes" if self.sheets_manager.service else "❌ No")
            logger.info("📋 Total clients: %s", self.sheet_info.get('total_clients', 'Unknown'))
            logger.info("💾 Persistent logging: %s", "✅ Yes" if persistent_logger.service else "❌ No")
            
            # High-level API handles initialize/start/polling/idle/stop
            self.application.run_polling(drop_pending_updates=True)
            
        except KeyboardInterrupt:
            logger.info("🛑 Bot stopped by user")
            EnhancedUserActivityLogger.log_system_event("BOT_SHUTDOWN", "Bot stopped by user (Ctrl+C)")
        except Exception as e:
            logger.error(f"❌ Critical error running bot: {e}")
            EnhancedUserActivityLogger.log_system_event("BOT_ERROR", f"Critical error: {str(e)}")
            raise