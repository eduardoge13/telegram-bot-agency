# Technology Stack

**Analysis Date:** 2026-03-13

## Languages

**Primary:**
- Python 3.12.6 - All application logic, bot handlers, Google Sheets integration

**Secondary:**
- Bash - Deployment scripting (`deploy.sh`)

## Runtime

**Environment:**
- Python 3.12.6 (pinned in `.python-version`)
- CPython (standard interpreter)

**Package Manager:**
- pip (via `requirements.txt`)
- Virtual environment: `.venv/`
- Lockfile: Not present (requirements.txt without pinned transitive deps)

## Frameworks

**Core:**
- `python-telegram-bot[job-queue]==20.8` - Telegram Bot API async framework; polling mode
- `Flask==3.0.3` - Minimal HTTP server for health check endpoints (`/` and `/health`)
- `gunicorn==22.0.0` - WSGI server (installed but not used in polling mode; present for potential webhook mode)

**Testing:**
- `pytest` (via `.pytest_cache/` presence) - Test runner
- No pinned pytest version in `requirements.txt`

**Build/Dev:**
- Docker / `python:3.12-slim` base image - Container packaging
- `python-dotenv==1.0.1` - Local `.env` file loading for development

## Key Dependencies

**Critical:**
- `python-telegram-bot[job-queue]==20.8` - Core bot framework; provides async `Application`, `CommandHandler`, `MessageHandler`, `CallbackQueryHandler`, `InlineKeyboardMarkup`
- `google-api-python-client==2.134.0` - Google Sheets API v4 client; used for all read/write operations via `googleapiclient.discovery.build`
- `google-auth-oauthlib==1.2.0` - OAuth2 service account credentials (`google.oauth2.service_account.Credentials`)
- `google-cloud-secret-manager==2.20.0` - GCP Secret Manager client; used to retrieve bot token and Google service account JSON at runtime

**Infrastructure:**
- `pytz==2024.1` - Timezone handling; `America/Mexico_City` timezone used throughout
- `Flask==3.0.3` - Exposes `/health` JSON endpoint and root health check for Cloud Run liveness probes

## Configuration

**Environment:**
- Configuration loaded via `python-dotenv` from `.env` in development
- In production, env vars injected via Cloud Run at deploy time from `deploy.sh`
- Sensitive values (bot token, Google credentials JSON) fetched at runtime from GCP Secret Manager

**Key env vars required:**
- `GCP_PROJECT_ID` - GCP project identifier; used to scope Secret Manager calls
- `SPREADSHEET_ID` - Main Google Sheet ID for client data
- `LOGS_SPREADSHEET_ID` - Separate Google Sheet ID for persistent audit logs
- `AUTHORIZED_USERS` - Comma-separated Telegram user IDs allowed to use the bot
- `TELEGRAM_BOT_TOKEN` - Optional override; if absent, fetched from Secret Manager
- `DEBUG` - Set to `1`/`true`/`yes` to enable DEBUG log level
- `INDEX_TTL_SECONDS` - Seconds before in-memory phone index expires (default: `600`)
- `ROW_CACHE_SIZE` - Max rows held in LRU cache (default: `200`)
- `SHEETS_THREAD_WORKERS` - ThreadPoolExecutor size for background Sheets IO (default: `4`)
- `SHEETS_RETRY_ATTEMPTS` - Number of retries on transient Sheets errors (default: `3`)
- `SHEETS_RETRY_BASE_DELAY` - Base delay in seconds for exponential backoff (default: `0.5`)
- `MIN_CLIENT_NUMBER_LENGTH` - Minimum digit count for recognized client numbers (default: `3`)
- `DEDUP_WINDOW_SECONDS` - Seconds window for in-memory message deduplication (default: `30`)
- `PORT` - HTTP port for Flask health server (default: `8080`)

**Build:**
- `Dockerfile` - Single-stage build from `python:3.12-slim`; copies source and runs `pip install -r requirements.txt`; exposes port 8080; entrypoint is `python main.py`
- `.gcloudignore` - Controls which files are excluded from Cloud Build source uploads

## Platform Requirements

**Development:**
- Python 3.12.6
- `.env` file with `GCP_PROJECT_ID`, `SPREADSHEET_ID`, `LOGS_SPREADSHEET_ID`, `AUTHORIZED_USERS`
- `telegram_dev_token.txt` with Telegram bot token
- `dev_config.env` (from `dev_config.env.template`) for dev sheet IDs and authorized users
- GCP credentials with Secret Manager access (or local `credentials.json` for fallback)

**Production:**
- Google Cloud Platform project `promising-node-469902-m2`
- Google Cloud Run (us-central1); single instance, no CPU throttling, 512Mi memory, 1 vCPU
- Min instances: 1 (required for polling mode; cannot scale to zero)
- Max instances: 1 (single-instance polling architecture)
- GCP APIs required: Cloud Run, Secret Manager, Google Sheets API, Cloud Build

---

*Stack analysis: 2026-03-13*
