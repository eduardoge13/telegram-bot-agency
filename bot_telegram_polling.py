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
import threading
import asyncio
import pytz
import re
from typing import Dict, Any, Optional, List, Tuple
from collections import OrderedDict
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
    # Allow enabling DEBUG via environment variable DEBUG=1 or DEBUG=true
    log_level = logging.INFO
    debug_env = os.getenv('DEBUG', '').lower()
    if debug_env in ('1', 'true', 'yes'):
        log_level = logging.DEBUG

    logging.basicConfig(
        level=log_level,
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

    def log_to_sheets_async(self, *args, **kwargs):
        # Fire-and-forget wrapper to avoid blocking handlers
        try:
            t = threading.Thread(target=self.log_to_sheets, args=args, kwargs=kwargs, daemon=True)
            t.start()
        except Exception:
            logger.debug('Failed to start persistent logging thread')
    
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
            logger.error(f"❌ Error al leer logs persistentes: {e}")
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
        user = getattr(update, 'effective_user', None)
        chat = getattr(update, 'effective_chat', None)
        timestamp = datetime.now(MEXICO_CITY_TZ).strftime('%Y-%m-%d %H:%M:%S')

        # Determine chat type safely
        chat_type = "Private" if getattr(chat, 'type', None) == Chat.PRIVATE else f"Group ({getattr(chat, 'title', '')})"

        # Safe user fields
        uname = getattr(user, 'username', None) or 'NoUsername'
        first = getattr(user, 'first_name', '')
        last = getattr(user, 'last_name', '')
        uid = getattr(user, 'id', 'unknown')

        # Create log message for local logging
        log_msg = (
            f"USER: @{uname} ({first} {last or ''}) | ID: {uid} | CHAT: {chat_type} | ACTION: {action}"
        )

        if details:
            log_msg += f" | DETAILS: {details}"

        if client_number:
            log_msg += f" | CLIENT: {client_number}"

        if success:
            log_msg += f" | RESULT: {success}"

        # Log locally
        logger.info(log_msg)

        # Log persistently to Google Sheets (safe user fields)
        try:
            persistent_logger.log_to_sheets(
                timestamp=timestamp,
                level="INFO",
                user_id=str(uid),
                username=f"@{uname} ({first})",
                action=action,
                details=details,
                chat_type=chat_type,
                client_number=client_number,
                success=success
            )
        except Exception:
            logger.debug("Failed to write persistent log; continuing")
    
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
        # In-memory index: normalized_client_number -> row dict
        # Lightweight index: phone -> row number (int)
        self.index_phone_to_row: Dict[str, int] = {}
        self.index_timestamp = 0
        self.index_ttl = int(os.getenv('INDEX_TTL_SECONDS', '600'))  # default 10 minutes
        # Row cache (LRU) to avoid re-reading frequently used rows
        self.row_cache: OrderedDict = OrderedDict()
        # Default row cache reduced for small-memory Cloud Run instances (512Mi)
        self.row_cache_size = int(os.getenv('ROW_CACHE_SIZE', '200'))
        # Minimum digits for client number (consistency with TelegramBot)
        self.min_client_digits = int(os.getenv('MIN_CLIENT_NUMBER_LENGTH', '3'))
        self._authenticate()
        # Lock protecting index map and timestamp
        self._index_lock = threading.Lock()
        # Lock protecting row cache accesses
        self._row_cache_lock = threading.Lock()
        # Start background refresher thread to keep index warm
        self._start_index_refresher()
        if self.service:
            self._find_client_column()
            # Attempt to load index at startup (best-effort)
            try:
                self.load_index()
            except Exception as e:
                logger.warning(f"⚠️ Could not load index at startup: {e}")

    def _start_index_refresher(self):
        def refresher():
            while True:
                try:
                    time.sleep(max(10, self.index_ttl))
                    if self.service and self.spreadsheet_id:
                        logger.debug('Index refresher: refreshing lightweight index')
                        try:
                            self.load_index()
                        except Exception as e:
                            logger.debug(f'Index refresher error: {e}')
                except Exception:
                    # keep loop alive
                    time.sleep(5)

        t = threading.Thread(target=refresher, daemon=True)
        t.start()
    
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
            if not self.spreadsheet_id:
                logger.warning("⚠️ SPREADSHEET_ID not set. Skipping client column discovery.")
                return
            if not self.service:
                logger.warning("⚠️ Sheets service not available. Skipping client column discovery.")
                return
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

    def _normalize_phone(self, raw: str) -> str:
        if not raw:
            return ""
        # Keep only digits, remove leading zeros optionally
        digits = ''.join(ch for ch in str(raw) if ch.isdigit())
        return digits.lstrip('0') if digits else ''

    def load_index(self):
        """Load an in-memory index mapping normalized phone -> row dict.

        This reads the sheet once and builds a dictionary for O(1) lookups.
        """
        if not self.service or not self.spreadsheet_id:
            logger.warning("⚠️ Cannot load index: Sheets service or spreadsheet ID missing")
            return

        # Read header row to get column names (assume simple 4-column sheet A:D)
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range='Sheet1!A1:D1'
        ).execute()
        headers = result.get('values', [[]])[0]
        if not headers:
            logger.warning("⚠️ No headers found when loading index")
            return

        # For large sheets, avoid loading full rows into memory.
        # We'll build a lightweight index: normalized_phone -> row_number
        cache_path = f"/tmp/sheets_index_rows_{self.spreadsheet_id}.json"
        try:
            if os.path.exists(cache_path):
                with open(cache_path, 'r', encoding='utf-8') as f:
                    cached = json.load(f)
                ts = cached.get('_ts', 0)
                if time.time() - ts < self.index_ttl:
                    # load phone->row mapping
                    with self._index_lock:
                        self.index_phone_to_row = cached.get('index', {})
                        self.index_timestamp = ts
                    logger.info(f"✅ Loaded lightweight index from cache with {len(self.index_phone_to_row)} entries")
                    return
        except Exception:
            logger.debug("No valid lightweight cache available, will rebuild index")

        # Determine which column to use for phones (default to A)
        try:
            col_idx = self.client_column if hasattr(self, 'client_column') and self.client_column is not None else 0
            # clamp
            if col_idx < 0:
                col_idx = 0
            column_letter = chr(ord('A') + int(col_idx))
        except Exception:
            column_letter = 'A'

        # Read only the detected column (phones) to minimize payload
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f'Sheet1!{column_letter}2:{column_letter}'
            ).execute()
        except Exception as e:
            logger.error(f"❌ Error reading phone column '{column_letter}': {e}")
            return

        phones = result.get('values', [])
        index_map: Dict[str, int] = {}
        # Phones correspond to rows starting at 2
        for i, row in enumerate(phones, start=2):
            raw_phone = row[0] if row and len(row) > 0 else ''
            normalized = self._normalize_phone(raw_phone)
            if normalized:
                index_map[normalized] = i

        with self._index_lock:
            self.index_phone_to_row = index_map
            self.index_timestamp = time.time()

        # persist cache
        try:
            try:
                with open(cache_path, 'w', encoding='utf-8') as f:
                    json.dump({'_ts': self.index_timestamp, 'index': self.index_phone_to_row}, f)
            except Exception:
                pass
            logger.info(f"✅ Lightweight index built with {len(self.index_phone_to_row)} entries (cached)")
        except Exception:
            logger.info(f"✅ Lightweight index built with {len(self.index_phone_to_row)} entries")

    def _ensure_index(self):
        now = time.time()
        # Only trigger a synchronous reload if index is empty; otherwise rely on
        # background refresher to keep it warm to avoid blocking request handlers.
        try:
            with self._index_lock:
                empty = not bool(self.index_phone_to_row)
                stale = (now - self.index_timestamp) > self.index_ttl

            if empty:
                # synchronous build required
                self.load_index()
            elif stale:
                # let background refresher update soon; don't block
                logger.debug('Index is stale; background refresher will update it')
        except Exception as e:
            logger.warning(f"⚠️ Failed to check/refresh index: {e}")
    
    def get_client_data(self, client_number: str) -> Optional[Dict[str, str]]:
        # Lightweight index lookup -> then fetch single row and cache it (LRU)
        try:
            self._ensure_index()
            normalized = self._normalize_phone(client_number)
            if not normalized:
                return None
            with self._index_lock:
                row_num = self.index_phone_to_row.get(normalized)
            if row_num:
                # check row cache
                if row_num in self.row_cache:
                    # move to end (recent)
                    with self._row_cache_lock:
                        entry = self.row_cache.pop(row_num)
                        self.row_cache[row_num] = entry
                    return entry

                # fetch only the single row A:D
                rng = f"Sheet1!A{row_num}:D{row_num}"
                result = self.service.spreadsheets().values().get(
                    spreadsheetId=self.spreadsheet_id,
                    range=rng
                ).execute()
                values = result.get('values', [])
                if not values:
                    return None
                row = values[0]
                client_data = {}
                # ensure headers exist
                for i, hdr in enumerate(self.headers[:4]):
                    client_data[hdr] = row[i].strip() if i < len(row) and row[i] is not None else ''

                # update LRU cache
                with self._row_cache_lock:
                    self.row_cache[row_num] = client_data
                    # evict if oversized
                    while len(self.row_cache) > self.row_cache_size:
                        self.row_cache.popitem(last=False)

                return client_data

            # Fallback: attempt suffix matching before rebuilding the index.
            # This helps when sheet stores numbers with country code or extra prefixes.
            try:
                with self._index_lock:
                    idx_copy = dict(self.index_phone_to_row)
                if idx_copy:
                    # find best suffix match (longest match)
                    best_match_row = None
                    best_match_len = 0
                    for k, rn in idx_copy.items():
                        if k.endswith(normalized) and len(normalized) <= len(k):
                            match_len = len(normalized)
                            if match_len > best_match_len:
                                best_match_len = match_len
                                best_match_row = rn

                    if best_match_row:
                        row_num = best_match_row
            except Exception:
                logger.debug("Suffix matching fallback failed; will rebuild index if needed")

            # Fallback: rebuild the lightweight index and re-attempt lookup once.
            # This is safer than scanning and avoids recursive calls / repeated scans.
            try:
                if not self.service:
                    return None

                logger.info("ℹ️ Client not found in index — rebuilding index and retrying (sync)")
                # Rebuild index synchronously here (this call may be slow for very large sheets)
                self.load_index()
                with self._index_lock:
                    row_num = self.index_phone_to_row.get(normalized)
                if not row_num:
                    logger.info(f"❌ Client '{client_number}' not found after rebuilding index")
                    return None

                # If index now contains the row number, fetch the single row A:D
                rng = f"Sheet1!A{row_num}:D{row_num}"
                result = self.service.spreadsheets().values().get(
                    spreadsheetId=self.spreadsheet_id,
                    range=rng
                ).execute()
                values = result.get('values', [])
                if not values:
                    return None
                row = values[0]
                client_data = {}
                for i, hdr in enumerate(self.headers[:4]):
                    client_data[hdr] = row[i].strip() if i < len(row) and row[i] is not None else ''

                # update LRU cache
                with self._row_cache_lock:
                    self.row_cache[row_num] = client_data
                    while len(self.row_cache) > self.row_cache_size:
                        self.row_cache.popitem(last=False)

                return client_data
            except Exception as e:
                logger.error(f"❌ Error during fallback index rebuild: {e}")
                return None
        except Exception as e:
            logger.error(f"❌ Error searching for client: {e}")
            return None

    async def get_client_data_async(self, client_number: str) -> Optional[Dict[str, str]]:
        """Async wrapper that runs the blocking get_client_data in an executor."""
        try:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, self.get_client_data, client_number)
        except Exception as e:
            logger.error(f"❌ Async get_client_data error: {e}")
            return None
    
    def get_sheet_info(self) -> Dict[str, Any]:
        try:
            if not self.spreadsheet_id:
                logger.warning("⚠️ SPREADSHEET_ID not set. Returning empty sheet info.")
                return {'total_clients': 0, 'headers': [], 'client_column': 'Unknown'}
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
        # Prefer an explicit env var (convenient for dev deploys). Fall back to Secret Manager.
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.token:
            logger.info("🔧 TELEGRAM_BOT_TOKEN env var not set, fetching from Secret Manager 'telegram-bot-token'...")
            self.token = get_secret(project_id, 'telegram-bot-token')
        if not self.token:
            logger.error("❌ Telegram bot token not provided (env or secret)")
            raise ValueError("❌ Telegram bot token not provided (env or secret)")
        
        logger.info("🔧 Token retrieved successfully, initializing Google Sheets manager...")
        self.sheets_manager = GoogleSheetsManager()
        self.sheet_info = self.sheets_manager.get_sheet_info()
        # Defensive: always bind an instance-level _normalize_phone callable so
        # message handlers (which may be running concurrently) cannot see a
        # missing attribute if the class-level method is replaced or shadowed.
        if hasattr(self.sheets_manager, '_normalize_phone'):
            # Delegate to sheets manager implementation
            self._normalize_phone = self.sheets_manager._normalize_phone
        else:
            # Fallback simple normalizer
            def _fallback_normalize(raw: str) -> str:
                if not raw:
                    return ''
                digits = ''.join(ch for ch in str(raw) if ch.isdigit())
                return digits.lstrip('0') if digits else ''

            self._normalize_phone = _fallback_normalize
        self.application = None
        self.bot_info = None  # To cache bot info
        # In-memory deduplication store to avoid processing duplicate messages
        self.recent_messages: Dict[str, float] = {}
        self.dedupe_window = int(os.getenv('DEDUP_WINDOW_SECONDS', '30'))
        # Minimum length for a recognized client number (in digits)
        self.min_client_digits = int(os.getenv('MIN_CLIENT_NUMBER_LENGTH', '3'))

        logger.info("✅ Bot initialized successfully")

    def _normalize_phone(self, raw: str) -> str:
        """Delegate normalization to sheets manager if available, otherwise fallback."""
        try:
            if hasattr(self, 'sheets_manager') and self.sheets_manager and hasattr(self.sheets_manager, '_normalize_phone'):
                return self.sheets_manager._normalize_phone(raw)
        except Exception:
            pass

        # Fallback normalization
        if not raw:
            return ''
        digits = ''.join(ch for ch in str(raw) if ch.isdigit())
        return digits.lstrip('0') if digits else ''

    def _get_normalize_fn(self):
        """Return a callable normalization function bound to the instance with fallbacks."""
        fn = getattr(self, '_normalize_phone', None)
        if callable(fn):
            return fn
        if hasattr(self, 'sheets_manager') and hasattr(self.sheets_manager, '_normalize_phone'):
            return self.sheets_manager._normalize_phone

        def _local_fallback(raw: str) -> str:
            if not raw:
                return ''
            digits = ''.join(ch for ch in str(raw) if ch.isdigit())
            return digits.lstrip('0') if digits else ''

        return _local_fallback

    async def _ensure_bot_info(self, context: ContextTypes.DEFAULT_TYPE):
        """Ensure self.bot_info is populated (best-effort)."""
        if self.bot_info:
            return
        try:
            self.bot_info = await context.bot.get_me()
        except Exception:
            logger.debug("Could not fetch bot info via get_me()")

    def _is_mentioned_in_message(self, message) -> bool:
        """Check entities and caption_entities for a mention of the bot username.

        Note: this requires `self.bot_info` to be set (username available).
        """
        if not message or not self.bot_info or not getattr(self.bot_info, 'username', None):
            return False

        bot_username = self.bot_info.username.lower()

        entities_sources = []
        if getattr(message, 'entities', None):
            entities_sources.append((message.entities, message.text or ""))
        if getattr(message, 'caption_entities', None):
            entities_sources.append((message.caption_entities, message.caption or ""))

        for ents, text in entities_sources:
            try:
                for ent in ents:
                    if ent.type == 'mention':
                        start, end = ent.offset, ent.offset + ent.length
                        mention_text = text[start:end]
                        if mention_text.lower() == f"@{bot_username}":
                            return True
            except Exception:
                continue

        # Fallback: raw text contains @username
        raw = (message.text or message.caption or "").lower()
        return f"@{bot_username}" in raw

    def _extract_client_number(self, text: str) -> str:
        if not text:
            return ""
        matches = re.findall(r"(\d+)", text)
        for m in matches:
            if len(m) >= self.min_client_digits:
                return m
        return ""

    async def _addressed_and_processed_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> Tuple[bool, str]:
        """Return (is_addressed, processed_text).

        Handles private chats, mentions (via entities), and replies to bot messages.
        """
        chat = update.effective_chat
        message = update.message

        # Private chat: always addressed
        if chat and chat.type == Chat.PRIVATE:
            raw_text = (message.text or message.caption) if message is not None else ""
            return True, (raw_text or "").strip()

        # Group chat: detect mention or replies
        if chat and chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
            await self._ensure_bot_info(context)

            # Mention via entities/caption_entities
            try:
                if self._is_mentioned_in_message(message):
                    processed = (message.text or message.caption or "")
                    if self.bot_info and getattr(self.bot_info, 'username', None):
                        processed = re.sub(fr"@{re.escape(self.bot_info.username)}", "", processed, flags=re.IGNORECASE)
                    return True, processed.strip()
            except Exception:
                logger.debug("Mention detection failed")

            # Reply to a bot message
            try:
                if message and getattr(message, 'reply_to_message', None) and getattr(message.reply_to_message, 'from_user', None) and self.bot_info and getattr(message.reply_to_message.from_user, 'id', None) == self.bot_info.id:
                    raw_text = (message.text or message.caption or "")
                    return True, (raw_text or "").strip()
            except Exception:
                logger.debug("Reply detection failed")

        return False, ""
    
    def _is_authorized_user(self, user_id: int) -> bool:
        authorized_users = os.getenv('AUTHORIZED_USERS', '').split(',')
        return str(user_id) in authorized_users if authorized_users != [''] else True
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            user = getattr(update, 'effective_user', None)
            
            # Log the action
            EnhancedUserActivityLogger.log_user_action(update, "START_COMMAND")
            
            if getattr(update, 'effective_chat', None) and getattr(update.effective_chat, 'type', None) == Chat.PRIVATE:
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
            
            try:
                await getattr(update, 'message', None).reply_text(msg, parse_mode='Markdown')
            except Exception:
                # Best-effort: send via context.bot
                try:
                    await context.bot.send_message(chat_id=update.effective_chat.id, text=msg, parse_mode='Markdown')
                except Exception:
                    logger.debug('Failed to send start message')
        except Exception as e:
            logger.error(f"Error in start_command: {e}")
            try:
                await getattr(update, 'message', None).reply_text("❌ Error interno del bot.")
            except Exception:
                try:
                    await context.bot.send_message(chat_id=getattr(update.effective_chat, 'id', None), text="❌ Error interno del bot.")
                except Exception:
                    logger.debug('Failed to notify user of internal error')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        chat = update.effective_chat
        
        # Log the action
        EnhancedUserActivityLogger.log_user_action(update, "HELP_COMMAND")
        
        help_message = (
            "📖 **Ayuda de Client Data Bot**\n\n"
            "**Buscar clientes:**\n"
            "• **En chat privado:** Simplemente envía el número de cliente.\n"
            "• **En grupos:** Menciona al bot (`@username_del_bot 12345`) o responde a un mensaje del bot con el número.\n\n"
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
            sheets_status = "❌ Disconnected"
        
        # Test persistent logging
        try:
            persistent_logger.get_recent_logs(limit=1)
            logs_status = "✅ Working"
        except:
            logs_status = "❌ Error"
        
        status_message = (
            "🔍 **Bot Status:**\n\n"
            f"🤖 **Bot:** ✅ Running\n"
            f"📊 **Google Sheets:** {sheets_status}\n"
            f"📝 **Persistent Logs:** {logs_status}\n"
            f"📋 **Total clients:** {self.sheet_info.get('total_clients', 'Unknown')}\n\n"
            f"🚀 **Ready to search!**"
        )
        
        await update.message.reply_text(status_message, parse_mode='Markdown')
    
    async def whoami_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user information"""
        EnhancedUserActivityLogger.log_user_action(update, "WHOAMI_COMMAND")
        
        user = update.effective_user
        auth_status = "✅ Sí" if self._is_authorized_user(user.id) else "❌ No"
        
        user_info = (
            f"👤 **Tu Información:**\n\n"
            f"🆔 **User ID:** `{user.id}`\n"
            f"👤 **Nombre:** {user.first_name} {user.last_name or ''}\n"
            f"📱 **Username:** @{user.username or 'No tienes'}\n"
            f"🔑 **Autorizado:** {auth_status}"
        )
        
        await update.message.reply_text(user_info, parse_mode='Markdown')
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show usage statistics (authorized users only)"""
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
    
    async def persistent_logs_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show recent persistent logs (authorized users only)"""
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
            if isinstance(entry, list) and len(entry) >= 5:
                log_message += f"{entry[0]:<16} | {entry[1]:<15} | {entry[4]}\n"
        log_message += "```"
        
        await update.message.reply_text(log_message, parse_mode='Markdown')
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            # Runtime defensive guard: ensure instance has a callable _normalize_phone.
            # Some runtimes/handler dispatching paths may execute handlers on objects
            # where instance attributes weren't bound as expected; ensure a safe
            # fallback is available to avoid AttributeError and allow graceful replies.
            if not hasattr(self, '_normalize_phone') or not callable(getattr(self, '_normalize_phone', None)):
                logger.warning("⚠️ _normalize_phone missing on TelegramBot instance; binding fallback normalizer")
                def _runtime_fallback(raw: str) -> str:
                    if not raw:
                        return ''
                    digits = ''.join(ch for ch in str(raw) if ch.isdigit())
                    return digits.lstrip('0') if digits else ''
                self._normalize_phone = _runtime_fallback

            chat = update.effective_chat
            user = update.effective_user
            # Use helper to determine if message is addressed and get processed text
            is_addressed_to_bot, message_to_process = await self._addressed_and_processed_text(update, context)

            # Raw message text for logging/dedupe fallback
            raw_text = ""
            if update.message is not None:
                raw_text = update.message.text or update.message.caption or ""

            logger.info("Processing message from %s in %s: '%s'", user.first_name if user else 'Unknown', chat.type if chat else 'Unknown', (message_to_process or raw_text))

            if not is_addressed_to_bot:
                return

            # Deduplication: avoid processing the same user+chat+text repeatedly within a short window
            try:
                dedupe_text = message_to_process or raw_text
                key = f"{chat.id}:{user.id}:{dedupe_text}"
                now_ts = time.time()
                # Clean old entries opportunistically
                self.recent_messages = {k: v for k, v in self.recent_messages.items() if now_ts - v < self.dedupe_window}
                if key in self.recent_messages and now_ts - self.recent_messages[key] < self.dedupe_window:
                    logger.info("Ignoring duplicate message from %s in chat %s", user.id, chat.id)
                    return
                self.recent_messages[key] = now_ts
            except Exception:
                logger.debug("Dedupe check failed, continuing")

            # Extract client number
            # Log original and attempt extraction for debugging
            original_text_for_log = message_to_process or raw_text
            logger.debug("Message original: %s", original_text_for_log)
            extracted_raw = self._extract_client_number(message_to_process)
            # Resolve normalization function safely via helper
            normalize_fn = self._get_normalize_fn()
            normalized_for_search = normalize_fn(extracted_raw)
            logger.debug("Extracted number: %s | Normalized for search: %s", extracted_raw, normalized_for_search)

            # Use normalized number for searching; keep extracted_raw for display if needed
            client_number = normalized_for_search

            if not client_number:
                # Only reply if the bot was directly addressed but no number was found
                bot_username = getattr(self.bot_info, 'username', '') if self.bot_info else ''
                message_text = (message_to_process or raw_text or "")
                if (chat and getattr(chat, 'type', None) == Chat.PRIVATE) or (bot_username and f"@{bot_username.lower()}" in message_text.lower()):
                    try:
                        await update.message.reply_text(
                            "❌ Por favor, envía un número de cliente válido.",
                            reply_to_message_id=getattr(update.message, 'message_id', None)
                        )
                    except Exception:
                        try:
                            await context.bot.send_message(chat_id=getattr(update.effective_chat, 'id', None), text="❌ Por favor, envía un número de cliente válido.")
                        except Exception:
                            logger.debug('Failed to notify user about missing client number')
                return
            
            # Search for client data (async to avoid blocking event loop)
            client_data = await self.sheets_manager.get_client_data_async(client_number)
            
            if client_data:
                # Log successful search (user-facing persistent log)
                # Non-blocking persistent log
                try:
                    persistent_logger.log_to_sheets_async(
                        timestamp=datetime.now(MEXICO_CITY_TZ).strftime('%Y-%m-%d %H:%M:%S'),
                        level="INFO",
                        user_id=str(getattr(user, 'id', 'unknown')),
                        username=f"@{getattr(user, 'username', '')}",
                        action="SEARCH",
                        details=f"Client: {client_number}, Fields: {len(client_data)}",
                        chat_type=getattr(chat, 'type', ''),
                        client_number=client_number,
                        success="SUCCESS"
                    )
                except Exception:
                    logger.debug('Failed to enqueue persistent log')
                
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
                
                # Send as plain text to avoid Markdown parsing errors when fields contain
                # characters that could break entity parsing.
                try:
                    # Send as plain text (no Markdown) to avoid entity parsing errors
                    await update.message.reply_text(response, reply_to_message_id=getattr(update.message, 'message_id', None), parse_mode=None)
                except Exception:
                    try:
                        await context.bot.send_message(chat_id=getattr(update.effective_chat, 'id', None), text=response, parse_mode=None)
                    except Exception:
                        logger.debug('Failed to send search response')
            else:
                # Log failed search async
                try:
                    persistent_logger.log_to_sheets_async(
                        timestamp=datetime.now(MEXICO_CITY_TZ).strftime('%Y-%m-%d %H:%M:%S'),
                        level="INFO",
                        user_id=str(getattr(user, 'id', 'unknown')),
                        username=f"@{getattr(user, 'username', '')}",
                        action="SEARCH",
                        details=f"Client: {client_number}, Not found (normalized: {normalized_for_search})",
                        chat_type=getattr(chat, 'type', ''),
                        client_number=client_number,
                        success="FAILURE"
                    )
                except Exception:
                    logger.debug('Failed to enqueue persistent failure log')

                # Plain-text reply for failure
                try:
                    await update.message.reply_text(f"❌ No se encontró información para el cliente: {client_number}", reply_to_message_id=getattr(update.message, 'message_id', None), parse_mode=None)
                except Exception:
                    try:
                        await context.bot.send_message(chat_id=getattr(update.effective_chat, 'id', None), text=f"❌ No se encontró información para el cliente: {client_number}", parse_mode=None)
                    except Exception:
                        logger.debug('Failed to send not-found message')
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            try:
                await update.message.reply_text("❌ Error interno procesando el mensaje.")
            except:
                pass
    
    def setup_handlers(self):
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("info", self.info_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("whoami", self.whoami_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("plogs", self.persistent_logs_command))
        
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