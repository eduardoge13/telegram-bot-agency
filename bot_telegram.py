import os
import logging
import json
import sys
from datetime import datetime, date
from typing import Dict, Any, Optional, List

# Importar Flask primero
from flask import Flask, request

# Importar Telegram y otras librerías
from telegram import Update, Chat
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import pytz
import asyncio

# --- Configuración Básica ---
MEXICO_CITY_TZ = pytz.timezone("America/Mexico_City")
# Logging simple para Vercel (solo a consola)
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s | %(name)s | %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# --- Variables Globales para Inicialización "Lazy" ---
# Se inicializarán en la primera solicitud
application: Optional[Application] = None
telegram_bot: Optional[Any] = None

# --- Clases de Lógica del Bot (Traídas del código original) ---

class PersistentLogger:
    """Almacena todos los logs de forma permanente en Google Sheets"""
    def __init__(self):
        self.logs_sheet_id = os.getenv('LOGS_SPREADSHEET_ID')
        self.service = None
        self._setup_sheets_service()

    def _setup_sheets_service(self):
        try:
            credentials_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
            if credentials_json:
                credentials_data = json.loads(credentials_json)
                creds = Credentials.from_service_account_info(
                    credentials_data, scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
                self.service = build('sheets', 'v4', credentials=creds)
                logger.info("✅ Logger persistente conectado a Google Sheets.")
            else:
                logger.warning("⚠️ No se encontraron credenciales para el logger persistente.")
                self.service = None
        except Exception as e:
            logger.error(f"❌ No se pudo configurar el logger persistente: {e}")
            self.service = None

    def log_to_sheets(self, timestamp: str, level: str, user_id: str, username: str, 
                     action: str, details: str, chat_type: str = "", 
                     client_number: str = "", success: str = ""):
        if not self.service: return False
        try:
            row_data = [timestamp, level, user_id, username, action, details, chat_type, client_number, success]
            self.service.spreadsheets().values().append(
                spreadsheetId=self.logs_sheet_id,
                range='Sheet1!A:I',
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body={'values': [row_data]}
            ).execute()
            return True
        except Exception as e:
            logger.error(f"❌ Error al guardar en log persistente: {e}")
            return False

    def get_recent_logs(self, limit: int = 20) -> List[List[str]]:
        if not self.service: return []
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.logs_sheet_id, range='Sheet1!A:I'
            ).execute()
            values = result.get('values', [])
            return values[-limit:] if values else []
        except Exception as e:
            logger.error(f"❌ Error al leer logs persistentes: {e}")
            return []

    def get_stats_from_logs(self) -> Dict[str, Any]:
        if not self.service: return {}
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.logs_sheet_id, range='Sheet1!A:I'
            ).execute()
            values = result.get('values', [[]])[1:] # Skip header
            if not values: return {}

            today = date.today().strftime('%Y-%m-%d')
            today_logs = [row for row in values if len(row) > 0 and today in row[0]]
            search_logs = [row for row in values if len(row) > 4 and "SEARCH" in row[4]]
            
            return {
                'total_logs': len(values),
                'today_logs': len(today_logs),
                'total_searches': len(search_logs),
                'successful_searches': len([log for log in search_logs if len(log) > 8 and log[8] == "SUCCESS"]),
                'failed_searches': len([log for log in search_logs if len(log) > 8 and log[8] == "FAILURE"]),
                'unique_users_today': len({log[2] for log in today_logs if len(log) > 2}),
                'active_groups_today': len({log[6] for log in today_logs if len(log) > 6 and "Group" in log[6]})
            }
        except Exception as e:
            logger.error(f"❌ Error al obtener estadísticas: {e}")
            return {}

persistent_logger = PersistentLogger()

class EnhancedUserActivityLogger:
    @staticmethod
    def log_user_action(update: Update, action: str, details: str = "", client_number: str = "", success: str = ""):
        user = update.effective_user
        chat = update.effective_chat
        timestamp = datetime.now(MEXICO_CITY_TZ).strftime('%Y-%m-%d %H:%M:%S')
        chat_type = "Private" if chat.type == Chat.PRIVATE else f"Group ({chat.title})"
        
        log_msg = f"USER: @{user.username or 'N/A'} ({user.id}) | CHAT: {chat_type} | ACTION: {action}"
        if details: log_msg += f" | DETAILS: {details}"
        logger.info(log_msg)
        
        persistent_logger.log_to_sheets(
            timestamp=timestamp, level="INFO", user_id=str(user.id),
            username=f"@{user.username or 'NoUsername'} ({user.first_name})",
            action=action, details=details, chat_type=chat_type,
            client_number=client_number, success=success
        )

    @staticmethod
    def log_search_result(update: Update, client_number: str, found: bool, fields_count: int = 0):
        result = "SUCCESS" if found else "FAILURE"
        details = f"Cliente: {client_number}, Campos: {fields_count}" if found else f"Cliente: {client_number}, No encontrado"
        EnhancedUserActivityLogger.log_user_action(update, "SEARCH", details, client_number, result)

class GoogleSheetsManager:
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
            if not credentials_json: raise ValueError("Env var GOOGLE_CREDENTIALS_JSON no está configurada.")
            
            credentials_data = json.loads(credentials_json)
            creds = Credentials.from_service_account_info(
                credentials_data, scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
            )
            self.service = build('sheets', 'v4', credentials=creds)
            logger.info("✅ Google Sheets conectado exitosamente.")
        except Exception as e:
            logger.error(f"❌ Falló la autenticación con Google Sheets: {e}")
            self.service = None

    def _find_client_column(self):
        try:
            spreadsheet_id = os.getenv('SPREADSHEET_ID')
            if not spreadsheet_id: raise ValueError("Env var SPREADSHEET_ID no está configurada.")
            
            result = self.service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range='Sheet1!1:1').execute()
            self.headers = result.get('values', [[]])[0]
            
            client_keywords = ['client', 'number', 'id', 'code']
            for i, header in enumerate(self.headers):
                if any(keyword in header.lower().strip() for keyword in client_keywords):
                    self.client_column = i
                    logger.info(f"📋 Columna de cliente encontrada: '{header}' en la posición {i}")
                    return
            logger.info("📋 Usando la primera columna como columna de cliente por defecto.")
        except Exception as e:
            logger.error(f"❌ Error al encontrar la columna de cliente: {e}")

    def get_client_data(self, client_number: str) -> Optional[Dict[str, str]]:
        if not self.service: return None
        try:
            spreadsheet_id = os.getenv('SPREADSHEET_ID')
            result = self.service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range='Sheet1!A:Z').execute()
            values = result.get('values', [])
            if len(values) < 2: return None

            for row in values[1:]:
                if len(row) > self.client_column and str(row[self.client_column]).strip().lower() == str(client_number).strip().lower():
                    logger.info(f"✅ Cliente '{client_number}' encontrado.")
                    return {header: row[i].strip() for i, header in enumerate(self.headers) if i < len(row) and row[i].strip()}
            
            logger.warning(f"❌ Cliente '{client_number}' no encontrado.")
            return None
        except Exception as e:
            logger.error(f"❌ Error al buscar cliente: {e}")
            return None
    
    def get_sheet_info(self) -> Dict[str, Any]:
        if not self.service: return {'total_clients': 0, 'headers': [], 'client_column': 'Desconocido'}
        try:
            spreadsheet_id = os.getenv('SPREADSHEET_ID')
            result = self.service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range='Sheet1!A:A').execute()
            total_rows = len(result.get('values', [])) - 1
            return {
                'total_clients': max(0, total_rows),
                'headers': self.headers,
                'client_column': self.headers[self.client_column] if self.headers else 'Desconocido'
            }
        except Exception as e:
            logger.error(f"Error al obtener info de la hoja: {e}")
            return {'total_clients': 0, 'headers': [], 'client_column': 'Error'}


class TelegramBot:
    def __init__(self):
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not bot_token: raise ValueError("TELEGRAM_BOT_TOKEN no encontrado.")
        
        self.sheets_manager = GoogleSheetsManager()
        self.application = Application.builder().token(bot_token).build()
        self._setup_handlers()
        self.sheet_info = self.sheets_manager.get_sheet_info()

    def _setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("info", self.info_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("whoami", self.whoami_command))
        self.application.add_handler(CommandHandler("logs", self.logs_command))
        self.application.add_handler(CommandHandler("plogs", self.persistent_logs_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    def _is_authorized_user(self, user_id: int) -> bool:
        authorized_users = os.getenv('AUTHORIZED_USERS', '').split(',')
        return str(user_id) in authorized_users if authorized_users != [''] else True

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        EnhancedUserActivityLogger.log_user_action(update, "START_COMMAND")
        
        if update.effective_chat.type == Chat.PRIVATE:
            welcome_message = (
                f"👋 ¡Hola {user.first_name}! Bienvenido a **Client Data Bot**.\n\n"
                f"Envíame un número de cliente y te daré su información.\n\n"
                f"Usa `/help` para ver todos los comandos."
            )
        else:
             welcome_message = (
                f"👋 ¡Hola a todos! Soy **Client Data Bot**.\n\n"
                f"Para buscar un cliente en este grupo, mencióname o responde a uno de mis mensajes.\n"
                f"Ejemplo: `@mi_bot_username 12345`"
            )
        await update.message.reply_text(welcome_message, parse_mode='Markdown')

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        EnhancedUserActivityLogger.log_user_action(update, "HELP_COMMAND")
        help_message = (
            "📖 **Ayuda de Client Data Bot**\n\n"
            "**Buscar clientes:**\n"
            "• **En chat privado:** Simplemente envía el número de cliente.\n"
            "• **En grupos:** Mencióna al bot (`@username_del_bot 12345`) o responde a un mensaje del bot con el número.\n\n"
            "**Comandos disponibles:**\n"
            "• `/start` - Mensaje de bienvenida.\n"
            "• `/help` - Muestra esta ayuda.\n"
            "• `/info` - Muestra información sobre la base de datos.\n"
            "• `/status` - Verifica el estado del bot y la conexión.\n"
            "• `/whoami` - Muestra tu información de Telegram.\n"
            "• `/stats` - Muestra estadísticas de uso (autorizado).\n"
            "• `/plogs` - Muestra los últimos logs de actividad (autorizado)."
        )
        await update.message.reply_text(help_message, parse_mode='Markdown')

    async def info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        EnhancedUserActivityLogger.log_user_action(update, "INFO_COMMAND")
        info = self.sheet_info
        message = (
            f"📋 **Información de la Base de Datos:**\n\n"
            f"📊 **Clientes totales:** {info.get('total_clients', 'N/A')}\n"
            f"🔍 **Columna de búsqueda:** `{info.get('client_column', 'N/A')}`\n\n"
            f"**Campos disponibles (primeros 10):**\n"
        )
        if info.get('headers'):
            for header in info['headers'][:10]:
                message += f"• {header}\n"
        else:
            message += "• No se encontraron campos.\n"
        await update.message.reply_text(message, parse_mode='Markdown')

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        EnhancedUserActivityLogger.log_user_action(update, "STATUS_COMMAND")
        sheets_status = "✅ Conectado" if self.sheets_manager.service else "❌ Desconectado"
        status_message = (
            "🔧 **Estado del Bot:**\n\n"
            f"🤖 **Bot:** ✅ Ejecutándose\n"
            f"📊 **Google Sheets:** {sheets_status}\n"
            f"📋 **Clientes Disponibles:** {self.sheet_info.get('total_clients', 'N/A')}\n"
            f"💬 **Tipo de Chat:** {update.effective_chat.type}\n"
            f"💾 **Logging Persistente:** {'✅ Activo' if persistent_logger.service else '❌ Inactivo'}\n\n"
            f"**Hora de México:** {datetime.now(MEXICO_CITY_TZ).strftime('%Y-%m-%d %H:%M:%S')}"
        )
        await update.message.reply_text(status_message, parse_mode='Markdown')
        
    async def whoami_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        EnhancedUserActivityLogger.log_user_action(update, "WHOAMI_COMMAND")
        user = update.effective_user
        auth_status = "✅ Sí" if self._is_authorized_user(user.id) else "❌ No"
        user_info = (
            f"👤 **Tu Información:**\n\n"
            f"🆔 **User ID:** `{user.id}`\n"
            f"👤 **Nombre:** {user.first_name} {user.last_name or ''}\n"
            f"📱 **Username:** @{user.username or 'No tienes'}\n"
            f"🔐 **Autorizado:** {auth_status}"
        )
        await update.message.reply_text(user_info, parse_mode='Markdown')
        
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        EnhancedUserActivityLogger.log_user_action(update, "STATS_COMMAND")
        if not self._is_authorized_user(update.effective_user.id):
            await update.message.reply_text("⛔ No estás autorizado para ver las estadísticas.")
            return

        stats = persistent_logger.get_stats_from_logs()
        if not stats:
            await update.message.reply_text("No hay estadísticas disponibles.")
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

    async def logs_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Esta función no funcionará en Vercel por el sistema de archivos de solo lectura.
        # Se deja aquí por completitud pero se le informará al usuario.
        EnhancedUserActivityLogger.log_user_action(update, "LOGS_COMMAND")
        if not self._is_authorized_user(update.effective_user.id):
            await update.message.reply_text("⛔ No estás autorizado para ver los logs.")
            return
        await update.message.reply_text("📝 El comando `/logs` no está disponible en este modo de despliegue. Por favor, usa `/plogs` para ver los logs persistentes de Google Sheets.")

    async def persistent_logs_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        EnhancedUserActivityLogger.log_user_action(update, "PLOGS_COMMAND")
        if not self._is_authorized_user(update.effective_user.id):
            await update.message.reply_text("⛔ No estás autorizado para ver los logs persistentes.")
            return
        
        logs = persistent_logger.get_recent_logs()
        if not logs:
            await update.message.reply_text("No se encontraron logs persistentes.")
            return

        log_message = "📝 **Últimos 20 Logs Persistentes:**\n\n```\n"
        for entry in logs:
            # Formato: Timestamp | Acción | Usuario
            log_line = f"{entry[:16]} | {entry:<10} | {entry}\n"
            log_message += log_line
        log_message += "```"
        
        await update.message.reply_text(log_message, parse_mode='Markdown')

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat = update.effective_chat
        message_text_original = update.message.text.strip()
        user = update.effective_user
        
        logger.info(f"📨 Mensaje de {user.first_name} en chat {chat.type}: '{message_text_original}'")
        
        message_to_process = ""
        is_addressed_to_bot = False

        if chat.type == Chat.PRIVATE:
            is_addressed_to_bot = True
            message_to_process = message_text_original
        
        elif chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
            bot_info = await context.bot.get_me()
            bot_username = bot_info.username.lower()

            if f"@{bot_username}" in message_text_original.lower():
                is_addressed_to_bot = True
                message_to_process = message_text_original.lower().replace(f"@{bot_username}", "").strip()
            elif update.message.reply_to_message and update.message.reply_to_message.from_user.id == bot_info.id:
                is_addressed_to_bot = True
                message_to_process = message_text_original
        
        if not is_addressed_to_bot:
            logger.info("Bot no fue mencionado en grupo. Ignorando.")
            return

        client_number = message_to_process
        if not client_number.isdigit():
            logger.warning(f"Formato de número de cliente inválido: '{client_number}'")
            await update.message.reply_text("❌ Por favor, envía solo el número de cliente.", reply_to_message_id=update.message.id)
            return

        await context.bot.send_chat_action(chat_id=chat.id, action="typing")
        client_data = self.sheets_manager.get_client_data(client_number)
        
        if client_data:
            EnhancedUserActivityLogger.log_search_result(update, client_number, True, len(client_data))
            response = f"✅ **Cliente encontrado: `{client_number}`**\n\n"
            
            field_mappings = {
                'client phone number': 'Número 📞',
                'cliente': 'Cliente 🙋🏻‍♀️', 'correo': 'Correo ✉️',
                'other info': 'Otra Información ℹ️'
            }
            for key, value in client_data.items():
                key_lower = key.lower().strip()
                display_key = field_mappings.get(key_lower, key.strip())
                response += f"**{display_key}:** {value}\n"
            
            user_display = f"@{user.username}" if user.username else user.first_name
            response += f"**Buscado por 🙋🏻‍♂️** {user_display}\n"
            
            await update.message.reply_text(response, parse_mode='Markdown', reply_to_message_id=update.message.id)
        else:
            EnhancedUserActivityLogger.log_search_result(update, client_number, False)
            await update.message.reply_text(f"❌ No se encontró cliente con el número `{client_number}`.", parse_mode='Markdown', reply_to_message_id=update.message.id)

# --- Lógica de Inicialización para Vercel ---
async def initialize():
    """Inicializa el bot en la primera solicitud."""
    global application, telegram_bot
    
    logger.info("🚀 Inicializando Bot y Google Sheets...")
    telegram_bot = TelegramBot()
    application = telegram_bot.application # Exponer la aplicación globalmente
    
    if not telegram_bot.sheets_manager.service:
        raise RuntimeError("No se pudo conectar con Google Sheets.")
    
    await application.initialize()
    logger.info("🎉 Bot inicializado exitosamente!")

# --- App de Flask y Webhook ---
app = Flask(__name__)

@app.route('/api/telegram', methods=['POST'])
async def webhook():
    """Endpoint del webhook que recibe los mensajes de Telegram."""
    global application
    
    if not application:
        try:
            await initialize()
        except Exception as e:
            logger.error(f"💥 CRÍTICO: La inicialización del bot falló: {e}")
            return "La inicialización del bot falló", 500

    try:
        update = Update.de_json(request.get_json(force=True), application.bot)
        await application.process_update(update)
        return "ok", 200
    except Exception as e:
        logger.error(f"❌ Error al procesar webhook: {e}")
        return "Error", 500

@app.route('/')
def index():
    status = "✅ Bot inicializado y listo." if application else "⏳ Bot aún no inicializado. Envía un mensaje al bot para activarlo."
    return f"<h1>Estado del Bot</h1><p>{status}</p>"