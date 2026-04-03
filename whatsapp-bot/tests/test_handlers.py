"""Tests for ProductHandler, OrderHandler — conversational product/order flow."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.handlers.product import ProductHandler
from app.handlers.order import OrderHandler
from app.session_store import ConversationSession
from app.businesses import BusinessConfig


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def puntoclave_business():
    return BusinessConfig(
        business_id="puntoclave",
        phone_number_id="123456789012345",
        system_prompt="Eres el asistente de Punto Clave MX.",
        sheets_id="test-sheet-id",
        handlers=["product", "order", "qa"],
    )


@pytest.fixture
def travel_business():
    return BusinessConfig(
        business_id="travel",
        phone_number_id="987654321098765",
        system_prompt="Eres el asistente de viajes.",
        sheets_id=None,
        handlers=["flight", "qa"],
    )


def make_session(state=None):
    """Create a mock ConversationSession with optional state."""
    mock_chat = MagicMock()
    mock_chat.send_message_async = AsyncMock(return_value=MagicMock(text="Respuesta de Gemini"))
    return ConversationSession(chat=mock_chat, state=state or {})


def make_mock_sheets_client(products=None):
    """Create a mock ProductSheetsClient."""
    client = MagicMock()
    client.search_product = AsyncMock(return_value=products or [])
    return client


# ── ProductHandler Tests ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_product_handler_can_handle_product_keywords():
    """ProductHandler.can_handle returns True for product-related Spanish messages."""
    mock_sheets = make_mock_sheets_client()
    handler = ProductHandler(sheets_client=mock_sheets)

    assert await handler.can_handle("¿cuánto cuesta la laptop?", {}) is True
    assert await handler.can_handle("¿tienen monitores disponibles?", {}) is True
    assert await handler.can_handle("quiero comprar un mouse", {}) is True
    assert await handler.can_handle("busco teclados", {}) is True


@pytest.mark.asyncio
async def test_product_handler_can_handle_false_for_generic():
    """ProductHandler.can_handle returns False for non-product messages."""
    mock_sheets = make_mock_sheets_client()
    handler = ProductHandler(sheets_client=mock_sheets)

    assert await handler.can_handle("hola, ¿cómo están?", {}) is False
    assert await handler.can_handle("gracias", {}) is False


@pytest.mark.asyncio
async def test_product_handler_output_includes_pricing(puntoclave_business):
    """ProductHandler.handle sends product data to Gemini and returns conversational response."""
    products = [
        {"nombre": "Laptop Dell Inspiron 15", "precio": "18500", "disponible": "si"},
    ]
    mock_sheets = make_mock_sheets_client(products=products)
    mock_chat = MagicMock()
    mock_chat.send_message_async = AsyncMock(
        return_value=MagicMock(text="La Laptop Dell Inspiron 15 está a $18,500 MXN y sí la tenemos disponible. ¿Te gustaría hacer un pedido?")
    )
    session = ConversationSession(chat=mock_chat, state={})

    handler = ProductHandler(sheets_client=mock_sheets)
    reply = await handler.handle("quiero una laptop", session, puntoclave_business)

    # Gemini was called (not an empty reply)
    assert mock_chat.send_message_async.called
    # The prompt sent to Gemini should include the product data
    call_args = mock_chat.send_message_async.call_args[0][0]
    assert "18500" in call_args or "Laptop Dell Inspiron 15" in call_args


@pytest.mark.asyncio
async def test_product_handler_suggests_similar_when_no_match(puntoclave_business):
    """When no exact match, handler still sends a message to Gemini with guidance."""
    mock_sheets = make_mock_sheets_client(products=[])
    mock_chat = MagicMock()
    mock_chat.send_message_async = AsyncMock(
        return_value=MagicMock(text="No encontré ese producto exacto, ¿buscas algo diferente?")
    )
    session = ConversationSession(chat=mock_chat, state={})

    handler = ProductHandler(sheets_client=mock_sheets)
    reply = await handler.handle("quiero un dron", session, puntoclave_business)

    assert mock_chat.send_message_async.called
    assert len(reply) > 0


# ── OrderHandler Tests ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_order_handler_can_handle_order_keywords():
    """OrderHandler.can_handle returns True for order-related messages."""
    handler = OrderHandler()

    assert await handler.can_handle("quiero pedir una laptop", {}) is True
    assert await handler.can_handle("hacer un pedido", {}) is True


@pytest.mark.asyncio
async def test_order_handler_can_handle_order_flow_state():
    """OrderHandler.can_handle returns True when order_flow=True in state."""
    handler = OrderHandler()

    assert await handler.can_handle("Juan García", {"order_flow": True, "order_step": "name"}) is True


@pytest.mark.asyncio
async def test_order_handler_collect_name(puntoclave_business):
    """OrderHandler starts by asking for customer name."""
    handler = OrderHandler()
    session = make_session()

    reply = await handler.handle("quiero pedir", session, puntoclave_business)

    assert "nombre" in reply.lower() or "llamas" in reply.lower() or "nombre" in reply.lower()
    assert session.state.get("order_step") == "name"
    assert session.state.get("order_flow") is True


@pytest.mark.asyncio
async def test_order_handler_collect_product(puntoclave_business):
    """OrderHandler step 2: stores name, asks for product."""
    handler = OrderHandler()
    session = make_session(state={"order_flow": True, "order_step": "name"})

    reply = await handler.handle("Juan García", session, puntoclave_business)

    assert session.state.get("order_name") == "Juan García"
    assert session.state.get("order_step") == "product"
    assert "producto" in reply.lower() or "qué" in reply.lower() or "deseas" in reply.lower()


@pytest.mark.asyncio
async def test_order_handler_collect_quantity(puntoclave_business):
    """OrderHandler step 3: stores product, asks for quantity."""
    handler = OrderHandler()
    session = make_session(state={"order_flow": True, "order_step": "product", "order_name": "Juan"})

    reply = await handler.handle("Laptop Dell Inspiron", session, puntoclave_business)

    assert session.state.get("order_product") == "Laptop Dell Inspiron"
    assert session.state.get("order_step") == "quantity"
    assert "cuántas" in reply.lower() or "cantidad" in reply.lower() or "unidades" in reply.lower()


@pytest.mark.asyncio
async def test_order_handler_complete_order_clears_state(puntoclave_business):
    """OrderHandler step 4: finalizes order and clears state."""
    mock_sheets = MagicMock()
    mock_sheets.append_order = AsyncMock(return_value=None)

    handler = OrderHandler(sheets_client=mock_sheets)
    session = make_session(state={
        "order_flow": True,
        "order_step": "quantity",
        "order_name": "Juan García",
        "order_product": "Laptop Dell",
    })

    reply = await handler.handle("1", session, puntoclave_business)

    # State should be cleared after order is complete
    assert session.state.get("order_flow") is None or session.state.get("order_flow") is False
    assert session.state.get("order_step") is None
    # Confirmation message
    assert "pedido" in reply.lower() or "recibido" in reply.lower() or "gracias" in reply.lower()
