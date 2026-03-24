"""
Amadeus flight-offers integration.

Adapted from flights-price-panel/app/providers/amadeus.py.
Key change: replaced pydantic-settings `get_settings()` call with direct os.environ reads
so this module has no dependency on flights-price-panel's config module.

Uses the Amadeus Self-Service REST API v2.
Docs: https://developers.amadeus.com/self-service/category/flights/api-doc/flight-offers-search
"""

import logging
import os
import re
from datetime import date, datetime, timezone

import httpx

from app.providers.base import FlightOfferData, FlightProvider, SearchResult

logger = logging.getLogger(__name__)


def _parse_duration(iso_duration: str | None) -> str | None:
    """Convert ISO 8601 duration (e.g., 'PT15H30M') to readable format (e.g., '15h 30m')."""
    if not iso_duration:
        return None

    # Parse PT format: PT[n]H[n]M[n]S
    pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
    match = re.match(pattern, iso_duration)

    if not match:
        return iso_duration

    hours, minutes, seconds = match.groups()
    parts = []

    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if seconds and int(seconds) > 0:
        parts.append(f"{seconds}s")

    return " ".join(parts) if parts else "0m"


class AmadeusProvider(FlightProvider):
    """Concrete provider for the Amadeus Flight Offers Search API.

    Reads credentials from environment variables directly:
        AMADEUS_CLIENT_ID     — Amadeus API client ID
        AMADEUS_CLIENT_SECRET — Amadeus API client secret
        AMADEUS_BASE_URL      — (optional) defaults to https://test.api.amadeus.com
    """

    def __init__(self) -> None:
        self._client_id = os.environ["AMADEUS_CLIENT_ID"]
        self._client_secret = os.environ["AMADEUS_CLIENT_SECRET"]
        self._base_url = os.environ.get("AMADEUS_BASE_URL", "https://test.api.amadeus.com")
        self._token: str | None = None
        self._token_expires: datetime | None = None
        self._http = httpx.AsyncClient(timeout=30)

    # ── Authentication ────────────────────────────────────────────────────────

    async def authenticate(self) -> None:
        """Obtain an OAuth2 bearer token from Amadeus."""
        if self._token and self._token_expires and datetime.now(timezone.utc) < self._token_expires:
            return  # token still valid

        url = f"{self._base_url}/v1/security/oauth2/token"
        payload = {
            "grant_type": "client_credentials",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        }
        resp = await self._http.post(url, data=payload)
        resp.raise_for_status()
        data = resp.json()

        self._token = data["access_token"]
        expires_in = data.get("expires_in", 1799)
        self._token_expires = datetime.now(timezone.utc).__add__(
            __import__("datetime").timedelta(seconds=expires_in - 60)
        )
        logger.info("Amadeus token refreshed, expires in %s s", expires_in)

    # ── Flight Search ─────────────────────────────────────────────────────────

    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        adults: int = 1,
        max_results: int = 50,
    ) -> SearchResult:
        await self.authenticate()

        url = f"{self._base_url}/v2/shopping/flight-offers"
        params = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": departure_date.isoformat(),
            "adults": adults,
            "max": max_results,
            "currencyCode": "USD",
        }
        headers = {"Authorization": f"Bearer {self._token}"}

        resp = await self._http.get(url, params=params, headers=headers)
        resp.raise_for_status()
        raw = resp.json()

        offers = self._parse_offers(raw)
        logger.info(
            "Amadeus returned %d offers for %s->%s on %s",
            len(offers),
            origin,
            destination,
            departure_date,
        )

        return SearchResult(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            searched_at=datetime.now(timezone.utc),
            offers=offers,
            raw_response=raw,
        )

    # ── Health Check ──────────────────────────────────────────────────────────

    async def health_check(self) -> bool:
        try:
            await self.authenticate()
            return True
        except Exception:
            logger.exception("Amadeus health-check failed")
            return False

    # ── Parsing Helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _parse_offers(raw: dict) -> list[FlightOfferData]:
        offers: list[FlightOfferData] = []
        for item in raw.get("data", []):
            try:
                price = float(item["price"]["total"])
                currency = item["price"].get("currency", "USD")

                # First itinerary / first segment for departure, last for arrival
                itinerary = item["itineraries"][0]
                segments = itinerary["segments"]
                first_seg = segments[0]
                last_seg = segments[-1]

                offers.append(
                    FlightOfferData(
                        airline=first_seg["carrierCode"],
                        price=price,
                        currency=currency,
                        stops=len(segments) - 1,
                        departure_time=datetime.fromisoformat(first_seg["departure"]["at"]),
                        arrival_time=datetime.fromisoformat(last_seg["arrival"]["at"]),
                        duration=_parse_duration(itinerary.get("duration")),
                        raw_payload=item,
                    )
                )
            except (KeyError, IndexError, ValueError) as exc:
                logger.warning("Skipping malformed offer: %s", exc)
        return offers

    # ── Cleanup ───────────────────────────────────────────────────────────────

    async def close(self) -> None:
        await self._http.aclose()
