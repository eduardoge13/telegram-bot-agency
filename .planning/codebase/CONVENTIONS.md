# Coding Conventions

**Analysis Date:** 2026-03-13

## Naming Patterns

**Files:**
- `snake_case.py` — all Python source files use snake_case (e.g., `bot_telegram_polling.py`, `main.py`)
- Test files prefixed with `test_` (e.g., `tests/test_index_manager.py`, `tests/test_message_parsing.py`)

**Functions/Methods:**
- `snake_case` for all function and method names
- Private methods prefixed with `_` (e.g., `_normalize_phone`, `_execute_with_retry`, `_fetch_row_client_data`, `_schedule_index_rebuild`)
- Async handlers suffixed with descriptive action verb (e.g., `start_command`, `handle_message`, `handle_edit_callback`)
- Background/internal helpers prefixed with `_bg_` inside closures (e.g., `_bg_build`)

**Variables:**
- `snake_case` throughout
- Constants in `UPPER_SNAKE_CASE` (e.g., `MEXICO_CITY_TZ`)
- Boolean flags named as `is_` or `_warming` (e.g., `is_addressed_to_bot`, `_index_warming`)

**Classes:**
- `PascalCase` (e.g., `TelegramBot`, `GoogleSheetsManager`, `PersistentLogger`, `EnhancedUserActivityLogger`)
- Dummy/stub test classes prefixed with `Dummy` (e.g., `DummyRequest`, `DummyValuesApi`, `DummyService`)

**Type Annotations:**
- Used consistently on all public and private methods
- From `typing`: `Dict`, `Any`, `Optional`, `List`, `Tuple`
- Return types declared on all methods:
  ```python
  def get_client_data(self, client_number: str) -> Optional[Dict[str, str]]:
  def update_field(self, client_number: str, field_name: str, new_value: str) -> tuple[bool, str]:
  async def get_client_data_async(self, client_number: str) -> Optional[Dict[str, str]]:
  ```

## Code Style

**Formatting:**
- No formatter config found (no `.prettierrc`, `pyproject.toml`, or `setup.cfg`)
- 4-space indentation used throughout
- Lines kept under ~120 chars; long strings broken with implicit concatenation inside `()`
- F-strings used consistently for logging and message construction

**Linting:**
- No linter config detected (no `.flake8`, `.pylintrc`, or `pyproject.toml`)
- Code follows PEP 8 naming but is not enforced by tooling

## Import Organization

**Order (observed):**
1. Standard library imports (`os`, `logging`, `asyncio`, `sys`, `json`, `time`, `threading`, `re`, `typing`, etc.)
2. Third-party imports (`pytz`, `telegram`, `google.oauth2`, `googleapiclient`, `flask`)
3. Local/internal imports not applicable (single-module project)

**Pattern:**
```python
import os
import logging
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from collections import OrderedDict
from telegram import Update, Chat, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ...
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
```

**Conditional Imports:**
- Optional dependencies wrapped in `try/except ImportError` blocks:
  ```python
  try:
      from dotenv import load_dotenv
      load_dotenv()
  except ImportError:
      pass
  ```
- Late imports inside functions for heavyweight or conditional SDKs:
  ```python
  def get_secret(...):
      from google.cloud import secretmanager
  ```

## Error Handling

**Strategy:**
- Broad `except Exception as e` used throughout — no granular exception hierarchies
- Internal errors always logged before returning a safe fallback or re-raising
- Critical operations return `(bool, str)` tuples for success/error message:
  ```python
  def update_field(self, ...) -> tuple[bool, str]:
      ...
      return False, error_msg  # on failure
      return True, ""          # on success
  ```
- Network/IO methods return `None` on failure (not raised)
- All Telegram message sends wrapped in nested `try/except` with a best-effort fallback:
  ```python
  try:
      await update.message.reply_text(msg, parse_mode='HTML')
  except Exception:
      try:
          await context.bot.send_message(...)
      except Exception:
          logger.debug('Failed to send ...')
  ```

**Retryable Errors:**
- `_is_retryable_error()` in `GoogleSheetsManager` centralizes retry logic; checks `BrokenPipeError`, `HttpError` status codes (408, 429, 500–504), and connection-related string tokens
- `_execute_with_retry()` implements exponential backoff: `delay = base_delay * (2 ** (attempt - 1))`

## Logging

**Framework:** Python stdlib `logging`

**Setup:**
- `setup_logging()` called at module import time in `bot_telegram_polling.py`
- Log level controllable via `DEBUG=1|true|yes` env var (defaults to `INFO`)
- Format: `[%(asctime)s] %(levelname)s | %(name)s | %(message)s`
- All loggers via `logger = logging.getLogger(__name__)` at module level
- HTTP client noise suppressed: `httpx`, `httpcore`, `urllib3`, `telegram.ext._updater` set to `WARNING`

**Conventions:**
- Emoji prefixes used in log messages to visually distinguish context:
  - `✅` — success
  - `❌` — error/failure
  - `⚠️` — warning/degraded state
  - `🔧` — init/setup steps
  - `📋`, `📊`, `🔍` — informational
- `logger.info()` for operational events
- `logger.warning()` for recoverable degraded states
- `logger.error()` for failures (with `f"❌ ..."` prefix)
- `logger.debug()` for verbose diagnostics and non-critical failures
- `logger.exception()` used in `main.py` when full stack trace is needed at fatal error

**Persistent Logging:**
- `PersistentLogger` additionally writes to Google Sheets (fire-and-forget via daemon thread)
- `EnhancedUserActivityLogger.log_user_action()` is the standard call for all Telegram handler activity

## Comments

**When to Comment:**
- Block comments before logical sections within long functions
- Inline comments on non-obvious design decisions (threading locks, async patterns, fallback strategy)
- Docstrings on most public methods; minimal/absent on private helpers:
  ```python
  def safe_html(text: Optional[str]) -> str:
      """Escape text for use in Telegram HTML parse mode.

      Keeps emojis and basic punctuation intact while escaping HTML special chars.
      """
  ```

**Docstring style:**
- PEP 257 short description, sometimes with `Returns:` section
- Not using NumPy or Google docstring format consistently — plain prose used

## Function Design

**Size:** Functions are large; `handle_message()` spans ~200 lines. No enforced size limit.

**Parameters:**
- Keyword arguments with defaults for optional fields:
  ```python
  def log_to_sheets(self, timestamp, level, user_id, ..., chat_type: str = "", client_number: str = "", success: str = ""):
  ```
- `Optional[str]` used for parameters that can be `None`

**Return Values:**
- Async handlers return `None` (Telegram convention)
- Data accessors return `Optional[Dict[str, str]]`
- Mutation methods return `tuple[bool, str]`

## Module Design

**Exports:** No `__all__` defined; module is not intended as a library

**Structure:** Single large module `bot_telegram_polling.py` (~1750 lines) containing all classes:
- `PersistentLogger` — Google Sheets audit log writer
- `EnhancedUserActivityLogger` — static methods for structured event logging
- `GoogleSheetsManager` — all Sheets I/O and caching
- `TelegramBot` — all Telegram handlers, command routing, and bot lifecycle

**Separation concern:** `main.py` handles Flask health server and process lifecycle; `bot_telegram_polling.py` contains all domain logic.

---

*Convention analysis: 2026-03-13*
