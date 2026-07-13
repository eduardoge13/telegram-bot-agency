#!/usr/bin/env python3
"""Incremental sync from Google Sheets into the local SQLite cache."""

import argparse
import hashlib
import json
import sqlite3
import time
from typing import Any, Dict, List, Tuple

from bot_telegram_polling import GoogleSheetsManager, logger


def ensure_sync_state_table(db: sqlite3.Connection):
    db.execute(
        '''
        CREATE TABLE IF NOT EXISTS sync_state (
            sync_key TEXT PRIMARY KEY,
            next_row INTEGER NOT NULL,
            last_total_rows INTEGER NOT NULL DEFAULT 0,
            headers_hash TEXT,
            headers_json TEXT,
            backfill_next_row INTEGER,
            backfill_headers_hash TEXT,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        '''
    )
    columns = {
        row[1]
        for row in db.execute("PRAGMA table_info(sync_state)").fetchall()
    }
    if "headers_hash" not in columns:
        db.execute("ALTER TABLE sync_state ADD COLUMN headers_hash TEXT")
    if "headers_json" not in columns:
        db.execute("ALTER TABLE sync_state ADD COLUMN headers_json TEXT")
    if "backfill_next_row" not in columns:
        db.execute("ALTER TABLE sync_state ADD COLUMN backfill_next_row INTEGER")
    if "backfill_headers_hash" not in columns:
        db.execute("ALTER TABLE sync_state ADD COLUMN backfill_headers_hash TEXT")


def get_sync_key(sheet_id: str, sheet_name: str) -> str:
    return f"{sheet_id}:{sheet_name}"


def get_next_row(db: sqlite3.Connection, sync_key: str) -> int:
    row = db.execute(
        'SELECT next_row FROM sync_state WHERE sync_key = ?',
        (sync_key,)
    ).fetchone()
    return int(row[0]) if row else 2


def get_sync_state(db: sqlite3.Connection, sync_key: str) -> Dict[str, Any]:
    row = db.execute(
        '''
        SELECT next_row, last_total_rows, headers_hash, headers_json,
               backfill_next_row, backfill_headers_hash
        FROM sync_state
        WHERE sync_key = ?
        ''',
        (sync_key,)
    ).fetchone()
    if not row:
        return {
            "next_row": 2,
            "last_total_rows": 0,
            "headers_hash": None,
            "headers_json": None,
            "backfill_next_row": None,
            "backfill_headers_hash": None,
        }
    return {
        "next_row": int(row["next_row"] if isinstance(row, sqlite3.Row) else row[0]),
        "last_total_rows": int(row["last_total_rows"] if isinstance(row, sqlite3.Row) else row[1]),
        "headers_hash": row["headers_hash"] if isinstance(row, sqlite3.Row) else row[2],
        "headers_json": row["headers_json"] if isinstance(row, sqlite3.Row) else row[3],
        "backfill_next_row": row["backfill_next_row"] if isinstance(row, sqlite3.Row) else row[4],
        "backfill_headers_hash": row["backfill_headers_hash"] if isinstance(row, sqlite3.Row) else row[5],
    }


def headers_signature(headers: List[str]) -> str:
    normalized = [str(header or "").strip() for header in headers]
    payload = json.dumps(normalized, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def update_sync_state(
    db: sqlite3.Connection,
    sync_key: str,
    next_row: int,
    total_rows: int,
    headers: List[str] | None = None,
):
    header_hash = headers_signature(headers) if headers is not None else None
    headers_json = json.dumps(headers or [], ensure_ascii=False, separators=(",", ":")) if headers is not None else None
    db.execute(
        '''
        INSERT INTO sync_state(sync_key, next_row, last_total_rows, headers_hash, headers_json, updated_at)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(sync_key) DO UPDATE SET
            next_row = excluded.next_row,
            last_total_rows = excluded.last_total_rows,
            headers_hash = COALESCE(excluded.headers_hash, sync_state.headers_hash),
            headers_json = COALESCE(excluded.headers_json, sync_state.headers_json),
            updated_at = CURRENT_TIMESTAMP
        ''',
        (sync_key, next_row, total_rows, header_hash, headers_json)
    )


def update_sync_metadata(
    db: sqlite3.Connection,
    sync_key: str,
    total_rows: int,
    headers: List[str],
) -> None:
    state = get_sync_state(db, sync_key)
    update_sync_state(db, sync_key, int(state["next_row"]), total_rows, headers)


def set_backfill_state(
    db: sqlite3.Connection,
    sync_key: str,
    next_row: int | None,
    headers_hash: str | None,
) -> None:
    db.execute(
        '''
        UPDATE sync_state
        SET backfill_next_row = ?,
            backfill_headers_hash = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE sync_key = ?
        ''',
        (next_row, headers_hash, sync_key)
    )


def count_rows(manager: GoogleSheetsManager, sheet_id: str, sheet_name: str) -> int:
    result = manager._execute_with_retry(
        manager.service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=manager._range_on_sheet(sheet_name, 'A:A')
        ),
        f"count rows for {sheet_id[:8]}:{sheet_name}"
    ) or {}
    values = result.get('values', [])
    return max(0, len(values) - 1)


def fetch_headers(manager: GoogleSheetsManager, sheet_id: str, sheet_name: str) -> List[str]:
    result = manager._execute_with_retry(
        manager.service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=manager._range_on_sheet(sheet_name, '1:1')
        ),
        f"read headers for {sheet_id[:8]}:{sheet_name}"
    ) or {}
    return result.get('values', [[]])[0]


def fetch_primary_phone_set(manager: GoogleSheetsManager) -> set[str]:
    sheet_id = manager.spreadsheet_id
    sheet_name = manager.primary_sheet_name
    headers = fetch_headers(manager, sheet_id, sheet_name)
    if not headers:
        return set()

    client_col = manager._find_client_column_in_headers(headers)
    col_letter = manager._col_to_letter(client_col)
    result = manager._execute_with_retry(
        manager.service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=manager._range_on_sheet(sheet_name, f"{col_letter}2:{col_letter}")
        ),
        f"read primary phones for {sheet_id[:8]}:{sheet_name}"
    ) or {}
    values = result.get('values', [])
    out: set[str] = set()
    for row in values:
        raw = row[0].strip() if row and row[0] is not None else ''
        norm = manager._normalize_phone(raw)
        if norm:
            out.add(norm)
    return out


def sync_one_batch(
    manager: GoogleSheetsManager,
    sheet_id: str,
    sheet_name: str,
    start_row: int,
    batch_size: int,
    primary_phones: set[str] | None = None,
    headers: List[str] | None = None,
    db_conn: sqlite3.Connection | None = None,
) -> Tuple[int, int, bool]:
    headers = headers if headers is not None else fetch_headers(manager, sheet_id, sheet_name)
    if not headers:
        logger.warning("⚠️ No headers found for %s:%s", sheet_id[:8], sheet_name)
        return 0, start_row, True

    client_col = manager._find_client_column_in_headers(headers)
    last_col = manager._col_to_letter(max(0, len(headers) - 1))
    end_row = start_row + batch_size - 1

    result = manager._execute_with_retry(
        manager.service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=manager._range_on_sheet(sheet_name, f"A{start_row}:{last_col}{end_row}")
        ),
        f"sync rows {start_row}-{end_row} from {sheet_id[:8]}:{sheet_name}"
    ) or {}
    values = result.get('values', [])
    if not values:
        return 0, start_row, True

    batch_rows: List[Tuple[str, str, Dict[str, str], str, str, int]] = []
    for row_num, row in enumerate(values, start=start_row):
        record: Dict[str, str] = {}
        for i, header in enumerate(headers):
            record[header] = row[i].strip() if i < len(row) and row[i] is not None else ''
        raw_phone = row[client_col].strip() if client_col < len(row) and row[client_col] is not None else ''
        normalized_phone = manager._normalize_phone(raw_phone)
        if normalized_phone:
            # Never let archive overwrite the primary source in the local cache.
            if primary_phones and sheet_id != manager.spreadsheet_id and normalized_phone in primary_phones:
                continue
            batch_rows.append((normalized_phone, raw_phone, record, sheet_id, sheet_name, row_num))

    imported = bulk_upsert_rows(db_conn, batch_rows) if db_conn is not None else manager.local_db.bulk_upsert(batch_rows)
    next_row = start_row + len(values)
    finished = len(values) < batch_size
    return imported, next_row, finished


def bulk_upsert_rows(
    conn: sqlite3.Connection,
    rows: List[Tuple[str, str, Dict[str, str], str, str, int]],
) -> int:
    payload = [
        (
            normalized_phone,
            raw_phone,
            json.dumps(record, ensure_ascii=False),
            sheet_id,
            sheet_name,
            row_num,
        )
        for normalized_phone, raw_phone, record, sheet_id, sheet_name, row_num in rows
        if normalized_phone and record
    ]
    if not payload:
        return 0
    conn.executemany(
        '''
        INSERT INTO client_records (
            normalized_phone,
            raw_phone,
            payload_json,
            sheet_id,
            sheet_name,
            row_num,
            updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(normalized_phone) DO UPDATE SET
            raw_phone=excluded.raw_phone,
            payload_json=excluded.payload_json,
            sheet_id=excluded.sheet_id,
            sheet_name=excluded.sheet_name,
            row_num=excluded.row_num,
            updated_at=excluded.updated_at
        ''',
        payload
    )
    return len(payload)


def print_status(manager: GoogleSheetsManager):
    with manager.local_db._connect() as conn:
        ensure_sync_state_table(conn)
        print(f"local_db_rows|{manager.local_db.get_total_clients()}")
        for sheet_id, sheet_name in manager.read_sources:
            sync_key = get_sync_key(sheet_id, sheet_name)
            state = get_sync_state(conn, sync_key)
            next_row = int(state["next_row"])
            total_rows = count_rows(manager, sheet_id, sheet_name)
            cached_rows = conn.execute(
                'SELECT COUNT(*) FROM client_records WHERE sheet_id = ? AND sheet_name = ?',
                (sheet_id, sheet_name)
            ).fetchone()[0]
            header_count = 0
            header_hash_short = ""
            try:
                headers = fetch_headers(manager, sheet_id, sheet_name)
                header_count = len(headers)
                header_hash_short = headers_signature(headers)[:12] if headers else ""
            except Exception:
                header_count = 0
            backfill_next_row = state.get("backfill_next_row")
            print(
                f"source|{sheet_id}|{sheet_name}|sheet_rows={total_rows}|cached_rows={cached_rows}|"
                f"next_row={next_row}|headers={header_count}|headers_hash={header_hash_short}|"
                f"backfill_next_row={backfill_next_row or ''}"
            )


def get_resume_row(
    conn: sqlite3.Connection,
    sheet_id: str,
    sheet_name: str,
    stored_next_row: int,
) -> int:
    if stored_next_row > 2:
        return stored_next_row

    cached_rows = conn.execute(
        'SELECT COUNT(*) FROM client_records WHERE sheet_id = ? AND sheet_name = ?',
        (sheet_id, sheet_name)
    ).fetchone()[0]
    if cached_rows <= 0:
        return stored_next_row

    # Resume close to the previous import position when legacy runs populated
    # the cache without storing sync_state.
    return cached_rows + 2


def run_incremental(
    manager: GoogleSheetsManager,
    batch_size: int,
    sleep_seconds: float,
    max_batches: int,
    force_resync: bool = False,
):
    with manager.local_db._connect() as conn:
        ensure_sync_state_table(conn)
        primary_phones = fetch_primary_phone_set(manager)
        batches = 0
        ordered_sources = sorted(
            manager.read_sources,
            key=lambda source: (source[0] != manager.spreadsheet_id, source[1], source[0])
        )
        for sheet_id, sheet_name in ordered_sources:
            sync_key = get_sync_key(sheet_id, sheet_name)
            headers = fetch_headers(manager, sheet_id, sheet_name)
            if not headers:
                logger.warning("⚠️ No headers found for %s:%s", sheet_id[:8], sheet_name)
                continue
            current_headers_hash = headers_signature(headers)
            total_rows = count_rows(manager, sheet_id, sheet_name)
            state = get_sync_state(conn, sync_key)
            stored_headers_hash = state.get("headers_hash")
            append_start_row = get_resume_row(conn, sheet_id, sheet_name, int(state["next_row"]))

            if force_resync:
                update_sync_metadata(conn, sync_key, total_rows, headers)
                set_backfill_state(conn, sync_key, 2, current_headers_hash)
                conn.commit()
                logger.warning(
                    "🔄 Forced resync requested for %s:%s; scheduling historical backfill from row 2",
                    sheet_id[:8],
                    sheet_name,
                )
            elif stored_headers_hash and stored_headers_hash != current_headers_hash:
                update_sync_metadata(conn, sync_key, total_rows, headers)
                if state.get("backfill_headers_hash") != current_headers_hash:
                    set_backfill_state(conn, sync_key, 2, current_headers_hash)
                    state["backfill_next_row"] = 2
                    state["backfill_headers_hash"] = current_headers_hash
                logger.warning(
                    "🔄 Header/column change detected for %s:%s; new rows stay prioritized, historical backfill starts at row 2",
                    sheet_id[:8],
                    sheet_name,
                )
            elif not stored_headers_hash:
                # Baseline metadata on first run after the migration without
                # forcing a 600k-row rebuild unless a real future change occurs.
                update_sync_state(conn, sync_key, append_start_row, total_rows, headers)
                conn.commit()

            state = get_sync_state(conn, sync_key)
            backfill_next_row = state.get("backfill_next_row")
            if append_start_row <= total_rows + 1:
                mode = "append"
                start_row = append_start_row
            elif backfill_next_row and int(backfill_next_row) <= total_rows + 1:
                mode = "backfill"
                start_row = int(backfill_next_row)
            else:
                logger.info("✅ Source already synced: %s:%s", sheet_id[:8], sheet_name)
                update_sync_state(conn, sync_key, append_start_row, total_rows, headers)
                if backfill_next_row and int(backfill_next_row) > total_rows + 1:
                    set_backfill_state(conn, sync_key, None, None)
                conn.commit()
                continue

            while batches < max_batches:
                imported, next_row, finished = sync_one_batch(
                    manager,
                    sheet_id,
                    sheet_name,
                    start_row,
                    batch_size,
                    primary_phones=primary_phones,
                    headers=headers,
                    db_conn=conn,
                )
                if mode == "append":
                    update_sync_state(conn, sync_key, next_row, total_rows, headers)
                else:
                    update_sync_metadata(conn, sync_key, total_rows, headers)
                    if finished or next_row > total_rows + 1:
                        set_backfill_state(conn, sync_key, None, None)
                    else:
                        set_backfill_state(conn, sync_key, next_row, current_headers_hash)
                conn.commit()
                batches += 1
                logger.info(
                    "✅ Incremental sync | mode=%s | source=%s:%s | imported=%s | next_row=%s | total_rows=%s | batch=%s/%s",
                    mode,
                    sheet_id[:8],
                    sheet_name,
                    imported,
                    next_row,
                    total_rows,
                    batches,
                    max_batches
                )
                if finished:
                    logger.info("✅ Completed source sync for %s:%s", sheet_id[:8], sheet_name)
                    break
                start_row = next_row
                time.sleep(sleep_seconds)

                if batches >= max_batches:
                    break


def main():
    parser = argparse.ArgumentParser(description="Incremental Google Sheets -> SQLite sync")
    parser.add_argument('--status', action='store_true', help='Show current sync status')
    parser.add_argument('--batch-size', type=int, default=1000, help='Rows per batch')
    parser.add_argument('--sleep-seconds', type=float, default=2.0, help='Pause between batches')
    parser.add_argument('--max-batches', type=int, default=10, help='Maximum batches per run')
    parser.add_argument(
        '--force-resync',
        action='store_true',
        help='Restart all configured sources at row 2 and backfill in batches'
    )
    args = parser.parse_args()

    manager = GoogleSheetsManager()
    if args.status:
        print_status(manager)
        return

    run_incremental(
        manager,
        batch_size=max(100, args.batch_size),
        sleep_seconds=max(0.0, args.sleep_seconds),
        max_batches=max(1, args.max_batches),
        force_resync=args.force_resync,
    )
    print_status(manager)


if __name__ == "__main__":
    main()
