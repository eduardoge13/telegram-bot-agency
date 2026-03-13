# Codebase Structure

**Analysis Date:** 2026-03-13

## Directory Layout

```
telegram-bot-agency/
├── main.py                        # Process entry point (Flask health + bot runner)
├── bot_telegram_polling.py        # All bot logic (1765 lines, single module)
├── requirements.txt               # Python dependencies
├── Dockerfile                     # Container build (python:3.12-slim, port 8080)
├── deploy.sh                      # Cloud Run deploy script
├── dev_config.env                 # Local dev environment variable template (checked in)
├── dev_config.env.template        # Template for dev_config.env
├── .env                           # Local secrets (gitignored)
├── .python-version                # Python version pin (3.x)
├── tests/
│   ├── test_index_manager.py      # Unit tests for GoogleSheetsManager
│   ├── test_message_parsing.py    # Unit tests for TelegramBot message handling
│   └── test_webhook.py            # Webhook smoke tests
├── docs/
│   ├── PROJECT_CONTEXT.md         # Business context and infrastructure details
│   ├── AGENT_INSTRUCTIONS.md      # Agent/LLM operational instructions
│   └── SCALING_TEST_PLAN.md       # Scale-to-zero test documentation
├── prod_setup/
│   ├── README.md                  # Production setup guide
│   ├── prod_config.env            # Production env var values (non-secret)
│   └── telegram_bot_production.json  # Cloud Run service JSON descriptor
├── logs/                          # Local log output directory (empty in repo)
├── .planning/                     # GSD planning documents
│   └── codebase/                  # Codebase analysis documents
├── .venv/                         # Local virtual environment (gitignored)
├── .pytest_cache/                 # Pytest cache (gitignored)
├── __pycache__/                   # Python bytecode cache (gitignored)
├── BANK_FEATURE_SUMMARY.md        # Feature documentation
├── DEPLOYMENT_GUIDE.md            # Deployment runbook
├── README.md                      # Project overview
└── SECURITY.md                    # Security notes
```

## Directory Purposes

**Root (source files):**
- Purpose: All runtime Python source lives at the root — there is no `src/` subdirectory
- Contains: `main.py`, `bot_telegram_polling.py`, configuration files, Dockerfile
- Key files: `bot_telegram_polling.py` (entire bot), `main.py` (process entrypoint)

**`tests/`:**
- Purpose: Automated unit tests
- Contains: pytest test files; no subdirectory structure
- Key files: `tests/test_index_manager.py`, `tests/test_message_parsing.py`

**`docs/`:**
- Purpose: Human-readable reference documents for the project
- Contains: Context docs, agent instructions, test plans
- Key files: `docs/PROJECT_CONTEXT.md` (most detailed reference)

**`prod_setup/`:**
- Purpose: Production deployment configuration and service descriptors
- Contains: Non-secret prod env vars, Cloud Run JSON service config
- Key files: `prod_setup/prod_config.env`, `prod_setup/telegram_bot_production.json`

**`.planning/codebase/`:**
- Purpose: GSD codebase analysis documents consumed by plan/execute commands
- Generated: By `/gsd:map-codebase`
- Committed: Yes

**`logs/`:**
- Purpose: Reserved for local log file output; empty in repository
- Generated: At runtime if configured
- Committed: Directory only (no log files)

## Key File Locations

**Entry Points:**
- `main.py`: Container/process entry point — starts Flask health server and runs the bot
- `bot_telegram_polling.py`: All bot logic — import `TelegramBot` from here

**Configuration:**
- `.env`: Local development secrets (never committed)
- `dev_config.env`: Local dev environment variable values (committed, no secrets)
- `dev_config.env.template`: Template documenting all required env vars
- `prod_setup/prod_config.env`: Production environment variable values (non-secret)
- `.python-version`: Python version pin for `pyenv`

**Core Logic:**
- `bot_telegram_polling.py` line 338 — `class GoogleSheetsManager`: data access, index, cache, retry
- `bot_telegram_polling.py` line 842 — `class TelegramBot`: all handlers, conversation state, message routing
- `bot_telegram_polling.py` line 94 — `class PersistentLogger`: audit log writes to Sheets
- `bot_telegram_polling.py` line 264 — `class EnhancedUserActivityLogger`: user action logging utility
- `bot_telegram_polling.py` line 80 — `get_secret()`: Secret Manager helper function

**Build & Deploy:**
- `Dockerfile`: Container definition (base `python:3.12-slim`, `CMD ["python", "main.py"]`)
- `deploy.sh`: Shell script for `gcloud run deploy`
- `requirements.txt`: Pinned Python dependencies

**Testing:**
- `tests/test_index_manager.py`: Tests for `GoogleSheetsManager` (retry, suffix matching, single-flight rebuild)
- `tests/test_message_parsing.py`: Tests for `TelegramBot` (extraction, mention detection, address routing)

## Naming Conventions

**Files:**
- Snake case: `bot_telegram_polling.py`, `test_index_manager.py`
- No module packages; all source is flat at root or in `tests/`

**Classes:**
- PascalCase: `TelegramBot`, `GoogleSheetsManager`, `PersistentLogger`, `EnhancedUserActivityLogger`

**Methods:**
- Snake case: `handle_message`, `get_client_data`, `load_index`, `setup_handlers`
- Private methods prefixed with `_`: `_authenticate`, `_normalize_phone`, `_execute_with_retry`, `_fetch_row_client_data`
- Async methods use same naming with `async def`; async wrappers of blocking methods append `_async`: `get_client_data_async`, `update_field_async`

**Instance variables:**
- Snake case: `self.sheets_manager`, `self.index_phone_to_row`, `self.row_cache`
- Private state prefixed with `_`: `self._index_lock`, `self._edit_conversations`, `self._pending_notifications`

**Environment variables:**
- SCREAMING_SNAKE_CASE: `SPREADSHEET_ID`, `LOGS_SPREADSHEET_ID`, `GCP_PROJECT_ID`, `TELEGRAM_BOT_TOKEN`, `AUTHORIZED_USERS`, `INDEX_TTL_SECONDS`, `ROW_CACHE_SIZE`, `MIN_CLIENT_NUMBER_LENGTH`, `ALLOW_DIRECT_GROUP_NUMBER`

**Callback data (inline keyboard):**
- Prefixed strings encoding action and payload: `"edit_{client_number}"`, `"field_{idx}_{client_number}"`, `"edit_cancel"`

## Where to Add New Code

**New bot command:**
- Handler method: Add `async def {name}_command(self, update, context)` to `TelegramBot` in `bot_telegram_polling.py`
- Registration: Add `self.application.add_handler(CommandHandler("{name}", self.{name}_command))` inside `TelegramBot.setup_handlers()`
- Tests: Add test file or extend `tests/test_message_parsing.py`

**New Google Sheets operation:**
- Implementation: Add method to `GoogleSheetsManager` in `bot_telegram_polling.py`
- Pattern: Provide both a synchronous method and an `_async` wrapper using `loop.run_in_executor(self._executor, ...)`
- Tests: Add to `tests/test_index_manager.py`

**New inline keyboard flow:**
- Add new `callback_data` prefix and handle it inside `TelegramBot.handle_edit_callback()`
- If multi-step, add conversation state to `self._edit_conversations` dict and route from `handle_message()`

**Utilities / helpers:**
- Free functions: Add to `bot_telegram_polling.py` at module level (before class definitions), following `safe_html()` and `get_secret()` as examples
- Shared constants: Add as module-level variables near the top of `bot_telegram_polling.py` (see `MEXICO_CITY_TZ`)

**New environment variable:**
- Document in `dev_config.env.template`
- Read with `os.getenv('VAR_NAME', 'default')` inline where used; no central config object

## Special Directories

**`.venv/`:**
- Purpose: Python virtual environment for local development
- Generated: Yes (via `python -m venv .venv`)
- Committed: No (gitignored)

**`logs/`:**
- Purpose: Placeholder for local log files
- Generated: Yes (at runtime)
- Committed: Directory only

**`.planning/`:**
- Purpose: GSD planning and codebase analysis artifacts
- Generated: By GSD tools
- Committed: Yes

**`__pycache__/`:**
- Purpose: Python bytecode cache
- Generated: Yes (by Python interpreter)
- Committed: No (gitignored)

---

*Structure analysis: 2026-03-13*
