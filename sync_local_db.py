#!/usr/bin/env python3
"""Incremental sync from Google Sheets into the local SQLite cache."""

import argparse
import sqlite3
import time
from typing import Dict, List, Tuple

from bot_telegram_polling import GoogleSheetsManager, logger


def ensure_sync_state_table(db: sqlite3.Connection):
    db.execute(
        '''
        CREATE TABLE IF NOT EXISTS sync_state (
            sync_key TEXT PRIMARY KEY,
            next_row INTEGER NOT NULL,
            last_total_rows INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        '''
    )


def get_sync_key(sheet_id: str, sheet_name: str) -> str:
    return f"{sheet_id}:{sheet_name}"


def get_next_row(db: sqlite3.Connection, sync_key: str) -> int:
    row = db.execute(
        'SELECT next_row FROM sync_state WHERE sync_key = ?',
        (sync_key,)
    ).fetchone()
    return int(row[0]) if row else 2


def update_sync_state(db: sqlite3.Connection, sync_key: str, next_row: int, total_rows: int):
    db.execute(
        '''
        INSERT INTO sync_state(sync_key, next_row, last_total_rows, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(sync_key) DO UPDATE SET
            next_row = excluded.next_row,
            last_total_rows = excluded.last_total_rows,
            updated_at = CURRENT_TIMESTAMP
        ''',
        (sync_key, next_row, total_rows)
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
) -> Tuple[int, int, bool]:
    headers = fetch_headers(manager, sheet_id, sheet_name)
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

    imported = manager.local_db.bulk_upsert(batch_rows)
    next_row = start_row + len(values)
    finished = len(values) < batch_size
    return imported, next_row, finished


def print_status(manager: GoogleSheetsManager):
    with manager.local_db._connect() as conn:
        ensure_sync_state_table(conn)
        print(f"local_db_rows|{manager.local_db.get_total_clients()}")
        for sheet_id, sheet_name in manager.read_sources:
            sync_key = get_sync_key(sheet_id, sheet_name)
            next_row = get_next_row(conn, sync_key)
            total_rows = count_rows(manager, sheet_id, sheet_name)
            cached_rows = conn.execute(
                'SELECT COUNT(*) FROM client_records WHERE sheet_id = ? AND sheet_name = ?',
                (sheet_id, sheet_name)
            ).fetchone()[0]
            print(
                f"source|{sheet_id}|{sheet_name}|sheet_rows={total_rows}|cached_rows={cached_rows}|next_row={next_row}"
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


def run_incremental(manager: GoogleSheetsManager, batch_size: int, sleep_seconds: float, max_batches: int):
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
            total_rows = count_rows(manager, sheet_id, sheet_name)
            start_row = get_resume_row(conn, sheet_id, sheet_name, get_next_row(conn, sync_key))
            if start_row > total_rows + 1:
                logger.info("✅ Source already synced: %s:%s", sheet_id[:8], sheet_name)
                continue

            while batches < max_batches:
                imported, next_row, finished = sync_one_batch(
                    manager,
                    sheet_id,
                    sheet_name,
                    start_row,
                    batch_size,
                    primary_phones=primary_phones,
                )
                update_sync_state(conn, sync_key, next_row, total_rows)
                conn.commit()
                batches += 1
                logger.info(
                    "✅ Incremental sync | source=%s:%s | imported=%s | next_row=%s | total_rows=%s | batch=%s/%s",
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
    args = parser.parse_args()

    manager = GoogleSheetsManager()
    if args.status:
        print_status(manager)
        return

    run_incremental(
        manager,
        batch_size=max(100, args.batch_size),
        sleep_seconds=max(0.0, args.sleep_seconds),
        max_batches=max(1, args.max_batches)
    )
    print_status(manager)


if __name__ == "__main__":
    main()
