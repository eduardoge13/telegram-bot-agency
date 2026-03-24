"""
Abstract base class for flight data providers.
Prevents vendor lock-in by defining a common interface.

Copied from flights-price-panel/app/providers/base.py and kept identical.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any


@dataclass
class FlightOfferData:
    """Normalised flight offer returned by any provider."""

    airline: str
    price: float
    currency: str
    stops: int
    departure_time: datetime
    arrival_time: datetime
    duration: str | None = None
    cabin_class: str | None = None
    booking_class: str | None = None
    raw_payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResult:
    """Result of a single search request."""

    origin: str
    destination: str
    departure_date: date
    searched_at: datetime
    offers: list[FlightOfferData]
    raw_response: dict[str, Any] = field(default_factory=dict)


class FlightProvider(ABC):
    """
    Abstract flight data provider.

    Subclass this for every external API (Amadeus, Sabre, Duffel, …).
    """

    @abstractmethod
    async def authenticate(self) -> None:
        """Obtain or refresh API credentials."""
        ...

    @abstractmethod
    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        adults: int = 1,
        max_results: int = 50,
    ) -> SearchResult:
        """Search for flight offers on a given route + date."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if the provider API is reachable."""
        ...
