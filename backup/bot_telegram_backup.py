import os
import logging
from typing import Dict, Any, Optional, List

# Load environment variables from .env file (only if .env exists)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, use system env vars

# Importar Flask primero
from flask import Flask, request

# Importar Telegram y otras librerías
from telegram import Update, Chat
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import json
import sys
import pytz
MEXICO_CITY_TZ = pytz.timezone("America/Mexico_City")
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s | %(name)s | %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# --- Variables Globales para Inicialización "Lazy" ---
telegram_bot: Optional[Any] = None

# --- Clases de Lógica del Bot ---

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
                print("Using persistent logging credentials from environment variable")
                credentials_data = json.loads(credentials_json)
                creds = Credentials.from_service_account_info(
                    credentials_data, 
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
            # Fallback to credentials file (for local development)
            elif os.path.exists('credentials.json'):
                print("Using persistent logging credentials from file")
                creds = Credentials.from_service_account_file(
                    'credentials.json', 
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
            else:
                print("⚠️ No credentials found for persistent logging - neither GOOGLE_CREDENTIALS_JSON nor credentials.json")
                self.service = None
                return
            
            self.service = build('sheets', 'v4', credentials=creds)
            print("✅ Persistent logger connected to Google Sheets")
            
        except json.JSONDecodeError:
            print("⚠️ Invalid JSON in GOOGLE_CREDENTIALS_JSON for persistent logging")
            self.service = None
        except Exception as e:
            print(f"⚠️ Could not setup persistent logging: {e}")
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
            print(f"❌ Error saving to persistent log: {e}")
            return False
    
    def get_recent_logs(self, limit: int = 50) -> List[List[str]]:
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
            logger.error(f"❌ Error al leer logs persistentes: {e}"); return []
    
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
            print(f"❌ Error getting stats from persistent logs: {e}")
            return {}

# Enhanced logging setup for Railway + Persistent storage
def setup_enhanced_logging():
    """Setup comprehensive logging system"""
    # Create logs directory if possible (will be temporary in Railway)
    try:
        os.makedirs('logs', exist_ok=True)
    except:
        pass
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler (Railway captures this)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Detailed formatter for console
    console_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Try to setup file logging (temporary but useful)
    try:
        # General log file
        file_handler = logging.FileHandler('logs/bot.log', encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(console_formatter)
        root_logger.addHandler(file_handler)
        
        # Activity log file
        activity_file_handler = logging.FileHandler('logs/user_activity.log', encoding='utf-8')
        activity_file_handler.setLevel(logging.INFO)
        activity_formatter = logging.Formatter('%(asctime)s | %(message)s')
        activity_file_handler.setFormatter(activity_formatter)
        
        # Activity logger with both console and file
        activity_logger = logging.getLogger('activity')
        activity_logger.setLevel(logging.INFO)
        activity_logger.addHandler(activity_file_handler)
        activity_logger.addHandler(console_handler)  # Also to console for Railway
        activity_logger.propagate = False
        
    except Exception as e:
        print(f"⚠️ File logging setup failed (normal for Railway): {e}")
        # Fallback: activity logger only to console
        activity_logger = logging.getLogger('activity')
        activity_logger.setLevel(logging.INFO)
        activity_logger.addHandler(console_handler)
        activity_logger.propagate = False
    
    return root_logger, activity_logger

# Setup logging
logger, activity_logger = setup_enhanced_logging()

# Initialize persistent logger
persistent_logger = PersistentLogger()

# Configuration
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
CREDENTIALS_FILE = 'credentials.json'

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
        
        # Log locally (temporary files + console)
        activity_logger.info(log_msg)
        
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

class GoogleSheetsManager:
    def __init__(self):
        self.creds = None
        self.service = None
        self.headers = []
        self.client_column = None
        self._authenticate()
        if self.service: self._find_client_column()
    
    def _authenticate(self):
        """Authenticate with Google Sheets API"""
        try:
            # Try environment variable first (for production)
            credentials_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
            if not credentials_json: 
                logger.error("❌ Env var GOOGLE_CREDENTIALS_JSON no está configurada.")
                raise ValueError("Env var GOOGLE_CREDENTIALS_JSON no está configurada.")
            credentials_data = json.loads(credentials_json)
            creds = Credentials.from_service_account_info(credentials_data, scopes=['https://www.googleapis.com/auth/spreadsheets.readonly'])
            self.service = build('sheets', 'v4', credentials=creds)
            logger.info("✅ Google Sheets conectado exitosamente.")
        except Exception as e:
            logger.error(f"❌ Falló la autenticación con Google Sheets: {e}"); self.service = None
    
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
                if any(keyword in header.lower().strip() for keyword in client_keywords):
                    self.client_column = i; logger.info(f"📋 Columna de cliente encontrada: '{header}' en la posición {i}"); return
            logger.info("📋 Usando la primera columna como columna de cliente por defecto.")
        except Exception as e: logger.error(f"❌ Error al encontrar la columna de cliente: {e}")
    
    def get_client_data(self, client_number: str) -> Optional[Dict[str, str]]:
        if not self.service: return None
        try:
            spreadsheet_id = os.getenv('SPREADSHEET_ID')
            result = self.service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range='Sheet1!A:Z').execute()
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
            logger.error(f"❌ Error al buscar cliente: {e}"); return None
    
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
    
    def _is_authorized_user(self, user_id: int) -> bool:
        """Check if user is authorized"""
        authorized_users = os.getenv('AUTHORIZED_USERS', '').split(',')
        return str(user_id) in authorized_users if authorized_users != [''] else True
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user; EnhancedUserActivityLogger.log_user_action(update, "START_COMMAND")
        msg = (f"👋 ¡Hola {user.first_name}! Bienvenido a **Client Data Bot**.\n\nEnvíame un número de cliente y te daré su información.\n\nUsa `/help` para ver todos los comandos.") if update.effective_chat.type == Chat.PRIVATE else (f"👋 ¡Hola a todos! Soy **Client Data Bot**.\n\nPara buscar un cliente en este grupo, menciónname o responde a uno de mis mensajes.\nEjemplo: `@mi_bot_username 12345`")
    await update.message.reply_text(msg, parse_mode=None)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        chat = update.effective_chat
        
        # Log the action
        EnhancedUserActivityLogger.log_user_action(update, "HELP_COMMAND")
        help_message = ("📖 **Ayuda de Client Data Bot**\n\n**Buscar clientes:**\n• **En chat privado:** Simplemente envía el número de cliente.\n• **En grupos:** Menciona al bot (`@username_del_bot 12345`) o responde a un mensaje del bot con el número.\n\n**Comandos disponibles:**\n• `/start` - Mensaje de bienvenida.\n• `/help` - Muestra esta ayuda.\n• `/info` - Muestra información sobre la base de datos.\n• `/status` - Verifica el estado del bot y la conexión.\n• `/whoami` - Muestra tu información de Telegram.\n• `/stats` - Muestra estadísticas de uso (autorizado).\n• `/plogs` - Muestra los últimos logs de actividad (autorizado).")
    await update.message.reply_text(help_message, parse_mode=None)
    
    async def info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show spreadsheet information"""
        # Log the action
        EnhancedUserActivityLogger.log_user_action(update, "INFO_COMMAND")
        
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
        
    await update.message.reply_text(message, parse_mode=None)
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check bot and system status"""
        # Log the action
        EnhancedUserActivityLogger.log_user_action(update, "STATUS_COMMAND")
        
        try:
            # Test Google Sheets connection
            test_info = self.sheets_manager.get_sheet_info()
            sheets_status = "✅ Connected"
        except:
            sheets_status = "❌ Connection Error"
        
        # Test persistent logging
        persistent_status = "✅ Active" if persistent_logger.service else "❌ Not configured"
        
        chat_context = "Private" if update.effective_chat.type == Chat.PRIVATE else "Group"
        
        status_message = (
            "🔧 **Bot Status Check:**\n\n"
            f"🤖 **Bot:** ✅ Running\n"
            f"📊 **Google Sheets:** {sheets_status}\n"
            f"📋 **Clients Available:** {test_info.get('total_clients', 'Unknown')}\n"
            f"🔍 **Search Ready:** {'✅ Yes' if sheets_status == '✅ Connected' else '❌ No'}\n"
            f"💬 **Chat Type:** {chat_context}\n"
            f"📝 **Local Logging:** ✅ Active\n"
            f"💾 **Persistent Logging:** {persistent_status}\n\n"
            f"**Mexico City Time:** {datetime.now(MEXICO_CITY_TZ).strftime('%H:%M:%S')}"
        )
        
    await update.message.reply_text(status_message, parse_mode=None)
    
    async def whoami_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        EnhancedUserActivityLogger.log_user_action(update, "WHOAMI_COMMAND"); user = update.effective_user
        auth_status = "✅ Sí" if self._is_authorized_user(user.id) else "❌ No"
        user_info = (f"👤 **Tu Información:**\n\n🆔 **User ID:** `{user.id}`\n👤 **Nombre:** {user.first_name} {user.last_name or ''}\n📱 **Username:** @{user.username or 'No tienes'}\n🔑 **Autorizado:** {auth_status}")
    await update.message.reply_text(user_info, parse_mode=None)
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        EnhancedUserActivityLogger.log_user_action(update, "STATS_COMMAND")
        if not self._is_authorized_user(update.effective_user.id): await update.message.reply_text("⛔ No estás autorizado para ver las estadísticas."); return
        stats = persistent_logger.get_stats_from_logs()
        if not stats: await update.message.reply_text("No hay estadísticas disponibles."); return
        stats_message = (f"📈 **Estadísticas de Uso:**\n\n📊 **Logs totales:** {stats.get('total_logs', 0)}\n📅 **Actividad de hoy:** {stats.get('today_logs', 0)}\n\n🔍 **Búsquedas Totales:** {stats.get('total_searches', 0)}\n  - ✅ Exitosas: {stats.get('successful_searches', 0)}\n  - ❌ Fallidas: {stats.get('failed_searches', 0)}\n\n👥 **Actividad de Hoy:**\n  - Usuarios únicos: {stats.get('unique_users_today', 0)}\n  - Grupos activos: {stats.get('active_groups_today', 0)}")
    await update.message.reply_text(stats_message, parse_mode=None)
    
    async def logs_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        EnhancedUserActivityLogger.log_user_action(update, "LOGS_COMMAND")
        if not self._is_authorized_user(update.effective_user.id): await update.message.reply_text("⛔ No estás autorizado para ver los logs."); return
        await update.message.reply_text("📝 El comando `/logs` no está disponible. Usa `/plogs` para ver los logs de Google Sheets.")
    
    async def persistent_logs_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        EnhancedUserActivityLogger.log_user_action(update, "PLOGS_COMMAND")
        if not self._is_authorized_user(update.effective_user.id): await update.message.reply_text("⛔ No estás autorizado para ver los logs persistentes."); return
        logs = persistent_logger.get_recent_logs()
        if not logs: await update.message.reply_text("No se encontraron logs persistentes."); return
        log_message = "📝 **Últimos 20 Logs Persistentes:**\n\n```\n"
        for entry in logs:
            if isinstance(entry, list) and len(entry) >= 5:
                log_message += f"{entry[0]:<16} | {entry[1]:<15} | {entry[4]}\n"
        log_message += "```"
    await update.message.reply_text(log_message, parse_mode=None)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat, user, message_text_original = update.effective_chat, update.effective_user, update.message.text.strip()
        logger.info(f"📨 Mensaje de {user.first_name} en chat {chat.type}: '{message_text_original}'")
        message_to_process, is_addressed_to_bot = "", False
        if chat.type == Chat.PRIVATE: is_addressed_to_bot, message_to_process = True, message_text_original
        elif chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
            bot_info = await context.bot.get_me()
            bot_username = bot_info.username.lower()
            if f"@{bot_username}" in message_text_original.lower(): is_addressed_to_bot, message_to_process = True, message_text_original.lower().replace(f"@{bot_username}", "").strip()
            elif update.message.reply_to_message and update.message.reply_to_message.from_user.id == bot_info.id: is_addressed_to_bot, message_to_process = True, message_text_original
        if not is_addressed_to_bot: logger.info("Bot no fue mencionado en grupo. Ignorando."); return
        client_number = ''.join(filter(str.isdigit, message_to_process))
        if not client_number: logger.warning(f"No se encontraron dígitos en '{message_to_process}'"); await update.message.reply_text("❌ Por favor, envía solo el número de cliente.", reply_to_message_id=update.message.id); return
        client_data = self.sheets_manager.get_client_data(client_number)
        if client_data:
            EnhancedUserActivityLogger.log_search_result(update, client_number, True, len(client_data))
            response = f"✅ **Cliente encontrado: `{client_number}`**\n\n"
            field_mappings = {'client phone number': 'Número 📞', 'cliente': 'Cliente 🙋🏻‍♀️', 'correo': 'Correo ✉️', 'other info': 'Otra Información ℹ️'}
            for key, value in client_data.items():
                display_key = field_mappings.get(key.lower().strip(), key.strip())
                response += f"**{display_key}:** {value}\n"
            user_display = f"@{user.username}" if user.username else user.first_name
            response += f"**Buscado por 🙋🏻‍♂️** {user_display}\n"
            await update.message.reply_text(response, parse_mode='HTML', reply_to_message_id=update.message.id)
        else:
            EnhancedUserActivityLogger.log_search_result(update, client_number, False)
            await update.message.reply_text(f"❌ No se encontró cliente con el número <code>{html_escape(client_number)}</code>.", parse_mode='HTML', reply_to_message_id=update.message.id)

# --- Lógica de Inicialización (serverless-safe) ---
async def _build_app_for_request(telegram_bot_instance):
    """
    Construye una app local por cada petición
    Esto evita reusar objetos/clients ligados a event loops previos (problema en serverless).
    """
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN no encontrado")
    # app_local
    app_local = Application.builder().token(bot_token).build()
    #handlers
    app_local.add_handler(CommandHandler("start", telegram_bot_instance.start_command))
    app_local.add_handler(CommandHandler("help", telegram_bot_instance.help_command))
    app_local.add_handler(CommandHandler("info", telegram_bot_instance.info_command))
    app_local.add_handler(CommandHandler("status", telegram_bot_instance.status_command))
    app_local.add_handler(CommandHandler("stats", telegram_bot_instance.stats_command))
    app_local.add_handler(CommandHandler("whoami", telegram_bot_instance.whoami_command))
    app_local.add_handler(CommandHandler("logs", telegram_bot_instance.logs_command))
    app_local.add_handler(CommandHandler("plogs", telegram_bot_instance.persistent_logs_command))
    app_local.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, telegram_bot_instance.handle_message))
    #inicializamos
    await app_local.initialize()
    logger.debug("app local inicializada")
    return app_local

# App flask y Webhook

app = Flask(__name__)

@app.route("/api/telegram", methods=['POST'])
async def webhook():
    '''
    Webhook entrypoint. Construye una Application local por petición y la cierra al final.
    Mantiene "telegram_bot" como instancia persistente (Google Sheets, estado).
    '''
    global telegram_bot
    if not telegram_bot:
        try:
            telegram_bot = TelegramBot()
            if not telegram_bot.sheets_manager.service:
                logger.error("No se pudo conectar con Google Sheets")
                return "Fallo en inicializacion sheets", 500
        except Exception as e:
            logger.exception("Fallo en inicializacion (bot)")
            return "Fallo en la inicialización (bot)", 500
    # build local app
    try:
        app_local = await _build_app_for_request(telegram_bot)
    except Exception as e:
        logger.exception(f"Fallo crítico al crear TelegramBot: {e}")
        return "init error", 500
    # 
    try:
        update = Update.de_json(request.get_json(force=True), app_local.bot)
        await app_local.process_update(update)
        return "ok", 200
    except Exception as e:
        logger.exception(f"Error al procesar webhook: {e}")
        return "error", 500
    finally:
        # Siempre cerramos recursos del Application local para seguridad
        try:
            await app_local.shutdown()
        except Exception as e:
            logger.warning(f"Error al cerrar la app local: {e}")

@app.route("/")
def index():
    # Como ya no usamos `application` global para servir requests serverless, mostramos el estado de telegram_bot
    status = "✅ Bot inicializado y listo." if telegram_bot else "⏳ Bot aún no inicializado. Envía un mensaje para activarlo."
    return f"<h1>Estado del Bot</h1><p>{status}</p>"

if __name__ == "__main__":
    app.run(debug=True)