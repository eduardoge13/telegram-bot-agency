# External Integrations

**Analysis Date:** 2026-03-13

## APIs & External Services

**Telegram Bot API:**
- Telegram Bot API (via `python-telegram-bot==20.8`) - Core messaging platform; bot receives updates via long-polling
  - SDK/Client: `python-telegram-bot[job-queue]==20.8`
  - Auth: Bot token stored in GCP Secret Manager under secret name `telegram-bot-token` (prod) or `telegram-bot-token-dev` (dev); optionally overridden via `TELEGRAM_BOT_TOKEN` env var
  - Bot token obtained from @BotFather on Telegram
  - Polling configured in `bot_telegram_polling.py` → `TelegramBot.run()` / `TelegramBot.setup_handlers()`

**Google Sheets API v4:**
- Google Sheets API v4 - Primary data store for client records and persistent audit logs
  - SDK/Client: `google-api-python-client==2.134.0` (`googleapiclient.discovery.build('sheets', 'v4', ...)`)
  - Auth: Service account JSON credentials fetched from GCP Secret Manager at runtime (`get_secret(project_id, 'google-credentials-json')`)
  - Scopes: `https://www.googleapis.com/auth/spreadsheets` (read + write)
  - Two spreadsheets used:
    - **Client data sheet** (`SPREADSHEET_ID` env var) - Source of truth for client records; read for lookups, written for field updates
    - **Logs sheet** (`LOGS_SPREADSHEET_ID` env var) - Append-only audit log; all user actions and system events written here via `PersistentLogger`
  - Implementation files: `bot_telegram_polling.py` → `GoogleSheetsManager` class (lines 339–841), `PersistentLogger` class (lines 94–262)

## Data Storage

**Databases:**
- No traditional database (PostgreSQL, MySQL, etc.)
- Google Sheets acts as the sole persistent data store for both client records and logs
  - Client data connection: `SPREADSHEET_ID` env var
  - Logs connection: `LOGS_SPREADSHEET_ID` env var
  - Client: `googleapiclient` + service account credentials from Secret Manager
  - ORM: None — raw Sheets API v4 calls (`spreadsheets().values().get()`, `.append()`, `.update()`)

**File Storage:**
- Local filesystem only (for temporary deployment artifacts; no persistent file storage)

**Caching:**
- In-process only; no external cache (Redis, Memcached, etc.)
  - **Phone index** (`GoogleSheetsManager.index_phone_to_row`): `Dict[str, int]` in memory; rebuilt on TTL expiry (`INDEX_TTL_SECONDS`, default 600s); protected by `threading.Lock`
  - **Row cache** (`GoogleSheetsManager.row_cache`): `OrderedDict` LRU cache; max size controlled by `ROW_CACHE_SIZE` env var (default 200)
  - **Message deduplication store** (`TelegramBot.recent_messages`): `Dict[str, float]` in memory; window controlled by `DEDUP_WINDOW_SECONDS` (default 30s)

## Authentication & Identity

**Auth Provider:**
- Google Cloud Secret Manager (`google-cloud-secret-manager==2.20.0`) - Used to store and retrieve all secrets at container startup
  - Implementation: `get_secret()` function in `bot_telegram_polling.py` (line 80)
  - Secrets managed:
    - `google-credentials-json` / `google-credentials-json-dev` — Service account JSON for Sheets API
    - `telegram-bot-token` / `telegram-bot-token-dev` — Telegram bot token
  - IAM: Cloud Run service identity must have `secretmanager.secretAccessor` role on the secrets

**User Authorization:**
- Custom allowlist — Telegram user IDs listed in `AUTHORIZED_USERS` env var (comma-separated)
- Authorization check in `TelegramBot._is_authorized_user()` (`bot_telegram_polling.py` line 1046)
- Unauthorized users receive a rejection message; no other access control layer

## Monitoring & Observability

**Error Tracking:**
- None (no Sentry, Datadog, etc.)

**Logs:**
- **Stdout/stderr** — Python `logging` module; structured format `[timestamp] LEVEL | module | message`; streamed to Cloud Run logs; viewable via `gcloud run services logs read`
- **Persistent Google Sheets log** — Every user action and system event appended to `LOGS_SPREADSHEET_ID` spreadsheet via `PersistentLogger.log_to_sheets()` and `EnhancedUserActivityLogger` (fire-and-forget background thread)
- Log verbosity: INFO by default; DEBUG enabled via `DEBUG=1` env var
- Noisy HTTP client loggers (`httpx`, `httpcore`, `urllib3`, `telegram.ext._updater`) suppressed to WARNING level

**Health Checks:**
- `GET /` — Returns plain text "Bot is running!" or "Bot is starting..." (HTTP 200)
- `GET /health` — Returns JSON `{status, bot_ready, sheets_connected, total_clients, timestamp}`; used by Cloud Run liveness probes and `deploy.sh` post-deploy validation
- Implemented in `main.py` Flask app (lines 51–80)

## CI/CD & Deployment

**Hosting:**
- Google Cloud Run (`us-central1`, project `promising-node-469902-m2`)
- Container built via `gcloud run deploy --source .` (Cloud Build triggered automatically)
- Service names: `telegram-bot-dev` (dev) / `telegram-bot-agency` (prod)
- Resource limits: 512Mi memory, 1 vCPU, min/max instances = 1

**CI Pipeline:**
- None (no GitHub Actions, CircleCI, etc.)
- Manual deployments via `deploy.sh dev` or `deploy.sh prod`

**Container Registry:**
- Google Cloud Build / Artifact Registry (implicit via `gcloud run deploy --source`)

## Webhooks & Callbacks

**Incoming:**
- None — Bot uses long-polling mode exclusively (`python-telegram-bot` `Application.run_polling()`); no webhook endpoint registered with Telegram

**Outgoing:**
- None — Bot sends messages to Telegram via the Bot API client; no outgoing webhooks configured

## Environment Configuration

**Required env vars (production):**
- `GCP_PROJECT_ID` — GCP project for Secret Manager lookups
- `SPREADSHEET_ID` — Google Sheets ID for client data
- `LOGS_SPREADSHEET_ID` — Google Sheets ID for audit logs
- `AUTHORIZED_USERS` — Comma-separated Telegram user IDs

**Optional env vars with defaults:**
- `TELEGRAM_BOT_TOKEN` — Direct token override (bypasses Secret Manager)
- `DEBUG` — Enable debug logging
- `INDEX_TTL_SECONDS` (600) — Phone index cache TTL
- `ROW_CACHE_SIZE` (200) — LRU row cache max size
- `SHEETS_THREAD_WORKERS` (4) — Background IO thread pool size
- `SHEETS_RETRY_ATTEMPTS` (3) — Sheets API retry count
- `SHEETS_RETRY_BASE_DELAY` (0.5) — Exponential backoff base seconds
- `MIN_CLIENT_NUMBER_LENGTH` (3) — Minimum digits for client number recognition
- `DEDUP_WINDOW_SECONDS` (30) — Message deduplication window
- `PORT` (8080) — Flask health server port

**Secrets location:**
- GCP Secret Manager (`promising-node-469902-m2`); accessed at container startup via `get_secret()` in `bot_telegram_polling.py`
- Local development: `.env` file (gitignored); token in `telegram_dev_token.txt` (gitignored)

---

*Integration audit: 2026-03-13*
