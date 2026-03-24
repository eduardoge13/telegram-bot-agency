"""Message dispatcher — routes incoming messages to the correct handler chain."""
import logging
from app.businesses import BusinessConfig
from app.session_store import ConversationSession
from app.handlers.product import ProductHandler
from app.handlers.order import OrderHandler
from app.handlers.qa import QAHandler

logger = logging.getLogger(__name__)

try:
    from app.handlers.flight import FlightHandler
    _flight_available = True
except ImportError:
    _flight_available = False
    FlightHandler = None  # type: ignore[assignment,misc]


# Handler registry maps handler name strings to their factory functions.
# Each factory receives the shared dependencies and returns a BaseHandler instance.
# This indirection allows per-request instantiation with correct dependencies.
_HANDLER_NAMES = {"product", "order", "flight", "qa"}


async def dispatch(
    business: BusinessConfig,
    session: ConversationSession,
    message: str,
    sheets_clients: dict,
    amadeus_provider,
) -> str:
    """Route the message to the first handler in the business's handler chain that can handle it.

    Args:
        business: The BusinessConfig for the current conversation.
        session: The ConversationSession for (business_id, phone).
        message: The incoming message text.
        sheets_clients: Dict mapping business_id -> ProductSheetsClient instance.
        amadeus_provider: AmadeusProvider instance (or None if not configured).

    Returns:
        A response string from the matched handler.
    """
    sheets_client = sheets_clients.get(business.business_id)

    for handler_name in business.handlers:
        handler = _make_handler(handler_name, sheets_client, amadeus_provider)
        if handler is None:
            logger.warning("Unknown handler name: %s (skipping)", handler_name)
            continue

        try:
            if await handler.can_handle(message, session.state):
                return await handler.handle(message, session, business)
        except Exception:
            logger.exception("Handler %s raised an exception", handler_name)
            # Fall through to next handler

    # Safety net: if no handler matched (shouldn't happen since qa always returns True)
    response = await session.chat.send_message_async(message)
    return response.text


def _make_handler(name: str, sheets_client, amadeus_provider):
    """Instantiate a handler by name with its dependencies. Returns None for unknown names."""
    import app.dispatcher as _self_module

    if name == "product":
        return ProductHandler(sheets_client=sheets_client)
    elif name == "order":
        return OrderHandler(sheets_client=sheets_client)
    elif name == "flight":
        # Look up FlightHandler on the module so tests can patch it
        flight_cls = getattr(_self_module, "FlightHandler", None)
        if flight_cls is not None:
            return flight_cls(amadeus_provider=amadeus_provider)
        else:
            logger.warning("FlightHandler not available — skipping 'flight' handler")
            return None
    elif name == "qa":
        return QAHandler()
    else:
        return None
