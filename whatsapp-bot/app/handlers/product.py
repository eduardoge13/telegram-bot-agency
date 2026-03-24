"""ProductHandler — intent-based product lookup via Google Sheets + Gemini response."""
import logging
from app.handlers.base import BaseHandler
from app.session_store import ConversationSession
from app.businesses import BusinessConfig

logger = logging.getLogger(__name__)

# Spanish keywords that indicate product-related intent
PRODUCT_KEYWORDS = [
    "precio", "cuesta", "cuánto", "cuanto", "tienen", "tienen",
    "disponible", "disponibilidad", "producto", "busco", "quiero",
    "comprar", "compra", "venden", "vende", "laptop", "computadora",
    "monitor", "teclado", "mouse", "audifonos", "audífonos",
    "tablet", "celular", "teléfono", "impresora", "camara", "cámara",
    "consola", "juego", "accesorio", "cable", "cargador", "memoria",
    "disco", "usb", "pantalla", "bocina", "bocinas", "speaker",
]


class ProductHandler(BaseHandler):
    """Handles product inquiries by searching Sheets and generating a Gemini response.

    Intent detection is keyword-based (first-pass filter). Gemini handles nuance
    in the conversational response after product data is injected into the prompt.
    """

    def __init__(self, sheets_client) -> None:
        """Initialize with a ProductSheetsClient instance."""
        self._sheets = sheets_client

    async def can_handle(self, message: str, state: dict) -> bool:
        """Return True if the message contains any product-related keyword."""
        message_lower = message.lower()
        return any(kw in message_lower for kw in PRODUCT_KEYWORDS)

    async def handle(
        self, message: str, session: ConversationSession, business: BusinessConfig
    ) -> str:
        """Search products and inject results into a Gemini conversational prompt.

        If products found: includes product data (name, price, availability) in prompt.
        If no products found: guides Gemini to suggest alternatives or offer human handoff.
        """
        try:
            products = await self._sheets.search_product(message)
        except Exception:
            logger.exception("Sheets search failed for query: %s", message)
            products = []

        if products:
            formatted_products = self._format_products(products)
            gemini_prompt = (
                f"El cliente pregunta: '{message}'. "
                f"Productos encontrados en el catálogo: {formatted_products}. "
                f"Responde mencionando los productos con sus precios en formato $X,XXX MXN y disponibilidad "
                f"de forma conversacional. Pregunta si quiere hacer un pedido."
            )
        else:
            gemini_prompt = (
                f"El cliente pregunta por '{message}' pero no encontré productos similares en el catálogo. "
                f"Sugiere amablemente que el producto puede no estar disponible, "
                f"ofrece buscar algo diferente o conectar con un asesor humano."
            )

        try:
            response = await session.chat.send_message_async(gemini_prompt)
            return response.text
        except Exception:
            logger.exception("Gemini call failed in ProductHandler")
            return "Lo siento, no pude obtener la información del producto. Por favor intenta de nuevo."

    @staticmethod
    def _format_products(products: list[dict]) -> str:
        """Format a list of product dicts into a readable string for the Gemini prompt."""
        lines = []
        for p in products:
            name = p.get("nombre", "Producto")
            price_raw = p.get("precio", "")
            available = p.get("disponible", "")
            desc = p.get("descripcion", "")

            # Format price inline
            try:
                price_val = int(float(str(price_raw).replace(",", "").strip()))
                price_str = f"${price_val:,} MXN"
            except (ValueError, TypeError):
                price_str = f"${price_raw} MXN"

            avail_str = "disponible" if str(available).lower() in ("si", "sí", "yes", "1", "true") else "no disponible"
            line = f"{name} - {price_str} - {avail_str}"
            if desc:
                line += f" ({desc})"
            lines.append(line)
        return "; ".join(lines)
