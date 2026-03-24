"""ProductSheetsClient — Google Sheets product lookup with in-memory caching."""
import json
import os
import asyncio
import logging
import time
from typing import Any

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

_CACHE_TTL_SECONDS = 10 * 60  # 10-minute TTL


class ProductSheetsClient:
    """Reads product data from a Google Sheets spreadsheet with case-insensitive search.

    Credentials are read from GOOGLE_CREDENTIALS_JSON environment variable (service
    account JSON string). This avoids file-path credential management on VPS deployments.

    Sync Sheets API calls are wrapped in run_in_executor to avoid blocking the event loop
    (google-api-python-client is synchronous — per research pitfall #4).
    """

    READONLY_SCOPE = "https://www.googleapis.com/auth/spreadsheets.readonly"
    READWRITE_SCOPE = "https://www.googleapis.com/auth/spreadsheets"

    def __init__(
        self,
        spreadsheet_id: str,
        sheets_range: str = "Sheet1!A:D",
        credentials_json: str | None = None,
    ) -> None:
        self.spreadsheet_id = spreadsheet_id
        self.sheets_range = sheets_range

        creds_json = credentials_json or os.environ.get("GOOGLE_CREDENTIALS_JSON", "{}")
        creds = Credentials.from_service_account_info(
            json.loads(creds_json),
            scopes=[self.READWRITE_SCOPE],
        )
        self.service = build("sheets", "v4", credentials=creds, cache_discovery=False)

        # In-memory cache
        self._cache: list[dict] | None = None
        self._cache_time: float = 0

    # ── Public API ────────────────────────────────────────────────────────────

    async def search_product(self, query: str) -> list[dict]:
        """Async search for products matching query (case-insensitive substring on 'nombre')."""
        return await asyncio.get_event_loop().run_in_executor(
            None, self._fetch_and_search, query
        )

    async def append_order(
        self,
        name: str,
        product: str,
        quantity: str,
        phone: str,
        status: str = "Nuevo",
    ) -> None:
        """Append an order row to the 'Pedidos' sheet tab."""
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = [timestamp, name, product, quantity, phone, status]
        await asyncio.get_event_loop().run_in_executor(
            None, self._append_row, "Pedidos!A:F", row
        )

    # ── Sync helpers (run in executor) ────────────────────────────────────────

    def _fetch_and_search(self, query: str) -> list[dict]:
        """Fetch (or use cached) product rows and return substring matches."""
        rows = self._get_rows()
        if not rows:
            return []

        headers = rows[0]
        query_lower = query.lower()
        matches = []
        for row in rows[1:]:
            row_dict = dict(zip(headers, row))
            name = row_dict.get("nombre", "")
            if query_lower in name.lower():
                matches.append(row_dict)
        return matches

    def _get_rows(self) -> list[list]:
        """Return cached product rows or fetch fresh from Sheets."""
        now = time.time()
        if self._cache is not None and now - self._cache_time < _CACHE_TTL_SECONDS:
            return self._cache

        try:
            result = (
                self.service.spreadsheets()
                .values()
                .get(spreadsheetId=self.spreadsheet_id, range=self.sheets_range)
                .execute()
            )
            rows = result.get("values", [])
        except Exception:
            logger.exception("Failed to fetch product data from Sheets")
            rows = self._cache or []

        self._cache = rows
        self._cache_time = now
        return rows

    def _append_row(self, range_name: str, row: list) -> None:
        """Append a single row to the given Sheets range."""
        body = {"values": [row]}
        self.service.spreadsheets().values().append(
            spreadsheetId=self.spreadsheet_id,
            range=range_name,
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body=body,
        ).execute()

    # ── Formatting helpers ────────────────────────────────────────────────────

    @staticmethod
    def _format_price(price_str: str) -> str:
        """Format a price string as '$X,XXX MXN' with comma separators.

        Examples:
            "18500" -> "$18,500 MXN"
            "350"   -> "$350 MXN"
        """
        try:
            # Strip any existing formatting
            cleaned = price_str.replace(",", "").replace("$", "").replace("MXN", "").strip()
            price_int = int(float(cleaned))
            return f"${price_int:,} MXN"
        except (ValueError, TypeError):
            return f"${price_str} MXN"
