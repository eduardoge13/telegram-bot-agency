"""Tests for the message dispatcher — handler chain routing."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.dispatcher import dispatch
from app.businesses import BusinessConfig
from app.session_store import ConversationSession


# ── Fixtures ─────────────────────────────────────────────────────────────────

def make_session(state=None):
    mock_chat = MagicMock()
    mock_chat.send_message_async = AsyncMock(return_value=MagicMock(text="QA fallback response"))
    return ConversationSession(chat=mock_chat, state=state or {})


@pytest.fixture
def puntoclave_business():
    return BusinessConfig(
        business_id="puntoclave",
        twilio_number="whatsapp:+15005550006",
        system_prompt="Eres el asistente de Punto Clave MX.",
        sheets_id="test-sheet-id",
        handlers=["product", "order", "qa"],
    )


@pytest.fixture
def travel_business():
    return BusinessConfig(
        business_id="travel",
        twilio_number="whatsapp:+15005550007",
        system_prompt="Eres el asistente de viajes.",
        sheets_id=None,
        handlers=["flight", "qa"],
    )


# ── Dispatcher Tests ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_dispatcher_routes_product_for_puntoclave(puntoclave_business):
    """Product intent message routes to ProductHandler for puntoclave business."""
    session = make_session()
    mock_sheets_clients = {
        "puntoclave": MagicMock(search_product=AsyncMock(return_value=[
            {"nombre": "Laptop Dell", "precio": "18500", "disponible": "si"}
        ]))
    }
    mock_amadeus = None

    # ProductHandler.can_handle should return True for "precio" keyword
    with patch("app.dispatcher.ProductHandler") as MockProduct:
        mock_handler = MagicMock()
        mock_handler.can_handle = AsyncMock(return_value=True)
        mock_handler.handle = AsyncMock(return_value="Tenemos laptops disponibles")
        MockProduct.return_value = mock_handler

        reply = await dispatch(puntoclave_business, session, "¿cuánto cuesta la laptop?", mock_sheets_clients, mock_amadeus)

    assert reply == "Tenemos laptops disponibles"
    mock_handler.handle.assert_called_once()


@pytest.mark.asyncio
async def test_dispatcher_qa_fallback(puntoclave_business):
    """Generic message (no handler matches) falls through to QAHandler."""
    session = make_session()
    mock_sheets_clients = {"puntoclave": MagicMock(search_product=AsyncMock(return_value=[]))}
    mock_amadeus = None

    with patch("app.dispatcher.ProductHandler") as MockProduct, \
         patch("app.dispatcher.OrderHandler") as MockOrder, \
         patch("app.dispatcher.QAHandler") as MockQA:

        mock_product = MagicMock()
        mock_product.can_handle = AsyncMock(return_value=False)
        MockProduct.return_value = mock_product

        mock_order = MagicMock()
        mock_order.can_handle = AsyncMock(return_value=False)
        MockOrder.return_value = mock_order

        mock_qa = MagicMock()
        mock_qa.can_handle = AsyncMock(return_value=True)
        mock_qa.handle = AsyncMock(return_value="Respuesta general de QA")
        MockQA.return_value = mock_qa

        reply = await dispatch(puntoclave_business, session, "hola, ¿cómo están?", mock_sheets_clients, mock_amadeus)

    assert reply == "Respuesta general de QA"
    mock_qa.handle.assert_called_once()


@pytest.mark.asyncio
async def test_dispatcher_skips_disabled_handler(travel_business):
    """Travel business (handlers=['flight','qa']) does NOT instantiate ProductHandler."""
    session = make_session()
    mock_sheets_clients = {}
    mock_amadeus = MagicMock()

    with patch("app.dispatcher.ProductHandler") as MockProduct, \
         patch("app.dispatcher.FlightHandler") as MockFlight, \
         patch("app.dispatcher.QAHandler") as MockQA:

        mock_flight = MagicMock()
        mock_flight.can_handle = AsyncMock(return_value=False)
        mock_flight.handle = AsyncMock(return_value="Vuelo reply")
        MockFlight.return_value = mock_flight

        mock_qa = MagicMock()
        mock_qa.can_handle = AsyncMock(return_value=True)
        mock_qa.handle = AsyncMock(return_value="QA reply for travel")
        MockQA.return_value = mock_qa

        reply = await dispatch(travel_business, session, "¿tienen laptops?", mock_sheets_clients, mock_amadeus)

    # ProductHandler should NOT have been instantiated since travel business only has ["flight", "qa"]
    MockProduct.assert_not_called()
    assert reply == "QA reply for travel"


@pytest.mark.asyncio
async def test_dispatcher_routes_flight_for_travel(travel_business):
    """Flight intent message routes to FlightHandler for travel business."""
    session = make_session()
    mock_sheets_clients = {}
    mock_amadeus = MagicMock()

    with patch("app.dispatcher.FlightHandler") as MockFlight, \
         patch("app.dispatcher.QAHandler") as MockQA:

        mock_flight = MagicMock()
        mock_flight.can_handle = AsyncMock(return_value=True)
        mock_flight.handle = AsyncMock(return_value="¿De dónde sales?")
        MockFlight.return_value = mock_flight

        mock_qa = MagicMock()
        mock_qa.can_handle = AsyncMock(return_value=True)
        mock_qa.handle = AsyncMock(return_value="QA fallback")
        MockQA.return_value = mock_qa

        reply = await dispatch(travel_business, session, "quiero un vuelo a Cancún", mock_sheets_clients, mock_amadeus)

    assert reply == "¿De dónde sales?"
    mock_flight.handle.assert_called_once()
    # QA should NOT have been called since flight matched first
    mock_qa.handle.assert_not_called()


@pytest.mark.asyncio
async def test_dispatcher_iterates_handlers_in_order(puntoclave_business):
    """Dispatcher uses the first handler that can_handle — does not call subsequent handlers."""
    session = make_session()
    mock_sheets_clients = {"puntoclave": MagicMock(search_product=AsyncMock(return_value=[]))}
    mock_amadeus = None

    with patch("app.dispatcher.ProductHandler") as MockProduct, \
         patch("app.dispatcher.OrderHandler") as MockOrder, \
         patch("app.dispatcher.QAHandler") as MockQA:

        mock_product = MagicMock()
        mock_product.can_handle = AsyncMock(return_value=True)
        mock_product.handle = AsyncMock(return_value="Product handler reply")
        MockProduct.return_value = mock_product

        mock_order = MagicMock()
        mock_order.can_handle = AsyncMock(return_value=True)
        MockOrder.return_value = mock_order

        mock_qa = MagicMock()
        mock_qa.can_handle = AsyncMock(return_value=True)
        MockQA.return_value = mock_qa

        reply = await dispatch(puntoclave_business, session, "precio de laptop", mock_sheets_clients, mock_amadeus)

    assert reply == "Product handler reply"
    # OrderHandler.handle and QAHandler.handle should NOT have been called
    mock_order.handle.assert_not_called()
    mock_qa.handle.assert_not_called()
