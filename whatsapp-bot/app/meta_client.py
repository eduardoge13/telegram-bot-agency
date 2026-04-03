"""Meta WhatsApp Cloud API client."""
import re

import httpx


class MetaWhatsAppClient:
    """Send WhatsApp messages through the Meta Graph API."""

    def __init__(
        self,
        access_token: str,
        api_version: str = "v24.0",
        base_url: str = "https://graph.facebook.com",
    ):
        self._access_token = access_token
        self._api_version = api_version
        self._client = httpx.AsyncClient(base_url=base_url, timeout=20.0)

    async def send_text_message(self, phone_number_id: str, to: str, body: str) -> dict:
        """Send a plain text WhatsApp message."""
        if not self._access_token:
            raise RuntimeError("WHATSAPP_ACCESS_TOKEN is not configured")
        if not phone_number_id:
            raise ValueError("phone_number_id is required")

        normalized_to = re.sub(r"\D", "", to)
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": normalized_to,
            "type": "text",
            "text": {
                "body": body,
                "preview_url": False,
            },
        }
        response = await self._client.post(
            f"/{self._api_version}/{phone_number_id}/messages",
            headers={
                "Authorization": f"Bearer {self._access_token}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()
