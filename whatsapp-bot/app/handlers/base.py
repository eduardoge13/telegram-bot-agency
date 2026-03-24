"""Abstract base handler for message handlers."""
from abc import ABC, abstractmethod
from app.session_store import ConversationSession
from app.businesses import BusinessConfig


class BaseHandler(ABC):
    """Abstract base class for message handlers.

    Each handler implements can_handle() to indicate if it should process the message,
    and handle() to process it and return a response string.
    """

    @abstractmethod
    async def can_handle(self, message: str, state: dict) -> bool:
        """Return True if this handler should process the given message."""
        ...

    @abstractmethod
    async def handle(
        self, message: str, session: ConversationSession, business: BusinessConfig
    ) -> str:
        """Process the message and return a response string."""
        ...
