"""QA handler: pure Gemini AI fallback for any message."""
from app.handlers.base import BaseHandler
from app.session_store import ConversationSession
from app.businesses import BusinessConfig


class QAHandler(BaseHandler):
    """Fallback handler that always handles any message via Gemini AI.

    Used as the last handler in the chain when no specialized handler matches.
    """

    async def can_handle(self, message: str, state: dict) -> bool:
        """Always returns True — this is the fallback handler."""
        return True

    async def handle(
        self, message: str, session: ConversationSession, business: BusinessConfig
    ) -> str:
        """Send message to Gemini AI and return the text response."""
        response = await session.chat.send_message_async(message)
        return response.text
