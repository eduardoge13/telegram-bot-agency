"""OrderHandler — multi-step order collection (name, product, quantity) → Sheets."""
import logging
from app.handlers.base import BaseHandler
from app.session_store import ConversationSession
from app.businesses import BusinessConfig

logger = logging.getLogger(__name__)

# Keywords that indicate ordering intent
ORDER_KEYWORDS = [
    "pedido", "pedir", "ordenar", "comprar", "quiero pedir",
    "hacer un pedido", "hacer pedido", "me interesa comprar",
    "quiero ordenar", "quisiera pedir",
]


class OrderHandler(BaseHandler):
    """Collects order info over multiple turns: name → product → quantity → confirmation.

    State is stored in session.state under 'order_flow', 'order_step', 'order_name',
    'order_product'. After completing the order, the data is written to a 'Pedidos' sheet
    tab and state is cleared.
    """

    def __init__(self, sheets_client=None) -> None:
        """Initialize with an optional ProductSheetsClient for writing orders."""
        self._sheets = sheets_client

    async def can_handle(self, message: str, state: dict) -> bool:
        """Return True if in an active order flow or message contains ordering intent."""
        if state.get("order_flow"):
            return True
        message_lower = message.lower()
        return any(kw in message_lower for kw in ORDER_KEYWORDS)

    async def handle(
        self, message: str, session: ConversationSession, business: BusinessConfig
    ) -> str:
        """Drive the multi-step order collection state machine."""
        state = session.state
        step = state.get("order_step")

        if step is None:
            # Step 1: Start order flow — ask for name
            state["order_flow"] = True
            state["order_step"] = "name"
            return "¡Claro! Con gusto tomo tu pedido. ¿Me puedes dar tu nombre completo?"

        elif step == "name":
            # Step 2: Store name, ask for product
            state["order_name"] = message.strip()
            state["order_step"] = "product"
            return f"Gracias, {state['order_name']}. ¿Qué producto deseas pedir?"

        elif step == "product":
            # Step 3: Store product, ask for quantity
            state["order_product"] = message.strip()
            state["order_step"] = "quantity"
            return f"Perfecto, *{state['order_product']}*. ¿Cuántas unidades necesitas?"

        elif step == "quantity":
            # Step 4: Store quantity, write to Sheets, confirm, clear state
            quantity = message.strip()
            name = state.get("order_name", "")
            product = state.get("order_product", "")
            phone = getattr(session, "_phone", "desconocido")

            # Write to Sheets (best-effort — don't lose the order if Sheets fails)
            if self._sheets is not None:
                try:
                    await self._sheets.append_order(
                        name=name,
                        product=product,
                        quantity=quantity,
                        phone=phone,
                        status="Nuevo",
                    )
                    logger.info("Order written to Sheets: %s - %s x%s", name, product, quantity)
                except Exception:
                    logger.exception(
                        "Failed to write order to Sheets (order not lost): %s - %s x%s",
                        name, product, quantity,
                    )

            # Clear order state
            for key in ["order_flow", "order_step", "order_name", "order_product"]:
                state.pop(key, None)

            return (
                f"¡Pedido recibido! 🎉\n\n"
                f"*Resumen del pedido:*\n"
                f"- Nombre: {name}\n"
                f"- Producto: {product}\n"
                f"- Cantidad: {quantity}\n\n"
                f"Nuestro equipo se pondrá en contacto contigo pronto para confirmar los detalles. "
                f"¡Gracias por tu compra!"
            )

        else:
            # Unknown step — reset
            state.clear()
            return "Lo siento, ocurrió un error con tu pedido. ¿Quieres intentarlo de nuevo?"
