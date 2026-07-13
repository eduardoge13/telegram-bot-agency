#!/usr/bin/env python3
"""Watch Google Sheets row/header changes and trigger incremental cache sync.

The previous watcher only compared row counts, so adding a new column to row 1
did not trigger any refresh for existing cached clients. This watcher stores a
per-source header signature and triggers the sync service when headers change;
`sync_local_db.py` then backfills existing rows in bounded batches.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any

from google.oauth2 import service_account
from googleapiclient.discovery import build

STATE_PATH = os.getenv("SYNC_WATCH_STATE_PATH", "/opt/telegram-bot-agency/data/sync_watch_state.json")
DB_PATH = os.getenv("CLIENT_DB_PATH", "/opt/telegram-bot-agency/data/clients.db")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def parse_sources() -> list[tuple[str, str]]:
    primary_id = (os.getenv("SPREADSHEET_ID") or "").strip()
    primary_sheet = (os.getenv("PRIMARY_SHEET_NAME") or "Sheet1").strip() or "Sheet1"
    archive_ids = [s.strip() for s in (os.getenv("ARCHIVE_SPREADSHEET_IDS") or "").split(",") if s.strip()]

    sources: list[tuple[str, str]] = []
    for sid in archive_ids:
        sources.append((sid, primary_sheet))
    if primary_id:
        sources.append((primary_id, primary_sheet))

    seen: set[str] = set()
    out: list[tuple[str, str]] = []
    for sid, sheet in sources:
        key = f"{sid}:{sheet}"
        if key in seen:
            continue
        seen.add(key)
        out.append((sid, sheet))
    return out


def load_state() -> dict[str, Any]:
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        if isinstance(loaded, dict):
            return loaded
    except Exception:
        pass
    return {"counts": {}, "sources": {}}


def save_state(sources: dict[str, dict[str, Any]]) -> None:
    payload = {
        "updated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "counts": {key: int(meta.get("row_count", 0)) for key, meta in sources.items()},
        "sources": sources,
    }
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    tmp = f"{STATE_PATH}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=True, sort_keys=True)
    os.replace(tmp, STATE_PATH)


def get_service():
    cred_path = (os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or "").strip()
    if not cred_path:
        raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS is not set")
    creds = service_account.Credentials.from_service_account_file(cred_path, scopes=SCOPES)
    return build("sheets", "v4", credentials=creds, cache_discovery=False)


def range_on_sheet(sheet_name: str, cell_range: str) -> str:
    escaped_sheet = sheet_name.replace("'", "''")
    return f"'{escaped_sheet}'!{cell_range}"


def headers_signature(headers: list[str]) -> str:
    normalized = [str(header or "").strip() for header in headers]
    payload = json.dumps(normalized, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def count_rows(service, spreadsheet_id: str, sheet_name: str) -> int:
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_on_sheet(sheet_name, "A:A"),
    ).execute()
    values = result.get("values", [])
    return max(0, len(values) - 1)


def fetch_headers(service, spreadsheet_id: str, sheet_name: str) -> list[str]:
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_on_sheet(sheet_name, "1:1"),
    ).execute()
    values = result.get("values", [[]])
    return [str(value or "").strip() for value in values[0]] if values else []


def current_source_metadata(service, spreadsheet_id: str, sheet_name: str) -> dict[str, Any]:
    headers = fetch_headers(service, spreadsheet_id, sheet_name)
    return {
        "row_count": count_rows(service, spreadsheet_id, sheet_name),
        "headers_hash": headers_signature(headers) if headers else "",
        "header_count": len(headers),
    }


def previous_source_metadata(state: dict[str, Any], key: str) -> dict[str, Any]:
    sources = state.get("sources") if isinstance(state, dict) else {}
    if isinstance(sources, dict) and isinstance(sources.get(key), dict):
        return sources[key]

    # Backward compatibility with the old state shape: {"counts": {"source": n}}.
    counts = state.get("counts") if isinstance(state, dict) else {}
    if isinstance(counts, dict) and key in counts:
        return {"row_count": counts.get(key), "headers_hash": None, "header_count": None}

    return {}


def pending_sync_keys(current_sources: dict[str, dict[str, Any]]) -> list[tuple[str, str, int | None, int]]:
    pending: list[tuple[str, str, int | None, int]] = []
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.row_factory = sqlite3.Row
        for key, meta in current_sources.items():
            sheet_rows = int(meta.get("row_count", 0))
            row = conn.execute(
                "SELECT next_row, backfill_next_row FROM sync_state WHERE sync_key = ?",
                (key,),
            ).fetchone()
            if not row:
                pending.append((key, "append", None, sheet_rows))
                continue
            next_row = int(row["next_row"])
            # Data rows are 2..(sheet_rows+1); synced when next_row > sheet_rows+1.
            if next_row <= sheet_rows + 1:
                pending.append((key, "append", next_row, sheet_rows))
                continue

            backfill_next_row = row["backfill_next_row"]
            if backfill_next_row is not None and int(backfill_next_row) <= sheet_rows + 1:
                pending.append((key, "backfill", int(backfill_next_row), sheet_rows))
    finally:
        conn.close()
    return pending


def is_sync_active() -> bool:
    return subprocess.run(
        ["systemctl", "is-active", "telegram-bot-sync.service"],
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip() == "active"


def trigger_sync(reason: str) -> None:
    if not is_sync_active():
        subprocess.run(["systemctl", "start", "telegram-bot-sync.service"], check=True)
        print(f"watcher: triggered sync ({reason})")
    else:
        print(f"watcher: sync already active ({reason})")


def main() -> int:
    sources = parse_sources()
    if not sources:
        print("watcher: no sources configured")
        return 0

    service = get_service()
    current: dict[str, dict[str, Any]] = {}
    for sid, sheet in sources:
        key = f"{sid}:{sheet}"
        current[key] = current_source_metadata(service, sid, sheet)

    state = load_state()

    row_changes: list[tuple[str, int, int]] = []
    header_changes: list[tuple[str, int | None, int, str, str]] = []
    for key, meta in current.items():
        previous = previous_source_metadata(state, key)

        old_rows = previous.get("row_count")
        if old_rows is not None and int(old_rows) != int(meta["row_count"]):
            row_changes.append((key, int(old_rows), int(meta["row_count"])))

        old_hash = previous.get("headers_hash")
        new_hash = meta.get("headers_hash") or ""
        if old_hash and new_hash and old_hash != new_hash:
            header_changes.append((
                key,
                previous.get("header_count"),
                int(meta.get("header_count", 0)),
                str(old_hash)[:12],
                str(new_hash)[:12],
            ))

    pending = pending_sync_keys(current)

    if header_changes:
        trigger_sync("header/column change")
        for key, old_count, new_count, old_hash, new_hash in header_changes:
            print(
                f"watcher: {key} headers {old_count} -> {new_count} "
                f"hash {old_hash} -> {new_hash}"
            )
    elif row_changes:
        trigger_sync("row-count change")
        for key, old, new in row_changes:
            print(f"watcher: {key} rows {old} -> {new}")
    elif pending:
        trigger_sync("pending rows")
        for key, mode, next_row, sheet_rows in pending:
            print(f"watcher: {key} pending mode={mode} next_row={next_row} sheet_rows={sheet_rows}")
    else:
        print("watcher: no sheet row/header changes and no pending rows")

    save_state(current)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"watcher: error: {exc}", file=sys.stderr)
        raise
