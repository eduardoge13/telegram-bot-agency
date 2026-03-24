"""Session store: manages per-(business_id, phone) conversation sessions with TTL expiry."""
import time
from dataclasses import dataclass, field
from app.gemini_client import GeminiClient


SESSION_TIMEOUT_SECONDS = 30 * 60  # 30 minutes of inactivity


@dataclass
class ConversationSession:
    """A single conversation session with a customer."""

    chat: object  # google.genai Chat object
    last_active: float = field(default_factory=time.time)
    state: dict = field(default_factory=dict)  # for multi-step flows (e.g. flight search)


class SessionStore:
    """In-memory store for conversation sessions, keyed on (business_id, phone)."""

    def __init__(self, gemini_client: GeminiClient):
        """Initialize with an injected GeminiClient (enables testing without real API)."""
        self._sessions: dict[tuple, ConversationSession] = {}
        self._gemini_client = gemini_client

    def get_or_create(
        self, business_id: str, phone: str, system_prompt: str
    ) -> ConversationSession:
        """Get an existing session or create a new one if expired/not found.

        Sessions are keyed on (business_id, phone) to isolate conversations
        across businesses with the same customer phone number.
        """
        key = (business_id, phone)
        session = self._sessions.get(key)

        # Expire session if beyond TTL
        if session is not None and time.time() - session.last_active > SESSION_TIMEOUT_SECONDS:
            del self._sessions[key]
            session = None

        if session is None:
            chat = self._gemini_client.create_chat(system_prompt)
            session = ConversationSession(chat=chat)
            self._sessions[key] = session

        session.last_active = time.time()
        return session

    def cleanup_expired(self) -> int:
        """Remove all sessions that have exceeded the TTL. Returns count removed."""
        now = time.time()
        expired_keys = [
            key
            for key, session in self._sessions.items()
            if now - session.last_active > SESSION_TIMEOUT_SECONDS
        ]
        for key in expired_keys:
            del self._sessions[key]
        return len(expired_keys)
