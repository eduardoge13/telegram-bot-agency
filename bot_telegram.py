import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, date
from dotenv import load_dotenv
from telegram import Update, Chat
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import json
import sys

# Load environment variables
load_dotenv()

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
        
        # Log bot startup
        EnhancedUserActivityLogger.log_system_event("BOT_STARTUP", f"Bot initialized with {self.sheet_info['total_clients']} clients")
    
    def _setup_handlers(self):
        """Setup bot command and message handlers"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("info", self.info_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("groupinfo", self.group_info_command))
        self.application.add_handler(CommandHandler("whoami", self.whoami_command))
        self.application.add_handler(CommandHandler("logs", self.logs_command))
        self.application.add_handler(CommandHandler("plogs", self.persistent_logs_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    def _is_authorized_user(self, user_id: int) -> bool:
        """Check if user is authorized"""
        authorized_users = os.getenv('AUTHORIZED_USERS', '').split(',')
        if authorized_users == ['']:
            return True  # If no specific users set, allow all
        return str(user_id) in authorized_users
    
    def _get_chat_context(self, update: Update) -> str:
        """Get chat context for logging and responses"""
        chat = update.effective_chat
        if chat.type == Chat.PRIVATE:
            return "private chat"
        else:
            return f"group '{chat.title}' (ID: {chat.id})"
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        chat = update.effective_chat
        
        # Log the action
        EnhancedUserActivityLogger.log_user_action(update, "START_COMMAND")
        
        user_name = user.first_name or "there"
        chat_context = self._get_chat_context(update)
        
        if chat.type == Chat.PRIVATE:
            welcome_message = (
                f"👋 Hi {user_name}! Welcome to the **Client Data Bot**!\n\n"
                f"🔍 I can help you find client information from our database.\n"
                f"📊 Currently tracking **{self.sheet_info['total_clients']} clients**\n\n"
                f"**Available commands:**\n"
                f"• `/help` - Show detailed instructions\n"
                f"• `/info` - Show sheet information\n"
                f"• `/status` - Check bot status\n"
                f"• `/whoami` - Get your User ID and info\n\n"
                f"💡 **Quick start:** Just send me any client number and I'll find their data!\n\n"
                f"👥 **For groups:** Add me to a group and I'll work there too!"
            )
        else:
            welcome_message = (
                f"👋 Hi everyone! **Client Data Bot** is now active in this group!\n\n"
                f"🔍 I can help you find client information from our database.\n"
                f"📊 Currently tracking **{self.sheet_info['total_clients']} clients**\n\n"
                f"**Usage in groups:**\n"
                f"• Send client numbers directly: `12345`\n"
                f"• Use commands: `/help`, `/info`, `/status`\n"
                f"• Get group info: `/groupinfo`\n\n"
                f"💡 I'll respond to everyone's queries in this group!"
            )
        
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
        logger.info(f"Start command executed by {user_name} in {chat_context}")
    
    async def whoami_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get user ID and information"""
        user = update.effective_user
        chat = update.effective_chat
        
        # Log the action
        EnhancedUserActivityLogger.log_user_action(update, "WHOAMI_COMMAND")
        
        user_info = (
            f"👤 **Your Telegram Info:**\n\n"
            f"🆔 **User ID:** `{user.id}`\n"
            f"👤 **Name:** {user.first_name} {user.last_name or ''}\n"
            f"📱 **Username:** @{user.username or 'No username'}\n"
            f"💬 **Chat Type:** {chat.type}\n"
            f"🔢 **Chat ID:** `{chat.id}`"
        )
        
        if chat.type != Chat.PRIVATE:
            user_info += f"\n🏷️ **Group:** {chat.title}"
        
        # Check if user is authorized
        is_authorized = self._is_authorized_user(user.id)
        user_info += f"\n🔐 **Authorized:** {'✅ Yes' if is_authorized else '❌ No'}"
        
        user_info += f"\n\n💡 **To authorize this user, add:** `{user.id}` to AUTHORIZED_USERS"
        
        await update.message.reply_text(user_info, parse_mode='Markdown')
        
        # Also print to console for admin
        logger.info(f"👤 User ID Request: {user.first_name} (@{user.username}) = {user.id}")
    
    async def logs_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show recent local logs"""
        user = update.effective_user
        
        # Log the action
        EnhancedUserActivityLogger.log_user_action(update, "LOGS_COMMAND")
        
        # Check if user is authorized
        if not self._is_authorized_user(user.id):
            await update.message.reply_text(
                "⛔ You're not authorized to view bot logs.\n"
                f"💡 Your User ID is: `{user.id}`",
                parse_mode='Markdown'
            )
            return
        
        try:
            # Get recent local activity logs
            recent_logs = self._get_recent_logs(lines=15)
            
            if not recent_logs:
                await update.message.reply_text(
                    "📝 No recent local activity logs found.\n"
                    "💡 Use `/plogs` for persistent logs from Google Sheets."
                )
                return
            
            log_message = (
                f"📝 **Recent Local Logs (Last 15 entries):**\n\n"
                f"```\n{recent_logs}\n```\n\n"
                f"📁 **Note:** Local logs are temporary in Railway\n"
                f"💡 Use `/plogs` for complete persistent history\n"
                f"🕐 **Generated:** {datetime.now().strftime('%H:%M:%S')}"
            )
            
            await update.message.reply_text(log_message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error retrieving local logs: {e}")
            await update.message.reply_text(
                "❌ Error retrieving local logs.\n"
                "💡 Try `/plogs` for persistent logs."
            )
    
    async def persistent_logs_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show persistent logs from Google Sheets"""
        user = update.effective_user
        
        # Log the action
        EnhancedUserActivityLogger.log_user_action(update, "PLOGS_COMMAND")
        
        # Check if user is authorized
        if not self._is_authorized_user(user.id):
            await update.message.reply_text(
                "⛔ You're not authorized to view persistent logs."
            )
            return
        
        try:
            # Get number of entries (default 20)
            args = context.args
            limit = int(args[0]) if args and args[0].isdigit() else 20
            limit = min(limit, 50)  # Max 50 entries
            
            # Get persistent logs
            persistent_logs = persistent_logger.get_recent_logs(limit)
            
            if not persistent_logs:
                await update.message.reply_text(
                    "📊 **No persistent logs found**\n\n"
                    "**Possible reasons:**\n"
                    "• LOGS_SPREADSHEET_ID not configured\n"
                    "• Google Sheets connection issue\n"
                    "• No activity logged yet\n\n"
                    "💡 Check your configuration and try again."
                )
                return
            
            # Format logs for display
            log_message = f"📊 **Persistent Logs (Last {len(persistent_logs)} entries):**\n\n"
            
            for log_entry in persistent_logs[-15:]:  # Show last 15 for readability
                if len(log_entry) >= 5:
                    timestamp = log_entry[0][:16]  # Truncate timestamp
                    action = log_entry[4]
                    username = log_entry[3][:20]  # Truncate username
                    details = log_entry[5][:40] if len(log_entry) > 5 else ""  # Truncate details
                    
                    log_message += f"`{timestamp}` | **{action}** | {username}"
                    if details:
                        log_message += f" | {details}..."
                    log_message += "\n"
            
            log_message += (
                f"\n📋 **Total entries shown:** {len(persistent_logs[-15:])}\n"
                f"📊 **Available in database:** {len(persistent_logs)}\n"
                f"💡 **Usage:** `/plogs 30` to see more entries\n"
                f"🕐 **Generated:** {datetime.now().strftime('%H:%M:%S')}"
            )
            
            await update.message.reply_text(log_message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error retrieving persistent logs: {e}")
            await update.message.reply_text(
                "❌ Error retrieving persistent logs.\n"
                "Check Google Sheets connection and LOGS_SPREADSHEET_ID."
            )
    
    def _get_recent_logs(self, lines: int = 20) -> str:
        """Get recent log entries from local files"""
        try:
            if not os.path.exists('logs/user_activity.log'):
                return "No local activity log file found."
            
            with open('logs/user_activity.log', 'r', encoding='utf-8') as f:
                log_lines = f.readlines()
            
            # Get last N lines
            recent_lines = log_lines[-lines:] if len(log_lines) > lines else log_lines
            
            # Format for display (truncate long lines)
            formatted_lines = []
            for line in recent_lines:
                if len(line) > 100:
                    formatted_lines.append(line[:97] + "...")
                else:
                    formatted_lines.append(line.rstrip())
            
            return '\n'.join(formatted_lines)
            
        except Exception as e:
            logger.error(f"Error reading recent logs: {e}")
            return "❌ Error reading local logs."
            
class PersistentLogger:
    """Store all logs permanently in Google Sheets"""
    
    def __init__(self):
        self.logs_sheet_id = os.getenv('LOGS_SPREADSHEET_ID')
        self.service = None
        self._setup_sheets_service()
    
    def _setup_sheets_service(self):
        """Setup Google Sheets service for logging"""
        try:
            credentials_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
            if credentials_json:
                credentials_data = json.loads(credentials_json)
                creds = Credentials.from_service_account_info(
                    credentials_data, 
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
                self.service = build('sheets', 'v4', credentials=creds)
                print("✅ Persistent logger connected to Google Sheets")
            else:
                print("⚠️ GOOGLE_CREDENTIALS_JSON not found - persistent logging disabled")
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
            print(f"❌ Error reading persistent logs: {e}")
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
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
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
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
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
            
            # Log system event
            EnhancedUserActivityLogger.log_system_event("SHEETS_CONNECTED", "Successfully connected to Google Sheets API")
            
        except json.JSONDecodeError:
            logger.error("❌ Invalid JSON in GOOGLE_CREDENTIALS_JSON")
            raise ValueError("GOOGLE_CREDENTIALS_JSON contains invalid JSON")
        except Exception as e:
            logger.error(f"Error reading recent logs: {e}")
            return f"Error reading logs: {e}"
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show comprehensive bot usage statistics"""
        user = update.effective_user
        
        # Log the action
        EnhancedUserActivityLogger.log_user_action(update, "STATS_COMMAND")
        
        # Check if user is authorized
        if not self._is_authorized_user(user.id):
            await update.message.reply_text(
                "⛔ You're not authorized to view bot statistics."
            )
            return
        
        try:
            # Get stats from persistent logs
            persistent_stats = persistent_logger.get_stats_from_logs()
            
            if not persistent_stats:
                # Fallback to local stats
                local_stats = self._get_local_usage_stats()
                stats_message = (
                    f"📈 **Bot Usage Statistics (Local):**\n\n"
                    f"🔍 **Searches today:** {local_stats.get('searches_today', 0)}\n"
                    f"✅ **Successful:** {local_stats.get('successful_searches', 0)}\n"
                    f"❌ **Failed:** {local_stats.get('failed_searches', 0)}\n"
                    f"👤 **Unique users today:** {local_stats.get('unique_users_today', 0)}\n\n"
                    f"⚠️ **Note:** Local stats only (temporary)\n"
                    f"💡 Configure LOGS_SPREADSHEET_ID for complete history"
                )
            else:
                # Use persistent stats
                stats_message = (
                    f"📈 **Bot Usage Statistics (Complete):**\n\n"
                    f"📊 **Total log entries:** {persistent_stats.get('total_logs', 0)}\n"
                    f"📅 **Today's activity:** {persistent_stats.get('today_logs', 0)}\n\n"
                    f"🔍 **Search Statistics:**\n"
                    f"• Total searches: {persistent_stats.get('total_searches', 0)}\n"
                    f"• ✅ Successful: {persistent_stats.get('successful_searches', 0)}\n"
                    f"• ❌ Failed: {persistent_stats.get('failed_searches', 0)}\n\n"
                    f"👥 **User Activity:**\n"
                    f"• Unique users today: {persistent_stats.get('unique_users_today', 0)}\n"
                    f"• Active groups today: {persistent_stats.get('active_groups_today', 0)}\n\n"
                    f"📊 **Database:** {self.sheet_info['total_clients']} clients available"
                )
            
            stats_message += f"\n🕐 **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            await update.message.reply_text(stats_message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error generating stats: {e}")
            await update.message.reply_text(
                "❌ Error generating statistics. Please try again later."
            )
    
    def _get_local_usage_stats(self) -> Dict[str, int]:
        """Get basic usage statistics from local logs (fallback)"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            if not os.path.exists('logs/user_activity.log'):
                return {}
            
            stats = {
                'searches_today': 0,
                'successful_searches': 0,
                'failed_searches': 0,
                'unique_users_today': set()
            }
            
            with open('logs/user_activity.log', 'r', encoding='utf-8') as f:
                for line in f:
                    if today in line and 'SEARCH' in line:
                        stats['searches_today'] += 1
                        
                        if 'SUCCESS' in line:
                            stats['successful_searches'] += 1
                        elif 'FAILURE' in line:
                            stats['failed_searches'] += 1
                        
                        # Extract user ID (simplified parsing)
                        try:
                            user_id = line.split('ID: ')[1].split(' |')[0]
                            stats['unique_users_today'].add(user_id)
                        except:
                            pass
            
            # Convert set to count
            stats['unique_users_today'] = len(stats['unique_users_today'])
            
            return stats
            
        except Exception as e:
            logger.error(f"Error reading local usage stats: {e}")
            return {}
    
    async def group_info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show information about the current group"""
        chat = update.effective_chat
        user = update.effective_user
        
        # Log the action
        EnhancedUserActivityLogger.log_user_action(update, "GROUP_INFO_COMMAND")
        
        if chat.type == Chat.PRIVATE:
            await update.message.reply_text(
                "ℹ️ This command only works in groups.\n"
                "Add me to a group and try again!",
                parse_mode='Markdown'
            )
            return
        
        # Get group member count (if possible)
        try:
            member_count = await context.bot.get_chat_member_count(chat.id)
        except:
            member_count = "Unknown"
        
        group_message = (
            f"👥 **Group Information:**\n\n"
            f"📝 **Name:** {chat.title}\n"
            f"🆔 **Group ID:** `{chat.id}`\n"
            f"👤 **Members:** {member_count}\n"
            f"🤖 **Bot Status:** Active and ready\n"
            f"📊 **Available Clients:** {self.sheet_info['total_clients']}\n\n"
            f"**Requested by:** {user.first_name} (@{user.username or 'no_username'})"
        )
        
        await update.message.reply_text(group_message, parse_mode='Markdown')
        logger.info(f"Group info requested by {user.first_name} in group {chat.title}")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        chat = update.effective_chat
        
        # Log the action
        EnhancedUserActivityLogger.log_user_action(update, "HELP_COMMAND")
        
        if chat.type == Chat.PRIVATE:
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
                "• `/status` - Check if everything is working\n"
                "• `/whoami` - Get your User ID and info\n"
                "• `/stats` - Show usage statistics (if authorized)\n"
                "• `/logs` - Show recent activity logs (if authorized)\n"
                "• `/plogs` - Show persistent logs from database (if authorized)\n\n"
                "**Group usage:**\n"
                "• Add me to any group and I'll work there too!\n"
                "• Use `/groupinfo` in groups for group-specific information\n\n"
                "**Tips:**\n"
                "• Make sure the client number matches exactly\n"
                "• Try different formats if first attempt fails\n"
                "• Contact admin if you find issues\n\n"
                "❓ **Need help?** Contact your system administrator."
            )
        else:
            help_message = (
                "📖 **How to use this bot in groups:**\n\n"
                "**Finding clients:**\n"
                "• Send any client number: `12345`, `CLIENT-001`, etc.\n"
                "• I'll respond with client information if found\n"
                "• Everyone in the group can use me!\n\n"
                "**Group commands:**\n"
                "• `/help` - This help message\n"
                "• `/info` - Show database information\n"
                "• `/status` - Check bot status\n"
                "• `/groupinfo` - Show group information\n"
                "• `/whoami` - Get your User ID\n\n"
                "**Tips for groups:**\n"
                "• I respond to all members equally\n"
                "• Use me for collaborative client lookup\n"
                "• All interactions are logged for security\n\n"
                "❓ **Questions?** Contact your administrator."
            )
        
        await update.message.reply_text(help_message, parse_mode='Markdown')
    
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
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
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
            f"**System Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        await update.message.reply_text(status_message, parse_mode='Markdown')
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle client number searches"""
        client_number = update.message.text.strip()
        user = update.effective_user
        chat_context = self._get_chat_context(update)
        
        if not client_number:
            await update.message.reply_text(
                "❌ Please send me a client number to search for.\n"
                "Example: `12345` or `CLIENT-001`",
                parse_mode='Markdown'
            )
            return
        
        # Show typing indicator while searching
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        logger.info(f"Search request from {user.first_name} in {chat_context}: '{client_number}'")
        
        try:
            # Search for client
            client_data = self.sheets_manager.get_client_data(client_number)
            
            if client_data:
                # Log successful search
                EnhancedUserActivityLogger.log_search_result(update, client_number, True, len(client_data))
                
                # Format successful response
                response = f"✅ **Client Found: `{client_number}`**\n\n"
                
                # Show data in a nice format
                for key, value in client_data.items():
                    if value and str(value).strip():  # Only show non-empty values
                        # Make key bold and value regular
                        response += f"**{key}:** {value}\n"
                
                # Add helpful footer with context
                if update.effective_chat.type != Chat.PRIVATE:
                    response += f"\n🔍 *Found {len(client_data)} fields | Requested by {user.first_name}*"
                else:
                    response += f"\n🔍 *Found {len(client_data)} fields with data*"
                
                await update.message.reply_text(response, parse_mode='Markdown')
                logger.info(f"✅ Successfully sent data for client: {client_number} to {user.first_name}")
            
            else:
                # Log failed search
                EnhancedUserActivityLogger.log_search_result(update, client_number, False)
                
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
                logger.info(f"❌ Client not found: {client_number} (requested by {user.first_name})")
        
        except Exception as e:
            # Log error
            EnhancedUserActivityLogger.log_user_action(update, "SEARCH_ERROR", f"Client: {client_number}, Error: {str(e)}")
            
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
            logger.error(f"❌ Error processing search for '{client_number}' by {user.first_name}: {e}")
    
    def run(self):
        """Start the bot"""
        try:
            logger.info("🚀 Starting Enhanced Telegram Bot with Persistent Logging...")
            logger.info(f"📊 Ready to serve {self.sheet_info['total_clients']} clients")
            logger.info("👥 Group functionality: ENABLED")
            logger.info("📝 Local logging: ENABLED")
            logger.info(f"💾 Persistent logging: {'ENABLED' if persistent_logger.service else 'DISABLED'}")
            logger.info("✅ Bot is running in polling mode")
            
            # Log bot startup
            EnhancedUserActivityLogger.log_system_event("BOT_STARTED", f"Bot started successfully with {self.sheet_info['total_clients']} clients loaded")
            
            # Start polling
            self.application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True  # Clear old messages on startup
            )
            
        except KeyboardInterrupt:
            logger.info("👋 Bot stopped by user")
            EnhancedUserActivityLogger.log_system_event("BOT_STOPPED", "Bot stopped by user (Ctrl+C)")
        except Exception as e:
            logger.error(f"❌ Bot crashed: {e}")
            EnhancedUserActivityLogger.log_system_event("BOT_CRASHED", f"Bot crashed: {str(e)}")
            raise

def main():
    """Main function"""
    try:
        print("🤖 Enhanced Telegram Client Data Bot with Persistent Logging")
        print("=" * 70)
        print("🔧 Initializing...")
        print("📝 Setting up logging system...")
        print("💾 Connecting to persistent storage...")
        print("👥 Enabling group functionality...")
        
        bot = TelegramBot()
        
        print("✅ Bot initialized successfully!")
        print(f"📊 {bot.sheet_info['total_clients']} clients loaded")
        print("📁 Local logs: ./logs/ directory (temporary in Railway)")
        print(f"💾 Persistent logs: {'Google Sheets ✅' if persistent_logger.service else 'Not configured ❌'}")
        print("👥 Groups supported: YES")
        print("🚀 Starting bot... (Press Ctrl+C to stop)")
        print("=" * 70)
        
        bot.run()
            
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\n🔧 Please check your .env file and make sure all required variables are set.")
        EnhancedUserActivityLogger.log_system_event("STARTUP_ERROR", f"Configuration error: {str(e)}")
    except Exception as e:
        print(f"\n❌ Failed to start bot: {e}")
        print("\n📖 Check the logs above for more details.")
        print("💡 Make sure your Google Sheets credentials and bot token are correct.")
        EnhancedUserActivityLogger.log_system_event("STARTUP_FAILED", f"Startup failed: {str(e)}")

if __name__ == '__main__':
    main()
