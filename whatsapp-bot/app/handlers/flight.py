"""FlightHandler — guided step-by-step flight search via Amadeus API."""
import logging
import re
from datetime import date
from app.handlers.base import BaseHandler
from app.session_store import ConversationSession
from app.businesses import BusinessConfig

logger = logging.getLogger(__name__)

# Spanish keywords that indicate flight-search intent
FLIGHT_KEYWORDS = [
    "vuelo", "vuelos", "volar", "avion", "avión", "boleto", "boletos",
    "viaje", "viajes", "flight", "flights", "pasaje", "pasajes",
    "aerolinea", "aerolínea", "ticket", "salida", "destino",
]

# IATA city mapping for common Mexican cities and destinations
IATA_MAP = {
    "ciudad de mexico": "MEX",
    "ciudad de méxico": "MEX",
    "mexico": "MEX",
    "méxico": "MEX",
    "cdmx": "MEX",
    "df": "MEX",
    "guadalajara": "GDL",
    "monterrey": "MTY",
    "cancun": "CUN",
    "cancún": "CUN",
    "tijuana": "TIJ",
    "merida": "MID",
    "mérida": "MID",
    "puebla": "PBC",
    "oaxaca": "OAX",
    "los cabos": "SJD",
    "cabo san lucas": "SJD",
    "puerto vallarta": "PVR",
    "vallarta": "PVR",
    "leon": "BJX",
    "léon": "BJX",
    "queretaro": "QRO",
    "querétaro": "QRO",
    "mazatlan": "MZT",
    "mazatlán": "MZT",
    "hermosillo": "HMO",
    "chihuahua": "CUU",
    "acapulco": "ACA",
    "veracruz": "VER",
    "tampico": "TAM",
    "torreon": "TRC",
    "torreón": "TRC",
    # International common destinations from Mexico
    "miami": "MIA",
    "nueva york": "JFK",
    "new york": "JFK",
    "los angeles": "LAX",
    "chicago": "ORD",
    "houston": "IAH",
    "dallas": "DFW",
    "madrid": "MAD",
    "barcelona": "BCN",
    "bogota": "BOG",
    "bogotá": "BOG",
    "lima": "LIM",
    "buenos aires": "EZE",
    "miami": "MIA",
    "toronto": "YYZ",
    "london": "LHR",
    "londres": "LHR",
}

# Month names in Spanish to number mapping
SPANISH_MONTHS = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}


class FlightHandler(BaseHandler):
    """Guides customers through a step-by-step flight search: origin → destination → date → results.

    State is stored in session.state under 'flight_flow', 'flight_step', 'flight_origin',
    'flight_destination'. After presenting results, state is cleared.
    """

    def __init__(self, amadeus_provider=None) -> None:
        """Initialize with an AmadeusProvider instance."""
        self._amadeus = amadeus_provider

    async def can_handle(self, message: str, state: dict) -> bool:
        """Return True if in an active flight flow or message contains flight-related keywords."""
        if state.get("flight_flow"):
            return True
        message_lower = message.lower()
        return any(kw in message_lower for kw in FLIGHT_KEYWORDS)

    async def handle(
        self, message: str, session: ConversationSession, business: BusinessConfig
    ) -> str:
        """Drive the multi-step flight search state machine."""
        state = session.state
        step = state.get("flight_step")

        if step is None:
            # Step 0: Start flow — ask origin
            state["flight_flow"] = True
            state["flight_step"] = "origin"
            return "¡Con gusto te ayudo a buscar vuelos! ✈️\n¿De qué ciudad sales? (ej. Ciudad de México, Guadalajara, Monterrey)"

        elif step == "origin":
            # Step 1: Parse origin city → IATA, ask destination
            iata = self._city_to_iata(message)
            if iata is None:
                return (
                    f"No reconozco esa ciudad de origen. Por favor usa el nombre de la ciudad "
                    f"o el código IATA (ej. MEX, GDL, MTY). ¿De qué ciudad sales?"
                )
            state["flight_origin"] = iata
            state["flight_step"] = "destination"
            return f"Perfecto, saliendo de *{iata}*. ¿A qué ciudad vas?"

        elif step == "destination":
            # Step 2: Parse destination city → IATA, ask date
            iata = self._city_to_iata(message)
            if iata is None:
                return (
                    f"No reconozco esa ciudad de destino. Por favor usa el nombre de la ciudad "
                    f"o el código IATA. ¿A qué ciudad vas?"
                )
            state["flight_destination"] = iata
            state["flight_step"] = "date"
            return f"Viajando a *{iata}*. ¿Qué fecha de salida prefieres? (ej. 15 de abril, 2026-04-15)"

        elif step == "date":
            # Step 3: Parse date, search Amadeus, present results
            parsed_date = self._parse_date(message)
            if parsed_date is None:
                return (
                    "No pude interpretar esa fecha. Por favor usa un formato como "
                    "'15 de abril', 'abril 15', o '2026-04-15'. ¿Qué fecha de salida prefieres?"
                )

            origin = state.get("flight_origin", "MEX")
            destination = state.get("flight_destination", "CUN")

            # Clear state before the search (so errors don't leave partial state)
            for key in ["flight_flow", "flight_step", "flight_origin", "flight_destination"]:
                state.pop(key, None)

            return await self._search_and_format(origin, destination, parsed_date)

        else:
            # Unknown step — reset
            state.clear()
            return "Lo siento, ocurrió un error con la búsqueda. ¿Quieres intentarlo de nuevo? Dime 'vuelo' para empezar."

    async def _search_and_format(self, origin: str, destination: str, departure_date: date) -> str:
        """Call Amadeus and format the top results as a conversational reply."""
        if self._amadeus is None:
            return (
                "Lo siento, el servicio de búsqueda de vuelos no está disponible en este momento. "
                "Por favor contacta directamente a nuestra agencia."
            )

        try:
            result = await self._amadeus.search_flights(
                origin=origin,
                destination=destination,
                departure_date=departure_date,
                adults=1,
                max_results=10,
            )
        except Exception:
            logger.exception("Amadeus search failed: %s -> %s on %s", origin, destination, departure_date)
            return "No pude buscar vuelos en este momento. Por favor intenta de nuevo en unos minutos."

        if not result.offers:
            return (
                f"No encontré vuelos disponibles de {origin} a {destination} "
                f"para el {departure_date.strftime('%d de %B de %Y')}. "
                f"¿Quieres intentar con otra fecha o destino?"
            )

        # Sort by price and show top 5
        offers = sorted(result.offers, key=lambda o: o.price)[:5]
        lines = [
            f"Vuelos de *{origin}* a *{destination}* - {departure_date.strftime('%d/%m/%Y')}:\n"
        ]

        for i, offer in enumerate(offers, 1):
            # Convert USD price to MXN (approximate: 1 USD ≈ 17 MXN; use as display estimate)
            price_mxn = offer.price * 17
            stops_str = "Directo" if offer.stops == 0 else f"{offer.stops} escala{'s' if offer.stops > 1 else ''}"
            duration_str = f" - {offer.duration}" if offer.duration else ""
            lines.append(
                f"{i}. {offer.airline} — ${price_mxn:,.0f} MXN ({offer.price:.2f} USD) — {stops_str}{duration_str}"
            )

        lines.append("\n¿Te interesa alguna de estas opciones? ¿Quieres buscar con otra fecha?")
        return "\n".join(lines)

    @staticmethod
    def _city_to_iata(text: str) -> str | None:
        """Convert city name to IATA code. Returns None if not recognized.

        Checks if the text itself is already a 3-letter IATA code, then checks the mapping dict.
        """
        text_clean = text.strip().lower()

        # Already a 3-letter IATA code?
        if re.match(r'^[a-z]{3}$', text_clean):
            return text_clean.upper()

        # Lookup in mapping
        return IATA_MAP.get(text_clean)

    @staticmethod
    def _parse_date(text: str) -> date | None:
        """Parse a date from Spanish or ISO format text. Returns None if unparseable.

        Supported formats:
        - ISO: "2026-04-15"
        - Spanish: "15 de abril", "abril 15", "15 abril"
        - Numeric: "15/04/2026"
        """
        text = text.strip().lower()

        # ISO format: YYYY-MM-DD
        m = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', text)
        if m:
            try:
                return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            except ValueError:
                pass

        # DD/MM/YYYY or DD-MM-YYYY
        m = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', text)
        if m:
            try:
                return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
            except ValueError:
                pass

        # Spanish: "15 de abril" or "abril 15" or "15 abril"
        # Extract day and month name
        day_match = re.search(r'\b(\d{1,2})\b', text)
        month_match = None
        for month_name, month_num in SPANISH_MONTHS.items():
            if month_name in text:
                month_match = month_num
                break

        if day_match and month_match:
            day = int(day_match.group(1))
            month = month_match
            # Determine year: use current year, or next year if date has passed
            import datetime
            today = datetime.date.today()
            year = today.year
            try:
                candidate = date(year, month, day)
                if candidate < today:
                    candidate = date(year + 1, month, day)
                return candidate
            except ValueError:
                pass

        return None
