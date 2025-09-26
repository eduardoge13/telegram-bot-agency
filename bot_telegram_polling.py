#!/usr/bin/env python3
"""
Telegram Bot for Client Data Management - Polling Version
Optimized for Render deployment - NO event loop issues, robust & simple
"""

import os
import logging
import asyncio
import sys
import json
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

# Log Python version and environment variables
print(f"Running Python version: {sys.version}")
print("Environment Variables:")
for key, value in os.environ.items():
    print(f"{key}: {value}")


def ensure_supported_python_version():
    """Try to keep running on Python 3.13+ while warning loudly."""
    if sys.version_info >= (3, 13):
        message = (
            "Python 3.13 introduces breaking changes for python-telegram-bot v20.x. "
            "Applying runtime compatibility patch, but PLEASE pin Render to Python 3.12.x "
            "(runtime.txt or PYTHON_VERSION env)."
        )
        logger.warning(message)


def patch_ptb_for_python_313():
    """Monkey-patch PTB Updater slots so run_polling works under Python 3.13."""
    if sys.version_info < (3, 13):
        return

    try:
        from telegram.ext import _updater  # type: ignore

        updater_cls = getattr(_updater, "Updater", None)
        if updater_cls is None:
            logger.error("Could not find Updater class to patch; aborting.")
            raise RuntimeError("Updater class missing")

        slots: Tuple[str, ...] = getattr(updater_cls, "__slots__", tuple())
        needed = (
            "_Updater__polling_cleanup_cb",
            "_Updater__start_polling_future",
            "_Updater__bootstrap_result",
        )

        missing = tuple(name for name in needed if name not in slots)
        if missing:
            updater_cls.__slots__ = slots + missing  # type: ignore[attr-defined]
            logger.warning(
                "Applied python-telegram-bot Updater compatibility patch for Python 3.13: added %s",
                ", ".join(missing),
            )
    except Exception as exc:
        logger.error("Failed to apply python-telegram-bot compatibility patch: %s", exc)
        raise


ensure_supported_python_version()
patch_ptb_for_python_313()

class PersistentLogger:
    """Store all logs permanently in Google Sheets"""
    
    def __init__(self):
        self.logs_sheet_id = os.getenv('LOGS_SPREADSHEET_ID')
        self.service = None
        self._setup_sheets_service()
    
    def _setup_sheets_service(self):
        """Setup Google Sheets service for logging"""
        try:
            # Try environment variable first (for production)
            credentials_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
            if credentials_json:
                try:
                    logger.info("Using persistent logging credentials from environment variable")
                    credentials_data = json.loads(credentials_json)
                    creds = Credentials.from_service_account_info(
                        credentials_data, 
                        scopes=['https://www.googleapis.com/auth/spreadsheets']
                    )
                except json.JSONDecodeError as e:
                    logger.warning(f"⚠️ Invalid JSON in GOOGLE_CREDENTIALS_JSON: {e}")
                    # Try to read from Render secret file path
                    secret_file_path = os.getenv('GOOGLE_CREDENTIALS_FILE_PATH', '/etc/secrets/credentials.json')
                    if os.path.exists(secret_file_path):
                        logger.info(f"Using persistent logging credentials from secret file: {secret_file_path}")
                        creds = Credentials.from_service_account_file(
                            secret_file_path, 
                            scopes=['https://www.googleapis.com/auth/spreadsheets']
                        )
                    else:
                        logger.warning(f"⚠️ Secret file not found at: {secret_file_path}")
                        self.service = None
                        return
            # Fallback to credentials file (for local development)
            elif os.path.exists('credentials.json'):
                logger.info("Using persistent logging credentials from file")
                creds = Credentials.from_service_account_file(
                    'credentials.json', 
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
            else:
                logger.warning("⚠️ No credentials found for persistent logging - neither GOOGLE_CREDENTIALS_JSON nor credentials.json")
                self.service = None
                return
            
            # Disable discovery cache to avoid noisy logs in server environments
            self.service = build('sheets', 'v4', credentials=creds, cache_discovery=False)
            logger.info("✅ Persistent logger connected to Google Sheets")
            
        except json.JSONDecodeError:
            logger.warning("⚠️ Invalid JSON in GOOGLE_CREDENTIALS_JSON for persistent logging")
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
    
    def get_recent_logs(self, limit: int = 20) -> List[List[str]]:
        """Get recent logs from Google Sheets"""
        if not self.service or not self.logs_sheet_id:
            return []
        
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.logs_sheet_id,
                range='Sheet1!A:I'
            ).execute()
            
            values = result.get('values', [])
            if len(values) <= 1:  # Only headers or empty
                return []
            
            # Return last N entries (excluding header)
            data_rows = values[1:]  # Skip header
            return data_rows[-limit:] if len(data_rows) > limit else data_rows
            
        except Exception as e:
            logger.error(f"❌ Error reading persistent logs: {e}")
            return []
    
    def get_stats_from_logs(self) -> Dict[str, Any]:
        """Get usage statistics from persistent logs"""
        if not self.service or not self.logs_sheet_id:
            return {}
        
        try:
            # Get today's date
            today = date.today().strftime('%Y-%m-%d')
            
            # Get all logs
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.logs_sheet_id,
                range='Sheet1!A:I'
            ).execute()
            
            values = result.get('values', [])
            if len(values) <= 1:
                return {'total_logs': 0, 'today_logs': 0}
            
            data_rows = values[1:]  # Skip header
            today_logs = []
            search_logs = []
            users_today = set()
            groups_today = set()
            
            for row in data_rows:
                if len(row) >= 5:  # Minimum required columns
                    timestamp = row[0]
                    action = row[4] if len(row) > 4 else ""
                    user_id = row[2] if len(row) > 2 else ""
                    chat_type = row[6] if len(row) > 6 else ""
                    
                    # Count today's activity
                    if today in timestamp:
                        today_logs.append(row)
                        if user_id:
                            users_today.add(user_id)
                        if "Group" in chat_type:
                            groups_today.add(chat_type)
                    
                    # Count searches
                    if "SEARCH" in action:
                        search_logs.append(row)
            
            successful_searches = len([log for log in search_logs if len(log) > 8 and log[8] == "SUCCESS"])
            failed_searches = len([log for log in search_logs if len(log) > 8 and log[8] == "FAILURE"])
            
            return {
                'total_logs': len(data_rows),
                'today_logs': len(today_logs),
                'total_searches': len(search_logs),
                'successful_searches': successful_searches,
                'failed_searches': failed_searches,
                'unique_users_today': len(users_today),
                'active_groups_today': len(groups_today)
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting stats from persistent logs: {e}")
            return {}

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
    def log_search_result(update: Update, client_number: str, found: bool, fields_count: int = 0):
        """Log search results with complete information"""
        result = "SUCCESS" if found else "FAILURE"
        details = f"Client: {client_number}, Fields: {fields_count}" if found else f"Client: {client_number}, Not found"
        
        EnhancedUserActivityLogger.log_user_action(
            update, 
            "SEARCH", 
            details, 
            client_number, 
            result
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
            credentials_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
            if credentials_json:
                try:
                    logger.info("Using Google Sheets credentials from environment variable")
                    credentials_data = json.loads(credentials_json)
                    creds = Credentials.from_service_account_info(
                        credentials_data, 
                        scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
                    )
                except json.JSONDecodeError as e:
                    logger.warning(f"⚠️ Invalid JSON in GOOGLE_CREDENTIALS_JSON: {e}")
                    # Try to read from Render secret file path
                    secret_file_path = os.getenv('GOOGLE_CREDENTIALS_FILE_PATH', '/etc/secrets/credentials.json')
                    if os.path.exists(secret_file_path):
                        logger.info(f"Using Google Sheets credentials from secret file: {secret_file_path}")
                        creds = Credentials.from_service_account_file(
                            secret_file_path, 
                            scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
                        )
                    else:
                        raise ValueError(f"❌ Secret file not found at: {secret_file_path}")
            elif os.path.exists('credentials.json'):
                logger.info("Using Google Sheets credentials from local file")
                creds = Credentials.from_service_account_file(
                    'credentials.json', 
                    scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
                )
            else:
                raise ValueError("❌ GOOGLE_CREDENTIALS_JSON not found and no credentials.json file")
            
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
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.token:
            raise ValueError("❌ TELEGRAM_BOT_TOKEN not found in environment variables")
        
        self.sheets_manager = GoogleSheetsManager()
        self.sheet_info = self.sheets_manager.get_sheet_info()
        self.application = None
        
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
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            # Log the action
            EnhancedUserActivityLogger.log_user_action(update, "HELP_COMMAND")
            
            help_message = (
                "📖 **Ayuda de Client Data Bot**\n\n"
                "**Buscar clientes:**\n"
                "• **En chat privado:** Simplemente envía el número de cliente.\n"
                "• **En grupos:** Menciona al bot o responde a un mensaje del bot.\n\n"
                "**Comandos disponibles:**\n"
                "• `/start` - Mensaje de bienvenida\n"
                "• `/help` - Muestra esta ayuda\n"
                "• `/info` - Información sobre la base de datos\n"
                "• `/status` - Estado del bot y conexiones\n"
                "• `/stats` - Estadísticas de uso (autorizado)\n"
                "• `/plogs` - Muestra los últimos logs persistentes (autorizado)"
            )
            
            await update.message.reply_text(help_message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error in help_command: {e}")
            await update.message.reply_text("❌ Error interno del bot.")
    
    async def info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            # Log the action
            EnhancedUserActivityLogger.log_user_action(update, "INFO_COMMAND")
            
            info = self.sheet_info
            
            message = (
                "📋 **Información de la Base de Datos:**\n\n"
                f"📊 **Total de clientes:** {info['total_clients']}\n"
                f"🔍 **Columna de búsqueda:** {info['client_column']}\n\n"
                "**Campos disponibles:**\n"
            )
            
            if info['headers']:
                for i, header in enumerate(info['headers'][:8], 1):
                    message += f"• {header}\n"
                if len(info['headers']) > 8:
                    message += f"• ... y {len(info['headers']) - 8} campos más\n"
            else:
                message += "• No se encontraron campos\n"
            
            message += "\n💡 ¡Envía cualquier número de cliente para buscarlo!"
            
            await update.message.reply_text(message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error in info_command: {e}")
            await update.message.reply_text("❌ Error interno del bot.")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            # Log the action
            EnhancedUserActivityLogger.log_user_action(update, "STATUS_COMMAND")
            
            sheets_status = "✅ Conectado" if self.sheets_manager.service else "❌ Error"
            persistent_status = "✅ Active" if persistent_logger.service else "❌ Not configured"
            total_clients = self.sheet_info.get('total_clients', 'Desconocido')
            chat_context = "Privado" if update.effective_chat.type == Chat.PRIVATE else "Grupo"
            
            status_message = (
                "🔧 **Estado del Bot:**\n\n"
                f"🤖 **Bot:** ✅ Funcionando (Polling Mode)\n"
                f"📊 **Google Sheets:** {sheets_status}\n"
                f"📋 **Clientes disponibles:** {total_clients}\n"
                f"💬 **Tipo de chat:** {chat_context}\n"
                f"💾 **Persistent Logging:** {persistent_status}\n\n"
                f"**Hora de México:** {datetime.now(MEXICO_CITY_TZ).strftime('%H:%M:%S')}"
            )
            
            await update.message.reply_text(status_message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error in status_command: {e}")
            await update.message.reply_text("❌ Error interno del bot.")
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show usage statistics from persistent logs"""
        try:
            # Log the action
            EnhancedUserActivityLogger.log_user_action(update, "STATS_COMMAND")
            
            # Check authorization
            if not self._is_authorized_user(update.effective_user.id):
                await update.message.reply_text("⛔ No estás autorizado para ver las estadísticas.")
                return
            
            # Get stats
            stats = persistent_logger.get_stats_from_logs()
            
            if not stats:
                await update.message.reply_text("📊 No hay estadísticas disponibles. Asegúrate de que LOGS_SPREADSHEET_ID esté configurado.")
                return
            
            stats_message = (
                f"📈 **Estadísticas de Uso:**\n\n"
                f"📊 **Logs totales:** {stats.get('total_logs', 0)}\n"
                f"📅 **Actividad de hoy:** {stats.get('today_logs', 0)}\n\n"
                f"🔍 **Búsquedas Totales:** {stats.get('total_searches', 0)}\n"
                f"  - ✅ Exitosas: {stats.get('successful_searches', 0)}\n"
                f"  - ❌ Fallidas: {stats.get('failed_searches', 0)}\n\n"
                f"👥 **Actividad de Hoy:**\n"
                f"  - Usuarios únicos: {stats.get('unique_users_today', 0)}\n"
                f"  - Grupos activos: {stats.get('active_groups_today', 0)}"
            )
            
            await update.message.reply_text(stats_message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error in stats_command: {e}")
            await update.message.reply_text("❌ Error interno del bot.")
    
    async def plogs_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show recent persistent logs"""
        try:
            # Log the action
            EnhancedUserActivityLogger.log_user_action(update, "PLOGS_COMMAND")
            
            # Check authorization
            if not self._is_authorized_user(update.effective_user.id):
                await update.message.reply_text("⛔ No estás autorizado para ver los logs persistentes.")
                return
            
            # Get recent logs
            logs = persistent_logger.get_recent_logs()
            
            if not logs:
                await update.message.reply_text("📝 No se encontraron logs persistentes. Asegúrate de que LOGS_SPREADSHEET_ID esté configurado.")
                return
            
            log_message = "📝 **Últimos 20 Logs Persistentes:**\n\n```\n"
            log_message += f"{'Timestamp':<16} | {'Level':<8} | {'Action'}\n"
            log_message += "-" * 50 + "\n"
            
            for entry in logs[-20:]:  # Show last 20
                if isinstance(entry, list) and len(entry) >= 5:
                    timestamp = entry[0][:16] if len(entry[0]) > 16 else entry[0]
                    level = entry[1][:8] if len(entry[1]) > 8 else entry[1]
                    action = entry[4][:25] if len(entry[4]) > 25 else entry[4]
                    log_message += f"{timestamp:<16} | {level:<8} | {action}\n"
            
            log_message += "```"
            
            # Check message length
            if len(log_message) > 4096:
                log_message = log_message[:4000] + "\n...\n```"
            
            await update.message.reply_text(log_message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error in plogs_command: {e}")
            await update.message.reply_text("❌ Error interno del bot.")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            chat = update.effective_chat
            user = update.effective_user
            message_text = update.message.text.strip()
            
            logger.info(f"📨 Message from {user.first_name} in {chat.type}: '{message_text}'")
            
            # Determine if message should be processed
            is_addressed_to_bot = False
            message_to_process = ""
            
            if chat.type == Chat.PRIVATE:
                is_addressed_to_bot = True
                message_to_process = message_text
            elif chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
                bot_info = await context.bot.get_me()
                bot_username = bot_info.username.lower() if bot_info.username else ""
                
                if f"@{bot_username}" in message_text.lower():
                    is_addressed_to_bot = True
                    message_to_process = message_text.lower().replace(f"@{bot_username}", "").strip()
                elif (update.message.reply_to_message and 
                      update.message.reply_to_message.from_user.id == bot_info.id):
                    is_addressed_to_bot = True
                    message_to_process = message_text
            
            if not is_addressed_to_bot:
                return
            
            # Extract client number
            client_number = ''.join(filter(str.isdigit, message_to_process))
            
            if not client_number:
                await update.message.reply_text(
                    "❌ Por favor, envía solo el número de cliente.",
                    reply_to_message_id=update.message.message_id
                )
                return
            
            # Search for client data
            client_data = self.sheets_manager.get_client_data(client_number)
            
            if client_data:
                # Log successful search
                EnhancedUserActivityLogger.log_search_result(update, client_number, True, len(client_data))
                
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
                EnhancedUserActivityLogger.log_search_result(update, client_number, False)
                
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
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("info", self.info_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("plogs", self.plogs_command))
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
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

def main():
    try:
        logger.info("🤖 Initializing Telegram Bot for Polling...")
        bot = TelegramBot()
        bot.run()
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # --- Minimal HTTP server for Render health checks ---
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer

    def start_healthcheck_server():
        """Starts a simple HTTP server in a thread to respond to Render's health checks."""
        port = int(os.environ.get("PORT", 10000))
        
        class HealthcheckHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"OK")
            
            def log_message(self, format, *args):
                # Suppress noisy logging from the healthcheck server
                return

        try:
            server = HTTPServer(("0.0.0.0", port), HealthcheckHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            logger.info(f"✅ Healthcheck server started on port {port}")
        except Exception as e:
            logger.error(f"❌ Could not start healthcheck server: {e}")
            
    logger.info("🚀 Starting Client Data Bot - Polling Version")
    start_healthcheck_server()
    main()
