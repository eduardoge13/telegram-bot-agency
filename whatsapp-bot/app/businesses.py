"""Business registry: maps Twilio numbers to BusinessConfig instances."""
from dataclasses import dataclass, field


@dataclass
class BusinessConfig:
    """Configuration for a single business using the WhatsApp bot platform."""

    business_id: str
    twilio_number: str
    system_prompt: str
    sheets_id: str | None
    handlers: list[str]
    sheets_range: str = "Sheet1!A:D"
    language: str = "es"


BUSINESSES: dict[str, BusinessConfig] = {
    # Punto Clave MX — e-commerce (tech products)
    "whatsapp:+15005550006": BusinessConfig(
        business_id="puntoclave",
        twilio_number="whatsapp:+15005550006",
        system_prompt=(
            "Eres el asistente virtual de Punto Clave MX, una tienda en línea de productos tecnológicos en México. "
            "Responde siempre en español de manera amigable y conversacional, como si fuera una persona real. "
            "Cuando el cliente pregunte por un producto, menciona el precio como $X,XXX MXN y si está disponible. "
            "Después de compartir información de un producto, siempre pregunta: '¿Te gustaría hacer un pedido?'. "
            "Si el producto no está disponible o no lo encuentras, sugiere alternativas similares y ofrece "
            "conectar al cliente con un asesor humano. "
            "Mantén el contexto de la conversación para entender referencias como 'el otro' o 'ése'. "
            "No inventes precios ni disponibilidad — usa solo la información que tienes disponible."
        ),
        sheets_id=None,  # Will be replaced with real SPREADSHEET_ID
        handlers=["product", "order", "qa"],
    ),
    # Travel Agency — flight search (Amadeus API)
    "whatsapp:+15005550007": BusinessConfig(
        business_id="travel",
        twilio_number="whatsapp:+15005550007",
        system_prompt=(
            "Eres el asistente de viajes de una agencia de turismo en México. "
            "Responde siempre en español de manera profesional y amigable. "
            "Ayudas a los clientes a buscar vuelos al mejor precio. "
            "Para buscar vuelos, necesitas: ciudad de origen, ciudad de destino, fecha de salida y número de pasajeros. "
            "Guía al cliente paso a paso para obtener esta información si no la proporciona de una vez. "
            "Presenta las opciones de vuelo de forma clara: aerolínea, precio en MXN, número de escalas y duración. "
            "Siempre muestra las opciones más baratas primero (máximo 5 opciones). "
            "Usa códigos IATA para las ciudades (ej. MEX para Ciudad de México, CUN para Cancún)."
        ),
        sheets_id=None,
        handlers=["flight", "qa"],
    ),
}
