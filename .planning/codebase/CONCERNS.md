# Codebase Concerns

**Analysis Date:** 2026-03-13

## Tech Debt

**Monolithic single-file architecture:**
- Issue: All application logic (bot handlers, Sheets access, logging, retry, caching, conversation state) lives in one 1,765-line file.
- Files: `bot_telegram_polling.py`
- Impact: Changes to one concern (e.g., retry logic) require touching the same file as message handlers. Tests must mock deeply nested internal structure. Onboarding is slow.
- Fix approach: Extract `GoogleSheetsManager` into `sheets/manager.py`, `PersistentLogger` into `logging/persistent.py`, and Telegram handlers into `bot/handlers.py`.

**Module-level global side effect at import time:**
- Issue: `persistent_logger = PersistentLogger()` runs at module import (line 336), which calls Secret Manager immediately. `setup_logging()` is also called at module level (line 68).
- Files: `bot_telegram_polling.py` (lines 68, 336)
- Impact: Importing the module triggers network calls. Tests that import the module risk hitting production Secret Manager unless they mock before import, and import order matters.
- Fix approach: Instantiate `persistent_logger` inside `TelegramBot.__init__` or use a lazy singleton pattern.

**`sheet_info` cached at startup only:**
- Issue: `self.sheet_info = self.sheets_manager.get_sheet_info()` is called once in `TelegramBot.__init__`. The `/info` and `/status` commands read this stale value. Total client count displayed to users does not update until the bot restarts.
- Files: `bot_telegram_polling.py` (lines 863, 1123, 1174)
- Impact: Users see outdated client counts; the status command does not reflect live data.
- Fix approach: Call `get_sheet_info()` on demand inside the command handlers (or refresh on a schedule), rather than caching at startup.

**`min_client_digits` defined redundantly on two classes:**
- Issue: `GoogleSheetsManager` defines `self.min_client_digits` (line 356) but never uses it. `TelegramBot` defines its own copy (line 886) and uses it in `_extract_client_number`. The setting is read from `MIN_CLIENT_NUMBER_LENGTH` twice.
- Files: `bot_telegram_polling.py` (lines 356, 886, 995)
- Impact: Config drift risk if someone changes one but not the other.
- Fix approach: Remove the unused copy from `GoogleSheetsManager`; define the constant once at module level.

**Normalization function defined three times with fallback ladder:**
- Issue: `_normalize_phone` is defined on `GoogleSheetsManager`, on `TelegramBot.__init__`, as a class method on `TelegramBot`, and as inline fallbacks inside `handle_message` and `_get_normalize_fn`. The comment at line 864 explains this was a runtime safety measure, but it has accumulated into six copies of the same logic.
- Files: `bot_telegram_polling.py` (lines 553–558, 872–878, 897–909, 919–924, 1277–1282)
- Impact: The extra defensive guards add noise and mask the real problem (unpredictable attribute binding); any change to normalization logic must be propagated to multiple places.
- Fix approach: Define one `normalize_phone(raw: str) -> str` module-level function. Remove all defensive copies.

**Response formatting duplicated in two handlers:**
- Issue: The HTML response block building client data (field_mappings dict, parts list, edit button) appears identically in `handle_message` (lines 1377–1399) and `_followup_after_rebuild` (lines 1720–1737).
- Files: `bot_telegram_polling.py` (lines 1377–1399, 1720–1737)
- Impact: Any change to how client data is displayed must be made in two places.
- Fix approach: Extract `_build_client_response_html(client_data, client_number)` helper.

---

## Known Bugs

**Edit conversation not scoped to user, only to chat:**
- Symptoms: In a group chat, if user A starts editing a field (conversation state stored by `chat_id`), any subsequent message from user B in the same group chat is routed to `handle_edit_input` and treated as the new field value.
- Files: `bot_telegram_polling.py` (lines 892, 1298–1306, 1549–1553, 1583–1590)
- Trigger: Two users in the same group chat when one has an active edit conversation.
- Workaround: Bot is currently single-user friendly in groups; risk is real in active group deployments.

**`callback_data` payload carries client number with no size validation:**
- Symptoms: Telegram limits `callback_data` to 64 bytes. `callback_data=f"field_{idx}_{client_number}"` or `callback_data=f"edit_{client_number}"` will silently fail or raise an API error if the client number is longer than ~55 characters.
- Files: `bot_telegram_polling.py` (lines 1399, 1523, 1736)
- Trigger: A phone number or client ID in the sheet exceeding ~55 characters causes `InlineKeyboardMarkup` creation to fail.
- Workaround: None implemented.

**`_pending_notifications` set is not thread-safe:**
- Symptoms: `_pending_notifications` is a plain Python `set` accessed from `asyncio.create_task` coroutines without a lock. Under concurrent lookups the `add`/`discard` operations are not atomic at Python level in edge cases.
- Files: `bot_telegram_polling.py` (lines 889, 1699–1701, 1764)
- Trigger: Multiple simultaneous searches for the same client number while the index is warming.
- Workaround: Risk is low given CPython GIL, but it is technically unsafe.

---

## Security Considerations

**Authorization bypass when `AUTHORIZED_USERS` is not set:**
- Risk: `_is_authorized_user` returns `True` for all users when `AUTHORIZED_USERS` env var is empty or unset (line 1048: `return ... if authorized_users != [''] else True`). This means `/stats` and `/plogs` commands expose all activity logs to any Telegram user by default.
- Files: `bot_telegram_polling.py` (line 1046–1048)
- Current mitigation: Documented that `AUTHORIZED_USERS` should be set in deployment.
- Recommendations: Change the default to deny-all (`return False`) when the env var is not set. Require explicit opt-in.

**Authorization not applied to edit operations:**
- Risk: Any Telegram user who receives a search result (which includes the "Edit field" inline button) can press the button and modify client data in Google Sheets. There is no `_is_authorized_user` check in `handle_edit_callback` or `handle_edit_input`.
- Files: `bot_telegram_polling.py` (lines 1483–1640)
- Current mitigation: None.
- Recommendations: Add `_is_authorized_user` check at the start of `handle_edit_callback` before allowing the edit flow to begin.

**GCP Project ID exposed in `SECURITY.md` and `deploy.sh`:**
- Risk: `promising-node-469902-m2` appears in plain text in `SECURITY.md` (multiple gcloud commands), `deploy.sh` (line 22), and is intended to be committed to git.
- Files: `SECURITY.md`, `deploy.sh` (line 22)
- Current mitigation: Project ID alone is not a secret, but combined with leaked credentials or a misconfigured IAM it aids an attacker in targeting the right GCP project.
- Recommendations: Move project ID to an environment variable or config file excluded from git.

**No `.dockerignore` — sensitive local files may enter Docker image:**
- Risk: `COPY . .` in `Dockerfile` copies the entire project directory. Without a `.dockerignore`, files like `telegram_dev_token.txt`, `dev_config.env`, `prod_setup/`, `__pycache__/`, `.venv/`, and `.planning/` are baked into the container image. If the image is pushed to a registry, tokens are exposed.
- Files: `Dockerfile` (line 15)
- Current mitigation: `.gitignore` exists but does not protect the Docker build context.
- Recommendations: Create `.dockerignore` excluding `prod_setup/`, `telegram_dev_token.txt`, `dev_config.env`, `.venv/`, `__pycache__/`, `tests/`, `.planning/`.

**Synchronous persistent log calls block bot startup and system events:**
- Risk: `log_system_event` (called at bot startup) calls `log_to_sheets` synchronously (line 325), which makes a live Google Sheets API call in the request path during startup. If Secret Manager or Sheets is slow, bot startup is delayed.
- Files: `bot_telegram_polling.py` (lines 317–333, 325, 1674)
- Current mitigation: The `log_user_action` path was converted to `log_to_sheets_async`, but `log_system_event` was not.
- Recommendations: Convert `log_system_event` to use `log_to_sheets_async`.

---

## Performance Bottlenecks

**`get_stats_from_logs` reads the entire logs sheet on every `/stats` call:**
- Problem: `get_stats_from_logs` fetches all rows from `Sheet1!A:I` with no limit, then iterates them in Python. As the logs sheet grows (every user action is appended), this call becomes increasingly expensive.
- Files: `bot_telegram_polling.py` (lines 203–262)
- Cause: No pagination, no aggregation in the sheet, no in-memory stats cache.
- Improvement path: Add a summary row or a separate stats sheet that is updated incrementally. Alternatively, cache the stats in memory with a short TTL (e.g., 60 seconds).

**`get_recent_logs` reads the entire logs sheet to return 50 rows:**
- Problem: `get_recent_logs` fetches `Sheet1!A:I` (all rows) to slice the last N (default 50). With thousands of log entries this wastes API quota and adds latency to every `/plogs` invocation.
- Files: `bot_telegram_polling.py` (lines 180–201)
- Cause: Google Sheets API does not natively support reading "last N rows" without knowing total row count. The code does not request a specific row range.
- Improvement path: Track total row count in a separate cell, or use a fixed rolling window range (e.g., last 1000 rows) rather than reading the full column.

**Index TTL-based refresh triggers full-sheet scan every 10 minutes:**
- Problem: `_start_index_refresher` wakes up every `index_ttl` seconds (default 600s) and rebuilds the index by reading the entire phone column from the sheet. For a large sheet this is a significant API call frequency.
- Files: `bot_telegram_polling.py` (lines 484–497, 560–634)
- Cause: No delta/change detection; always reads full column.
- Improvement path: Use Google Sheets `changesToken` or a last-modified timestamp to skip rebuilds when the sheet has not changed.

---

## Fragile Areas

**`_find_client_column` uses keyword matching that can misidentify columns:**
- Files: `bot_telegram_polling.py` (lines 525–551)
- Why fragile: Column selection matches the first header containing any of `['client', 'number', 'id', 'code']`. A sheet with a column named "order id" or "product code" before the phone column would be selected instead.
- Safe modification: Add the ability to specify the column index directly via an env var (e.g., `CLIENT_COLUMN_INDEX`) as an override.
- Test coverage: No tests for `_find_client_column`.

**Edit conversation state is lost on bot restart:**
- Files: `bot_telegram_polling.py` (lines 892–893)
- Why fragile: `_edit_conversations` is an in-memory dict. If the bot restarts (Cloud Run cold start, OOM, or redeploy) while a user is mid-edit, the state is gone. The user's next message is then treated as a client number search rather than a field value, with no feedback.
- Safe modification: Add a conversation expiry TTL and send a "session expired" message when a stale conversation key is referenced.
- Test coverage: Not tested.

**`_followup_after_rebuild` polls `_index_warming` in a tight loop:**
- Files: `bot_telegram_polling.py` (lines 1692–1765)
- Why fragile: The coroutine polls `_index_warming` every 1 second for up to 30 seconds. If the background rebuild runs longer than 30 seconds (large sheet), the follow-up sends a "not found" message even though the data may arrive moments later.
- Safe modification: Use `asyncio.Event` to signal completion rather than polling with a timeout.
- Test coverage: Not tested.

---

## Scaling Limits

**Single instance constraint (max-instances=1):**
- Current capacity: One Cloud Run instance, one polling connection to Telegram.
- Limit: If the single instance OOMs or crashes, there is a restart gap with no bot availability. Telegram polling cannot run on multiple instances simultaneously (they would each try to poll and conflict).
- Scaling path: Migrate from polling to webhook mode to allow horizontal scaling behind Cloud Run's load balancer. This would require adding a webhook endpoint and removing the polling loop.

**In-memory deduplication does not survive restarts:**
- Current capacity: `recent_messages` dict is bounded only by `dedupe_window` cleanup.
- Limit: On restart all deduplication state is lost; pending messages queued during downtime are re-processed, potentially duplicating responses.
- Scaling path: Use a lightweight external cache (Redis, Memorystore) for deduplication state.

---

## Dependencies at Risk

**`python-telegram-bot==20.8` (pinned, 2+ major versions behind):**
- Risk: Version 20.x is not the latest stable release series. The library has since released 21.x with breaking changes. Pinning to 20.8 means security patches in newer releases are not received.
- Impact: Bot handlers rely on `Application.run_polling` API which changed in 21.x.
- Migration plan: Review 21.x changelog for breaking changes; the main incompatibility is in job queue and application builder API.

**`google-api-python-client==2.134.0` (pinned without upper bound):**
- Risk: No upper bound means a `pip install -r requirements.txt` on a fresh environment could resolve to a newer version if `==` is removed. If it is kept as `==`, security patches require manual version bumps.
- Impact: Sheets API client; no known active vulnerability at pinned version.
- Migration plan: Add Dependabot or a weekly `pip-audit` CI step.

---

## Missing Critical Features

**No rate limiting per user:**
- Problem: Any Telegram user (or bot) can flood the bot with messages, triggering rapid-fire Sheets API calls and exhausting the daily Google Sheets quota (60 requests/minute/project for the standard tier).
- Blocks: Running at scale or in public groups without risking quota exhaustion.

**No webhook-based deployment path:**
- Problem: The bot exclusively uses long-polling (`run_polling`). Cloud Run's pay-per-request model is best suited for webhook mode; long-polling requires `min-instances=1` which means the instance runs 24/7 even with zero traffic.
- Blocks: Cost optimization; horizontal scaling; zero-downtime deploys.

**No health check for index state:**
- Problem: The `/health` endpoint reports `sheets_connected` but does not report whether the in-memory phone index has been loaded. Operators have no visibility into whether the bot can actually serve lookups.
- Blocks: Reliable readiness probes; early detection of index-warming failures.

---

## Test Coverage Gaps

**Edit flow (callback and input handlers) completely untested:**
- What's not tested: `handle_edit_callback`, `handle_edit_input`, the full edit conversation lifecycle, cancellation, concurrent edit conflicts between users in the same group.
- Files: `bot_telegram_polling.py` (lines 1483–1640)
- Risk: Regressions in the edit flow (including the authorization bypass described above) would not be caught.
- Priority: High

**`_find_client_column` logic untested:**
- What's not tested: Column selection via keyword matching; the default fallback to column 0; behavior when headers are empty.
- Files: `bot_telegram_polling.py` (lines 525–551)
- Risk: Wrong column silently selected, causing all lookups to fail or search the wrong field.
- Priority: High

**`PersistentLogger` untested:**
- What's not tested: `log_to_sheets`, `get_recent_logs`, `get_stats_from_logs`; the async thread wrapper `log_to_sheets_async`.
- Files: `bot_telegram_polling.py` (lines 94–262)
- Risk: Log data corruption or silently dropped logs go undetected.
- Priority: Medium

**No integration or end-to-end tests:**
- What's not tested: Full message → Sheets lookup → response cycle; bot startup with missing env vars; graceful shutdown via SIGTERM.
- Files: `tests/test_webhook.py` — uses a live local HTTP endpoint rather than a proper test harness and is not runnable in CI.
- Risk: Deployment regressions discovered only in production.
- Priority: Medium

---

*Concerns audit: 2026-03-13*
