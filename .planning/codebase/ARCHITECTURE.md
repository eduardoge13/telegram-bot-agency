# Architecture

**Analysis Date:** 2026-03-13

## Pattern Overview

**Overall:** Monolithic single-process bot with layered class decomposition

**Key Characteristics:**
- All logic lives in two files: `bot_telegram_polling.py` (core bot) and `main.py` (process entrypoint)
- Event-driven: Telegram polling drives all user interactions via python-telegram-bot's `Application` dispatcher
- Mixed async/sync execution: Telegram handlers are `async`; Google Sheets API calls are blocking and offloaded to a `ThreadPoolExecutor`
- Google Sheets is the sole data store — no database, no ORM, no local persistence beyond an in-memory index and a `/tmp` cache file

## Layers

**Process/Health Layer:**
- Purpose: Bootstrap process, serve Cloud Run health check endpoint, manage graceful shutdown
- Location: `main.py`
- Contains: Flask app for `/` and `/health` routes, signal handlers, thread management
- Depends on: `bot_telegram_polling.TelegramBot`
- Used by: Cloud Run container runtime (Docker `CMD ["python", "main.py"]`)

**Bot Application Layer:**
- Purpose: Handle all Telegram interactions — command routing, message parsing, conversation state, inline keyboard flows
- Location: `bot_telegram_polling.py` — class `TelegramBot` (lines 842–1765)
- Contains: Command handlers (`start_command`, `help_command`, `info_command`, `status_command`, `whoami_command`, `stats_command`, `persistent_logs_command`), message handler (`handle_message`), inline keyboard callback handler (`handle_edit_callback`), edit conversation handler (`handle_edit_input`), `setup_handlers()`, `run()`
- Depends on: `GoogleSheetsManager`, `PersistentLogger`, `EnhancedUserActivityLogger`
- Used by: `main.py` via `TelegramBot().run()`

**Data Access Layer:**
- Purpose: Manage all reads and writes to the primary Google Sheets client database
- Location: `bot_telegram_polling.py` — class `GoogleSheetsManager` (lines 338–840)
- Contains: Authentication (`_authenticate`), schema discovery (`_find_client_column`), in-memory phone index with LRU row cache, background index refresher thread, retry logic (`_execute_with_retry`), async wrappers (`get_client_data_async`, `update_field_async`)
- Depends on: `google-api-python-client`, `google-cloud-secret-manager`, `ThreadPoolExecutor`
- Used by: `TelegramBot`

**Logging Layer:**
- Purpose: Dual-path logging — local stdout and persistent audit trail in a separate Google Sheets log spreadsheet
- Location: `bot_telegram_polling.py` — classes `PersistentLogger` (lines 94–262) and `EnhancedUserActivityLogger` (lines 264–334)
- Contains: `log_to_sheets()` (blocking), `log_to_sheets_async()` (fire-and-forget thread), `get_recent_logs()`, `get_stats_from_logs()`
- Depends on: `google-api-python-client`, `google-cloud-secret-manager`
- Used by: `TelegramBot` handlers, module-level singleton `persistent_logger`

**Secrets Layer:**
- Purpose: Retrieve runtime secrets from Google Cloud Secret Manager
- Location: `bot_telegram_polling.py` — free function `get_secret()` (lines 80–92)
- Contains: Single function wrapping `secretmanager.SecretManagerServiceClient`
- Used by: `GoogleSheetsManager._authenticate()`, `PersistentLogger._setup_sheets_service()`, `TelegramBot.__init__()`

## Data Flow

**Client Lookup (Search):**

1. Telegram delivers a message to Cloud Run via polling
2. `TelegramBot.handle_message()` calls `_addressed_and_processed_text()` to determine if the message is directed at the bot (private chat, mention, reply, or direct phone number in group)
3. `_extract_client_number()` extracts digit sequences from the text; `_normalize_phone()` strips leading zeros
4. `GoogleSheetsManager.get_client_data_async()` runs `get_client_data()` in `ThreadPoolExecutor`
5. `get_client_data()` checks the in-memory `index_phone_to_row` dict (O(1) lookup); on miss it tries suffix matching, then schedules a background `load_index()` rebuild
6. On index hit, `_fetch_row_client_data()` checks the LRU `row_cache`; on miss it reads the single sheet row via Google Sheets API
7. Response is formatted as HTML, sent to Telegram with an inline keyboard "Edit field" button
8. Action is logged asynchronously to the logs spreadsheet via `persistent_logger.log_to_sheets_async()`

**Field Edit Flow:**

1. User clicks "Edit field" — triggers `handle_edit_callback()` with `callback_data="edit_{client_number}"`
2. Bot presents an inline keyboard of editable fields (all headers except column 0)
3. User selects a field — `callback_data="field_{idx}_{client_number}"` — bot stores `{client_number, field_name}` in `_edit_conversations[chat_id]` dict
4. Bot prompts for the new value; subsequent message from same chat is intercepted at the top of `handle_message()` and routed to `handle_edit_input()`
5. `handle_edit_input()` calls `sheets_manager.update_field_async()`, which writes the cell via Google Sheets API and invalidates the row cache
6. Conversation state for that `chat_id` is removed from `_edit_conversations`

**Index Warm-up on Cold Start:**

1. `GoogleSheetsManager.__init__()` calls `load_index()` synchronously at startup
2. `load_index()` checks `/tmp/sheets_index_rows_{spreadsheet_id}.json` for a valid cached index (within TTL)
3. On cache miss, reads the phone column from the sheet, builds `index_phone_to_row` dict, persists to `/tmp`
4. Background `_start_index_refresher()` thread re-triggers `_schedule_index_rebuild()` every `INDEX_TTL_SECONDS` (default 600s)

**State Management:**
- `_edit_conversations`: `dict[int, dict]` — keyed by `chat_id`, tracks active edit flow per chat
- `recent_messages`: `dict[str, float]` — keyed by `{chat_id}:{user_id}:{text}`, deduplication within `DEDUP_WINDOW_SECONDS` (default 30s)
- `_pending_notifications`: `set` — debounce for follow-up index rebuild notifications
- All state is in-process memory; not persisted across restarts

## Key Abstractions

**GoogleSheetsManager:**
- Purpose: Encapsulates all I/O to the primary data spreadsheet with caching and retry
- Examples: `bot_telegram_polling.py` lines 338–840
- Pattern: Service object with explicit connection setup; blocking methods wrapped in async executors

**TelegramBot:**
- Purpose: Wires all Telegram handlers together; holds all conversation state
- Examples: `bot_telegram_polling.py` lines 842–1765
- Pattern: Facade over `python-telegram-bot`'s `Application`; handlers are async methods registered via `setup_handlers()`

**PersistentLogger / EnhancedUserActivityLogger:**
- Purpose: Audit trail for all user and system events to a separate log spreadsheet
- Examples: `bot_telegram_polling.py` lines 94–334
- Pattern: `PersistentLogger` is a stateful service (holds Sheets connection); `EnhancedUserActivityLogger` is a static-method utility that delegates to the module-level `persistent_logger` singleton

## Entry Points

**Container Entry Point:**
- Location: `main.py`
- Triggers: Docker `CMD ["python", "main.py"]`, or `python main.py` locally
- Responsibilities: Starts Flask health server in a daemon thread, registers OS signal handlers, instantiates and runs `TelegramBot` in the main thread (required by asyncio)

**Bot Polling Entry Point:**
- Location: `bot_telegram_polling.TelegramBot.run()` (line 1668)
- Triggers: Called by `main.py:run_bot_once()`
- Responsibilities: Builds `Application`, calls `setup_handlers()`, starts `run_polling(drop_pending_updates=True)`

**Health Check Endpoints:**
- Location: `main.py` Flask routes
- `GET /` — returns 200 with simple text
- `GET /health` — returns JSON with `status`, `bot_ready`, `sheets_connected`, `total_clients`

## Error Handling

**Strategy:** Defensive programming with extensive try/except; individual failures are logged and silently absorbed to keep the bot running. Google Sheets I/O uses exponential backoff retry for transient errors.

**Patterns:**
- Every Telegram `send_message` / `reply_text` is wrapped in try/except with a fallback `context.bot.send_message` call
- `_execute_with_retry()` retries on `BrokenPipeError`, `HttpError` (408, 429, 500–504), and network timeouts with `base_delay * 2^attempt` backoff
- `get_secret()` returns `None` on failure (does not raise); callers check for `None` and raise `ValueError` if secrets are mandatory
- Index rebuild failures are logged as warnings and non-fatal; the bot continues serving from a stale index

## Cross-Cutting Concerns

**Logging:** `logging.basicConfig` to stdout. Log level is INFO by default; set `DEBUG=1` env var to enable DEBUG. Logger names use `__name__`. `httpx`, `httpcore`, `urllib3`, and `telegram.ext._updater` are throttled to WARNING to reduce noise.

**Validation:** No schema validation library. Validation is inline: phone normalization strips non-digits, length checked via `MIN_CLIENT_NUMBER_LENGTH` (default 3), HTML output escaped via `safe_html()` / `html.escape`.

**Authentication:** Two levels — (1) `_is_authorized_user()` checks Telegram user ID against `AUTHORIZED_USERS` env var for privileged commands (`/stats`, `/plogs`); (2) Google API access uses a service account JSON fetched from Secret Manager at startup.

**Concurrency:** Bot handlers run in asyncio event loop (main thread). Blocking Sheets calls are dispatched to a dedicated `ThreadPoolExecutor` (`SHEETS_THREAD_WORKERS`, default 4). Shared state is protected by `threading.Lock` objects (`_index_lock`, `_row_cache_lock`, `_index_build_lock`, `_edit_conversations_lock`, `_recent_messages_lock`).

---

*Architecture analysis: 2026-03-13*
