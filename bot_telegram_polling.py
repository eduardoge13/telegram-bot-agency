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
from concurrent.futures import ThreadPoolExecutor
import pytz
import re
from typing import Dict, Any, Optional, List, Tuple
from collections import OrderedDict
from datetime import datetime, date
from html import escape as html_escape

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Telegram imports
from telegram import Update, Chat, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import telegram

# Google Sheets imports
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

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
    
    # Reduce noisy HTTP client logs (99% log reduction)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('telegram.ext._updater').setLevel(logging.WARNING)
    
    # Log key runtime versions for diagnostics
    logging.getLogger(__name__).info(
        "Runtime versions -> python-telegram-bot=%s, python=%s",
        getattr(telegram, "__version__", "unknown"),
        sys.version.split()[0]
    )

setup_logging()


def safe_html(text: Optional[str]) -> str:
    """Escape text for use in Telegram HTML parse mode.

    Keeps emojis and basic punctuation intact while escaping HTML special chars.
    """
    if text is None:
        return ''
    return html_escape(str(text))

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
        self.sheets_retry_attempts = int(os.getenv('SHEETS_RETRY_ATTEMPTS', '3'))
        self.sheets_retry_base_delay = float(os.getenv('SHEETS_RETRY_BASE_DELAY', '0.5'))
        # Minimum digits for client number (consistency with TelegramBot)
        self.min_client_digits = int(os.getenv('MIN_CLIENT_NUMBER_LENGTH', '3'))
        self._authenticate()
        # Lock protecting index map and timestamp
        self._index_lock = threading.Lock()
        # Lock protecting row cache accesses
        self._row_cache_lock = threading.Lock()
        # Lock to ensure only one index build runs at a time
        self._index_build_lock = threading.Lock()
        # Flag used by handlers to know if index is warming
        self._index_warming = False
        # Executor for background blocking IO tasks
        self._executor = ThreadPoolExecutor(max_workers=int(os.getenv('SHEETS_THREAD_WORKERS', '4')))
        # Start background refresher thread to keep index warm
        self._start_index_refresher()
        if self.service:
            self._find_client_column()
            # Attempt to load index at startup (best-effort)
            try:
                self.load_index()
            except Exception as e:
                logger.warning(f"⚠️ Could not load index at startup: {e}")

    def _is_retryable_error(self, error: Exception) -> bool:
        if isinstance(error, BrokenPipeError):
            return True
        if isinstance(error, HttpError):
            try:
                status = int(getattr(error.resp, 'status', 0))
                return status in (408, 429, 500, 502, 503, 504)
            except Exception:
                return False
        message = str(error).lower()
        retryable_tokens = (
            'broken pipe',
            'connection reset',
            'connection aborted',
            'temporarily unavailable',
            'timed out',
            'timeout',
            'eof occurred in violation of protocol'
        )
        return any(token in message for token in retryable_tokens)

    def _execute_with_retry(self, request, operation_name: str):
        attempts = max(1, self.sheets_retry_attempts)
        last_error = None
        for attempt in range(1, attempts + 1):
            try:
                return request.execute()
            except Exception as e:
                last_error = e
                if not self._is_retryable_error(e) or attempt == attempts:
                    raise
                delay = self.sheets_retry_base_delay * (2 ** (attempt - 1))
                logger.warning(
                    f"⚠️ {operation_name} failed (attempt {attempt}/{attempts}): {e}. Retrying in {delay:.1f}s"
                )
                time.sleep(delay)
        if last_error:
            raise last_error

    def _schedule_index_rebuild(self, reason: str):
        if self._index_warming:
            return

        self._index_warming = True
        logger.info(f"ℹ️ Scheduling background index rebuild ({reason})")

        def _bg_build():
            try:
                with self._index_build_lock:
                    # Clear row cache before rebuilding index to ensure fresh data
                    with self._row_cache_lock:
                        self.row_cache.clear()
                        logger.debug("🗑️ Row cache cleared before index rebuild")
                    self.load_index()
            except Exception as e:
                logger.warning(f"⚠️ Background index rebuild failed: {e}")
            finally:
                self._index_warming = False

        self._executor.submit(_bg_build)

    def _col_to_letter(self, col_idx: int) -> str:
        n = int(col_idx) + 1
        letters = []
        while n > 0:
            n, remainder = divmod(n - 1, 26)
            letters.append(chr(65 + remainder))
        return ''.join(reversed(letters))

    def _fetch_row_client_data(self, row_num: int) -> Optional[Dict[str, str]]:
        if row_num <= 0:
            return None

        if row_num in self.row_cache:
            with self._row_cache_lock:
                entry = self.row_cache.pop(row_num)
                self.row_cache[row_num] = entry
            return entry

        max_col_idx = max(3, len(self.headers) - 1) if self.headers else 3
        end_col = self._col_to_letter(max_col_idx)
        rng = f"Sheet1!A{row_num}:{end_col}{row_num}"
        result = self._execute_with_retry(
            self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=rng
            ),
            f"fetch row {row_num}"
        )
        values = result.get('values', [])
        if not values:
            return None

        row = values[0]
        headers = self.headers if self.headers else ['client phone number', 'cliente', 'correo', 'other info']
        client_data = {}
        for i, hdr in enumerate(headers):
            client_data[hdr] = row[i].strip() if i < len(row) and row[i] is not None else ''

        with self._row_cache_lock:
            self.row_cache[row_num] = client_data
            while len(self.row_cache) > self.row_cache_size:
                self.row_cache.popitem(last=False)

        return client_data

    def _start_index_refresher(self):
        def refresher():
            while True:
                try:
                    time.sleep(max(10, self.index_ttl))
                    if self.service and self.spreadsheet_id:
                        logger.debug('Index refresher: refreshing lightweight index')
                        self._schedule_index_rebuild('periodic refresher')
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
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
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
        try:
            if not self.service or not self.spreadsheet_id:
                logger.warning("⚠️ Cannot load index: Sheets service or spreadsheet ID missing")
                return

            # Read full header row to keep response mapping aligned with sheet structure
            header_result = self._execute_with_retry(
                self.service.spreadsheets().values().get(
                    spreadsheetId=self.spreadsheet_id,
                    range='Sheet1!1:1'
                ),
                'read sheet headers for index'
            )
            headers = header_result.get('values', [[]])[0]
            if not headers:
                logger.warning("⚠️ No headers found when loading index")
                return
            self.headers = headers

            cache_path = f"/tmp/sheets_index_rows_{self.spreadsheet_id}.json"
            try:
                if os.path.exists(cache_path):
                    with open(cache_path, 'r', encoding='utf-8') as f:
                        cached = json.load(f)
                    ts = cached.get('_ts', 0)
                    if time.time() - ts < self.index_ttl:
                        with self._index_lock:
                            self.index_phone_to_row = cached.get('index', {})
                            self.index_timestamp = ts
                        logger.info(f"✅ Loaded lightweight index from cache with {len(self.index_phone_to_row)} entries")
                        return
            except Exception:
                logger.debug("No valid lightweight cache available, will rebuild index")

            try:
                col_idx = self.client_column if hasattr(self, 'client_column') and self.client_column is not None else 0
                if col_idx < 0:
                    col_idx = 0
                column_letter = self._col_to_letter(int(col_idx))
            except Exception:
                column_letter = 'A'

            result = self._execute_with_retry(
                self.service.spreadsheets().values().get(
                    spreadsheetId=self.spreadsheet_id,
                    range=f'Sheet1!{column_letter}2:{column_letter}'
                ),
                f"read phone column {column_letter}"
            )

            phones = result.get('values', [])
            index_map: Dict[str, int] = {}
            for i, row in enumerate(phones, start=2):
                raw_phone = row[0] if row and len(row) > 0 else ''
                normalized = self._normalize_phone(raw_phone)
                if normalized:
                    index_map[normalized] = i

            with self._index_lock:
                self.index_phone_to_row = index_map
                self.index_timestamp = time.time()

            try:
                with open(cache_path, 'w', encoding='utf-8') as f:
                    json.dump({'_ts': self.index_timestamp, 'index': self.index_phone_to_row}, f)
                logger.info(f"✅ Lightweight index built with {len(self.index_phone_to_row)} entries (cached)")
            except Exception:
                logger.info(f"✅ Lightweight index built with {len(self.index_phone_to_row)} entries")
        except Exception as e:
            logger.warning(f"⚠️ load_index failed: {e}")

    def _ensure_index(self):
        now = time.time()
        # Only trigger a synchronous reload if index is empty; otherwise rely on
        # background refresher to keep it warm to avoid blocking request handlers.
        try:
            with self._index_lock:
                empty = not bool(self.index_phone_to_row)
                stale = (now - self.index_timestamp) > self.index_ttl

            if empty:
                # Do NOT block request handlers by rebuilding the entire index
                # synchronously. Instead, schedule a background index build the
                # first time we notice the index is empty. Handlers can check
                # `self._index_warming` to provide a friendly message to users
                # while the index is being built.
                self._schedule_index_rebuild('index empty')
                # Return without blocking; callers should handle the None response
                return
            elif stale:
                self._schedule_index_rebuild('index stale')
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
                return self._fetch_row_client_data(row_num)

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
                        return self._fetch_row_client_data(row_num)
            except Exception:
                logger.debug("Suffix matching fallback failed; will rebuild index if needed")

            # Fallback: avoid blocking synchronous rebuilds during request handling.
            # Schedule a background index rebuild and return None immediately so
            # the handler can respond quickly. The background build will refresh
            # the lightweight index for subsequent requests.
            try:
                if not self.service:
                    return None

                self._schedule_index_rebuild('client not found')

                logger.info(f"❌ Client '{client_number}' not found; background rebuild scheduled")
                return None
            except Exception as e:
                logger.error(f"❌ Error scheduling fallback index rebuild: {e}")
                return None
        except Exception as e:
            logger.error(f"❌ Error searching for client: {e}")
            return None

    async def get_client_data_async(self, client_number: str) -> Optional[Dict[str, str]]:
        """Async wrapper that runs the blocking get_client_data in an executor."""
        try:
            loop = asyncio.get_running_loop()
            # Use the manager's dedicated executor to avoid overloading the default
            return await loop.run_in_executor(self._executor, self.get_client_data, client_number)
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

    def update_field(self, client_number: str, field_name: str, new_value: str) -> tuple[bool, str]:
        """Update any field for a specific client

        Returns:
            tuple[bool, str]: (success, error_message)
        """
        try:
            if not self.service or not self.spreadsheet_id:
                error_msg = "Servicio de Sheets no disponible"
                logger.error(f"❌ Cannot update field: Sheets service or spreadsheet ID missing")
                return False, error_msg

            # Find the row number for the client
            self._ensure_index()
            normalized = self._normalize_phone(client_number)
            if not normalized:
                error_msg = "No se pudo normalizar el número de teléfono"
                return False, error_msg

            with self._index_lock:
                row_num = self.index_phone_to_row.get(normalized)

            if not row_num:
                error_msg = f"Cliente {client_number} no encontrado"
                logger.error(f"❌ Client {client_number} not found in index")
                return False, error_msg

            # Find the field column index
            field_column_idx = None
            field_name_lower = field_name.lower().strip()
            logger.info(f"🔍 Searching for field '{field_name}' in headers: {self.headers}")

            # First try exact match (case-insensitive)
            for i, header in enumerate(self.headers):
                if header.lower().strip() == field_name_lower:
                    field_column_idx = i
                    logger.info(f"✅ Found exact match at index {i}: '{header}'")
                    break

            # If no exact match, try partial match
            if field_column_idx is None:
                for i, header in enumerate(self.headers):
                    header_lower = header.lower().strip()
                    if field_name_lower in header_lower or header_lower in field_name_lower:
                        field_column_idx = i
                        logger.info(f"✅ Found partial match at index {i}: '{header}'")
                        break

            if field_column_idx is None:
                error_msg = f"Campo '{field_name}' no encontrado. Columnas disponibles: {', '.join(self.headers)}"
                logger.error(f"❌ Field '{field_name}' not found in headers: {self.headers}")
                return False, error_msg

            # Update the cell
            column_letter = self._col_to_letter(field_column_idx)
            cell_range = f"Sheet1!{column_letter}{row_num}"

            self._execute_with_retry(
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=cell_range,
                    valueInputOption='RAW',
                    body={'values': [[new_value]]}
                ),
                f"update {field_name} for client {client_number}"
            )

            # Clear row cache for this client to force refresh
            with self._row_cache_lock:
                if row_num in self.row_cache:
                    del self.row_cache[row_num]
                    logger.debug(f"🗑️ Cleared cache for row {row_num}")

            logger.info(f"✅ Successfully updated {field_name} for client {client_number} to {new_value}")
            return True, ""

        except Exception as e:
            error_msg = f"Error al actualizar: {str(e)}"
            logger.error(f"❌ Error updating {field_name} for client {client_number}: {e}")
            return False, error_msg

    async def update_field_async(self, client_number: str, field_name: str, new_value: str) -> tuple[bool, str]:
        """Async wrapper for update_field

        Returns:
            tuple[bool, str]: (success, error_message)
        """
        try:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(self._executor, self.update_field, client_number, field_name, new_value)
        except Exception as e:
            error_msg = f"Error en operación asíncrona: {str(e)}"
            logger.error(f"❌ Async update_field error: {e}")
            return False, error_msg

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
        self._recent_messages_lock = threading.Lock()
        self.dedupe_window = int(os.getenv('DEDUP_WINDOW_SECONDS', '30'))
        # Minimum length for a recognized client number (in digits)
        self.min_client_digits = int(os.getenv('MIN_CLIENT_NUMBER_LENGTH', '3'))

        # Pending notifications to avoid duplicate follow-ups: (chat_id, client_number)
        self._pending_notifications = set()

        # Edit conversation tracking: chat_id -> {'client_number': str, 'field_name': str}
        self._edit_conversations: Dict[int, Dict[str, str]] = {}
        self._edit_conversations_lock = threading.Lock()

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

    def _is_direct_group_phone_candidate(self, raw_text: str) -> bool:
        """Validate whether a group message looks like a standalone phone number.

        Accept only digits with common separators and enforce realistic length
        to avoid accidental triggers on casual group messages.
        """
        if not raw_text:
            return False

        text = raw_text.strip()
        # Only allow digits and common phone separators when using direct mode
        if not re.fullmatch(r"[\d\s\-\(\)\+]+", text):
            return False

        digits = ''.join(ch for ch in text if ch.isdigit())
        min_digits = int(os.getenv('MIN_GROUP_DIRECT_DIGITS', '10'))
        max_digits = int(os.getenv('MAX_GROUP_DIRECT_DIGITS', '15'))
        return min_digits <= len(digits) <= max_digits

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
                    if ent.type == 'text_mention':
                        mentioned_user = getattr(ent, 'user', None)
                        if mentioned_user and self.bot_info and getattr(mentioned_user, 'id', None) == getattr(self.bot_info, 'id', None):
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

            # Optional direct-number mode for groups: if the whole message looks
            # like a client number, process it even without mention/reply.
            try:
                allow_direct_group = os.getenv('ALLOW_DIRECT_GROUP_NUMBER', 'true').lower() in ('1', 'true', 'yes')
                raw_text = (message.text or message.caption or "").strip() if message is not None else ""
                if allow_direct_group and self._is_direct_group_phone_candidate(raw_text):
                    return True, raw_text
            except Exception:
                logger.debug("Direct-number detection in group failed")

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
                    f"👋 ¡Hola {safe_html(getattr(user, 'first_name', ''))}! Bienvenido a <b>Client Data Bot</b>.\n\n"
                    "Envíame un número de cliente y te daré su información.\n\n"
                    "Usa /help para ver todos los comandos."
                )
            else:
                msg = (
                    f"👋 ¡Hola a todos! Soy <b>Client Data Bot</b>.\n\n"
                    "Para buscar un cliente en este grupo, mencióname o responde a uno de mis mensajes.\n"
                    "Ejemplo: @mi_bot_username 12345"
                )
            
            try:
                await getattr(update, 'message', None).reply_text(msg, parse_mode='HTML')
            except Exception:
                # Best-effort: send via context.bot
                try:
                    await context.bot.send_message(chat_id=update.effective_chat.id, text=msg, parse_mode='HTML')
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
            "📖 <b>Ayuda de Client Data Bot</b>\n\n"
            "<b>Buscar clientes:</b>\n"
            "• <b>En chat privado:</b> Simplemente envía el número de cliente.\n"
            "• <b>En grupos:</b> Menciona al bot (ej. <code>@username_del_bot 12345</code>) o responde a un mensaje del bot con el número.\n\n"
            "<b>Comandos disponibles:</b>\n"
            "• <code>/start</code> - Mensaje de bienvenida.\n"
            "• <code>/help</code> - Muestra esta ayuda.\n"
            "• <code>/info</code> - Muestra información sobre la base de datos.\n"
            "• <code>/status</code> - Verifica el estado del bot y la conexión.\n"
            "• <code>/whoami</code> - Muestra tu información de Telegram.\n"
            "• <code>/stats</code> - Muestra estadísticas de uso (autorizado).\n"
            "• <code>/plogs</code> - Muestra los últimos logs de actividad (autorizado)."
        )
        # Send help as HTML (static content already safe)
        try:
            await update.message.reply_text(help_message, parse_mode='HTML')
        except Exception:
            try:
                await context.bot.send_message(chat_id=getattr(update.effective_chat, 'id', None), text=help_message, parse_mode='HTML')
            except Exception:
                logger.debug('Failed to send help message')
    
    async def info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show spreadsheet information"""
        # Log the action
        EnhancedUserActivityLogger.log_user_action(update, "INFO_COMMAND")
        
        info = self.sheet_info
        
        message = (
            "📋 <b>Spreadsheet Information:</b>\n\n"
            f"📊 <b>Total clients:</b> {safe_html(info.get('total_clients', '0'))}\n"
            f"🔍 <b>Search column:</b> {safe_html(info.get('client_column', 'Unknown'))}\n\n"
            f"<b>Available fields:</b>\n"
        )
        
        if info['headers']:
            for i, header in enumerate(info['headers'][:10], 1):  # Show first 10 headers
                message += f"• {safe_html(header)}\n"
            
            if len(info['headers']) > 10:
                message += f"• ... and {safe_html(str(len(info['headers']) - 10))} more fields\n"
        else:
            message += "• No headers found\n"
        
        message += f"\n💡 Send any client number to search!"
        try:
            await update.message.reply_text(message, parse_mode='HTML')
        except Exception:
            try:
                await context.bot.send_message(chat_id=getattr(update.effective_chat, 'id', None), text=message, parse_mode='HTML')
            except Exception:
                logger.debug('Failed to send info message')
    
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
            "🔍 <b>Bot Status:</b>\n\n"
            f"🤖 <b>Bot:</b> ✅ Running\n"
            f"📊 <b>Google Sheets:</b> {safe_html(sheets_status)}\n"
            f"📝 <b>Persistent Logs:</b> {safe_html(logs_status)}\n"
            f"📋 <b>Total clients:</b> {safe_html(str(self.sheet_info.get('total_clients', 'Unknown')))}\n\n"
            f"🚀 <b>Ready to search!</b>"
        )
        try:
            await update.message.reply_text(status_message, parse_mode='HTML')
        except Exception:
            try:
                await context.bot.send_message(chat_id=getattr(update.effective_chat, 'id', None), text=status_message, parse_mode='HTML')
            except Exception:
                logger.debug('Failed to send status message')
    
    async def whoami_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user information"""
        EnhancedUserActivityLogger.log_user_action(update, "WHOAMI_COMMAND")
        
        user = update.effective_user
        auth_status = "✅ Sí" if self._is_authorized_user(getattr(user, 'id', None)) else "❌ No"

        safe_user_info = (
            f"👤 <b>Tu Información:</b>\n\n"
            f"🆔 <b>User ID:</b> <code>{safe_html(getattr(user, 'id', ''))}</code>\n"
            f"👤 <b>Nombre:</b> {safe_html(getattr(user, 'first_name', ''))} {safe_html(getattr(user, 'last_name', '') or '')}\n"
            f"📱 <b>Username:</b> @{safe_html(getattr(user, 'username', 'No tienes'))}\n"
            f"🔑 <b>Autorizado:</b> {safe_html(auth_status)}"
        )

        try:
            await update.message.reply_text(safe_user_info, parse_mode='HTML')
        except Exception:
            try:
                await context.bot.send_message(chat_id=getattr(update.effective_chat, 'id', None), text=safe_user_info, parse_mode='HTML')
            except Exception:
                logger.debug('Failed to send whoami message')
    
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
            "📈 <b>Estadísticas de Uso:</b>\n\n"
            f"📊 <b>Logs totales:</b> {safe_html(str(stats.get('total_logs', 0)))}\n"
            f"📅 <b>Actividad de hoy:</b> {safe_html(str(stats.get('today_logs', 0)))}\n\n"
            f"🔍 <b>Búsquedas Totales:</b> {safe_html(str(stats.get('total_searches', 0)))}\n"
            f"  - ✅ <b>Exitosas:</b> {safe_html(str(stats.get('successful_searches', 0)))}\n"
            f"  - ❌ <b>Fallidas:</b> {safe_html(str(stats.get('failed_searches', 0)))}\n\n"
            f"👥 <b>Actividad de Hoy:</b>\n"
            f"  - <b>Usuarios únicos:</b> {safe_html(str(stats.get('unique_users_today', 0)))}\n"
            f"  - <b>Grupos activos:</b> {safe_html(str(stats.get('active_groups_today', 0)))}"
        )

        try:
            await update.message.reply_text(stats_message, parse_mode='HTML')
        except Exception:
            try:
                await context.bot.send_message(chat_id=getattr(update.effective_chat, 'id', None), text=stats_message, parse_mode='HTML')
            except Exception:
                logger.debug('Failed to send stats message')
    
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
        
        log_message = "📝 Últimos 20 Logs Persistentes:\n\n"
        for entry in logs:
            if isinstance(entry, list) and len(entry) >= 5:
                log_message += f"{safe_html(entry[0])} | {safe_html(entry[1])} | {safe_html(entry[4])}\n"

        # logs displayed as preformatted text — escape and wrap in <pre>
        safe_logs = '<pre>' + html_escape(log_message) + '</pre>'
        try:
            await update.message.reply_text(safe_logs, parse_mode='HTML')
        except Exception:
            try:
                await context.bot.send_message(chat_id=getattr(update.effective_chat, 'id', None), text=log_message)
            except Exception:
                logger.debug('Failed to send persistent logs')
    
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

            if not is_addressed_to_bot:
                return

            # Check if we're in an edit conversation first
            chat_id = getattr(chat, 'id', None)
            if chat_id:
                with self._edit_conversations_lock:
                    in_edit_conversation = chat_id in self._edit_conversations

                if in_edit_conversation:
                    # Route to edit input handler
                    await self.handle_edit_input(update, context)
                    return

            logger.info("Processing message from %s in %s: '%s'", user.first_name if user else 'Unknown', chat.type if chat else 'Unknown', (message_to_process or raw_text))

            # Deduplication: avoid processing the same user+chat+text repeatedly within a short window
            try:
                dedupe_text = message_to_process or raw_text
                key = f"{chat.id}:{user.id}:{dedupe_text}"
                now_ts = time.time()
                with self._recent_messages_lock:
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
                
                # Build an HTML-safe response with new format
                field_mappings = {
                    'client phone number': 'Número 📞',
                    'cliente': 'Cliente 🙋🏻‍♀️',
                    'correo': 'Correo ✉️',
                    'other info': 'Otra Información ℹ️'
                }

                parts = []
                parts.append("✅ <b>Cliente encontrado</b>")
                parts.append("")

                for key, value in client_data.items():
                    display_key = field_mappings.get(key.lower().strip(), key.strip())
                    parts.append(f"{safe_html(display_key)}: {safe_html(value)}")

                user_display = f"@{getattr(user, 'username', '')}" if getattr(user, 'username', None) else safe_html(getattr(user, 'first_name', ''))
                parts.append("")
                parts.append(f"Buscado por: {safe_html(user_display)}")

                response_html = "\n".join(parts)

                # Add edit button
                keyboard = [[InlineKeyboardButton("✏️ Editar campo", callback_data=f"edit_{client_number}")]]
                reply_markup = InlineKeyboardMarkup(keyboard)

                try:
                    await update.message.reply_text(
                        response_html,
                        reply_to_message_id=getattr(update.message, 'message_id', None),
                        parse_mode='HTML',
                        reply_markup=reply_markup
                    )
                except Exception:
                    try:
                        await context.bot.send_message(
                            chat_id=getattr(update.effective_chat, 'id', None),
                            text=response_html,
                            parse_mode='HTML',
                            reply_markup=reply_markup
                        )
                    except Exception:
                        logger.debug('Failed to send search response')
            else:
                # If a background rebuild was scheduled by the sheets manager,
                # tell the user we scheduled an index refresh and set up a
                # follow-up notification that will re-query once the index
                # finishes warming (or times out).
                try:
                    if getattr(self.sheets_manager, '_index_warming', False):
                        chat_id = getattr(update.effective_chat, 'id', None)
                        reply_to_id = getattr(update.message, 'message_id', None)
                        try:
                            await update.message.reply_text(
                                f"🔄 No se encontró información para <code>{safe_html(client_number)}</code>. He programado una actualización del índice en segundo plano y te avisaré cuando termine.",
                                reply_to_message_id=reply_to_id,
                                parse_mode='HTML'
                            )
                        except Exception:
                            try:
                                await context.bot.send_message(chat_id=chat_id, text=f"🔄 No se encontró información para {safe_html(client_number)}. He programado una actualización del índice en segundo plano y te avisaré cuando termine.")
                            except Exception:
                                logger.debug('Failed to notify user that index is warming')

                        # Schedule a follow-up task that will re-run the lookup after
                        # the index build completes (with debounce via _pending_notifications)
                        try:
                            if chat_id is not None:
                                # Fire-and-forget; the coroutine handles its own exceptions
                                asyncio.create_task(self._followup_after_rebuild(chat_id, reply_to_id, client_number, context.bot))
                        except Exception:
                            logger.debug('Failed to schedule followup after rebuild')

                        return
                except Exception:
                    pass
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
                    await update.message.reply_text(f"❌ No se encontró información para el cliente: <code>{safe_html(client_number)}</code>", reply_to_message_id=getattr(update.message, 'message_id', None), parse_mode='HTML')
                except Exception:
                    try:
                        await context.bot.send_message(chat_id=getattr(update.effective_chat, 'id', None), text=f"❌ No se encontró información para el cliente: {safe_html(client_number)}", parse_mode='HTML')
                    except Exception:
                        logger.debug('Failed to send not-found message')
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            try:
                await update.message.reply_text("❌ Error interno procesando el mensaje.")
            except:
                pass

    async def handle_edit_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard callback for edit field"""
        query = update.callback_query
        await query.answer()

        try:
            chat_id = update.effective_chat.id
            user = update.effective_user

            logger.info(f"📝 Callback received: {query.data}")

            if query.data.startswith("edit_"):
                # User clicked "Edit field" button - show field selection
                client_number = query.data.split("_", 1)[1]

                EnhancedUserActivityLogger.log_user_action(update, "EDIT_START", f"Client: {client_number}")

                # Get available editable fields from sheet headers (skip phone number column)
                headers = self.sheets_manager.headers if self.sheets_manager.headers else []
                keyboard = []

                field_icons = {
                    'banco': '🏦',
                    'bank': '🏦',
                    'correo': '✉️',
                    'email': '✉️',
                    'other info': 'ℹ️',
                    'cliente': '👤',
                    'client': '👤'
                }

                for idx, header in enumerate(headers):
                    # Skip phone number column (usually first column)
                    if idx == 0:
                        continue

                    header_lower = header.lower().strip()
                    icon = field_icons.get(header_lower, '📝')
                    button_text = f"{icon} {header}"

                    keyboard.append([InlineKeyboardButton(button_text, callback_data=f"field_{idx}_{client_number}")])

                keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="edit_cancel")])
                reply_markup = InlineKeyboardMarkup(keyboard)

                await query.edit_message_text(
                    f"¿Qué campo deseas editar para el cliente <code>{safe_html(client_number)}</code>?",
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )

            elif query.data.startswith("field_"):
                # User selected a field to edit
                parts = query.data.split("_", 2)
                field_idx = int(parts[1])
                client_number = parts[2]

                # Get the actual field name from headers
                headers = self.sheets_manager.headers if self.sheets_manager.headers else []
                if field_idx < len(headers):
                    field_name = headers[field_idx]
                else:
                    await query.edit_message_text("❌ Error: campo no válido")
                    return

                # Store conversation state
                with self._edit_conversations_lock:
                    self._edit_conversations[chat_id] = {
                        'client_number': client_number,
                        'field_name': field_name
                    }

                await query.edit_message_text(
                    f"✏️ Por favor, envía el nuevo valor para <b>{safe_html(field_name)}</b> del cliente <code>{safe_html(client_number)}</code>:",
                    parse_mode='HTML'
                )

            elif query.data == "edit_cancel":
                # User cancelled edit
                with self._edit_conversations_lock:
                    if chat_id in self._edit_conversations:
                        del self._edit_conversations[chat_id]

                EnhancedUserActivityLogger.log_user_action(update, "EDIT_CANCELLED", "User cancelled edit")
                await query.edit_message_text("✅ Edición cancelada.")

        except Exception as e:
            logger.error(f"❌ Error handling edit callback: {e}", exc_info=True)
            try:
                await query.edit_message_text(f"❌ Error procesando la solicitud: {str(e)}")
            except Exception as e2:
                logger.error(f"Failed to send error message: {e2}")

    async def handle_edit_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle field value input when in edit conversation state"""
        try:
            chat_id = update.effective_chat.id
            user = update.effective_user
            message_text = (update.message.text or "").strip()

            with self._edit_conversations_lock:
                if chat_id not in self._edit_conversations:
                    # Not in an edit conversation, ignore
                    return

                conv_data = self._edit_conversations[chat_id]
                client_number = conv_data.get('client_number')
                field_name = conv_data.get('field_name')

            if not message_text:
                await update.message.reply_text("❌ Por favor, envía un valor válido.")
                return

            # Update the field
            await update.message.reply_text("🔄 Actualizando campo en Google Sheets...")

            success, error_message = await self.sheets_manager.update_field_async(client_number, field_name, message_text)

            if success:
                EnhancedUserActivityLogger.log_user_action(
                    update,
                    "FIELD_UPDATED",
                    f"Client: {client_number}, Field: {field_name}, Value: {message_text}",
                    client_number=client_number,
                    success="SUCCESS"
                )
                await update.message.reply_text(
                    f"✅ <b>Campo actualizado exitosamente</b>\n\n"
                    f"Cliente: <code>{safe_html(client_number)}</code>\n"
                    f"Campo: <b>{safe_html(field_name)}</b>\n"
                    f"Nuevo valor: {safe_html(message_text)}",
                    parse_mode='HTML'
                )
            else:
                EnhancedUserActivityLogger.log_user_action(
                    update,
                    "FIELD_UPDATE_FAILED",
                    f"Client: {client_number}, Field: {field_name}, Error: {error_message}",
                    client_number=client_number,
                    success="FAILURE"
                )
                await update.message.reply_text(
                    f"❌ <b>No pude actualizar el campo</b>\n\n"
                    f"<b>Error:</b> {safe_html(error_message)}",
                    parse_mode='HTML'
                )

            # Clean up conversation state
            with self._edit_conversations_lock:
                if chat_id in self._edit_conversations:
                    del self._edit_conversations[chat_id]

        except Exception as e:
            logger.error(f"Error handling edit input: {e}")
            try:
                await update.message.reply_text("❌ Error procesando el valor del campo.")
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

        # Callback query handler for inline keyboard buttons
        self.application.add_handler(CallbackQueryHandler(self.handle_edit_callback))

        # More efficient message handling
        # 1. Private chats (any text)
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, self.handle_message)
        )
        # 2. Group messages are routed through a single handler and then gated by
        # _addressed_and_processed_text (mention/reply/direct-number mode).
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS, self.handle_message)
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

    async def _followup_after_rebuild(self, chat_id: int, reply_to_message_id: Optional[int], client_number: str, bot, timeout: int = 30):
        """Wait for the background index rebuild to complete (or timeout), re-run the lookup and notify the user.

        This prevents spamming multiple follow-ups for the same chat+client by
        using `self._pending_notifications` as a debounce set.
        """
        key = (chat_id, client_number)
        if key in self._pending_notifications:
            return
        self._pending_notifications.add(key)

        try:
            waited = 0
            interval = 1
            # Wait until index warming finishes or timeout
            while getattr(self.sheets_manager, '_index_warming', False) and waited < timeout:
                await asyncio.sleep(interval)
                waited += interval

            # After waiting (either finished or timed out), re-run lookup
            try:
                client_data = await self.sheets_manager.get_client_data_async(client_number)
            except Exception as e:
                logger.debug(f'Followup lookup failed for {client_number}: {e}')
                client_data = None

            if client_data:
                # Build response same as in main handler
                field_mappings = {
                    'client phone number': 'Número 📞',
                    'cliente': 'Cliente 🙋🏻‍♀️',
                    'correo': 'Correo ✉️',
                    'other info': 'Otra Información ℹ️'
                }
                
                parts = []
                parts.append("✅ <b>Cliente encontrado</b>")
                parts.append("")
                for key_name, value in client_data.items():
                    display_key = field_mappings.get(key_name.lower().strip(), key_name.strip())
                    parts.append(f"{safe_html(display_key)}: {safe_html(value)}")
                response_html = "\n".join(parts)

                # Add edit button
                keyboard = [[InlineKeyboardButton("✏️ Editar campo", callback_data=f"edit_{client_number}")]]
                reply_markup = InlineKeyboardMarkup(keyboard)

                try:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=response_html,
                        parse_mode='HTML',
                        reply_to_message_id=reply_to_message_id,
                        reply_markup=reply_markup
                    )
                except Exception:
                    try:
                        await bot.send_message(chat_id=chat_id, text="✅ Cliente encontrado")
                    except Exception:
                        logger.debug('Failed to send followup found message')
            else:
                # Notify that index updated (or timed out) and nothing found
                try:
                    await bot.send_message(chat_id=chat_id, text=f"🔎 Índice actualizado: no se encontró información para el cliente: <code>{safe_html(client_number)}</code>", parse_mode='HTML', reply_to_message_id=reply_to_message_id)
                except Exception:
                    try:
                        await bot.send_message(chat_id=chat_id, text=f"🔎 Índice actualizado: no se encontró información para el cliente: {safe_html(client_number)}")
                    except Exception:
                        logger.debug('Failed to send followup not-found message')

        finally:
            try:
                self._pending_notifications.discard(key)
            except Exception:
                pass