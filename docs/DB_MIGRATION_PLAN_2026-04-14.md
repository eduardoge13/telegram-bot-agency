# DB Migration Plan (2026-04-14)

## Current status
- Production bot is running and healthy on VPS.
- Immediate Sheets capacity issue was mitigated by reducing unused columns and expanding rows in the active tab.
- Active intake tab: `Active_20260414`
- Historical archive tab: `Sheet1`

## Immediate production objective
Keep operations stable now while preparing a controlled migration from Google Sheets to a real database.

## Phase 0: Stabilize Google Sheets (done)
- Keep client writes in `Active_20260414`.
- Keep historical reads in `Sheet1`.
- Continue using in-memory index cache for fast phone lookups.

## Phase 1: Prepare a new production spreadsheet file (short term)
Goal: make spreadsheet rollover repeatable and avoid future 10M cell emergencies.

### Required one-time manual step
Create a new Google Spreadsheet file and share it as `Editor` with:
- `telegram-bot@telegram-bot-production.iam.gserviceaccount.com`

### Bot config cutover
When new file is created:
- `SPREADSHEET_ID=<NEW_FILE_ID>`
- `PRIMARY_SHEET_NAME=Sheet1`
- `ARCHIVE_SPREADSHEET_IDS=<OLD_FILE_ID>`
- `ARCHIVE_SHEET_NAMES=` (empty)

Result:
- New records are stored in the new file.
- Bot can still read old records from the archive file.

## Phase 2: Database migration (recommended target: PostgreSQL)
Goal: remove hard dependency on Sheets as primary store.

### Why PostgreSQL
- Better scale for 100k+ to millions of records.
- Strong indexing for phone lookups.
- Reliable updates, constraints, and auditability.
- Easy backup/restore and observability.

### Proposed schema (minimum)
- `clients`
  - `id` (bigserial pk)
  - `phone_normalized` (varchar, unique index)
  - `name`
  - `email`
  - `bank`
  - `metadata_json` (jsonb)
  - `created_at`, `updated_at`
- `client_events`
  - `id` (bigserial pk)
  - `client_id` (fk clients.id)
  - `event_type`
  - `payload_json` (jsonb)
  - `created_at`

### Migration strategy (safe)
1. Build DB adapter layer in bot (`Repository` pattern).
2. Backfill historical data from Sheets to PostgreSQL.
3. Enable dual-write (DB primary + Sheets shadow write) for 1-2 weeks.
4. Validate parity with nightly checks.
5. Switch reads to DB only.
6. Keep Sheets as export/report sink, not source of truth.

## Phase 3: Cache strategy redesign
Current behavior indexes every phone in memory.

### Problems at larger scale
- Memory growth with row count.
- Rebuild latency increases over time.

### Target design
- Use PostgreSQL indexed lookups (`phone_normalized` btree index).
- Replace full in-memory index with bounded LRU cache (hot set only).
- Optional Redis for shared cache if multiple bot instances are used.

## Operational checklist
- Add health endpoint checks for DB connectivity and query latency.
- Add backup policy for DB (daily snapshots + PITR if possible).
- Add migration runbook and rollback runbook.
- Add alerting for ingest failures and queue lag.

## Suggested execution order
1. Complete spreadsheet file rollover playbook.
2. Implement DB schema + data access layer.
3. Run historical backfill.
4. Deploy dual-write.
5. Verify parity and cut reads to DB.
6. Decommission Sheets as primary data store.
