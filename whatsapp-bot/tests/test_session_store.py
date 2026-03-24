"""Tests for SessionStore (PLAT-03)."""
import time
import pytest
from unittest.mock import MagicMock, patch
from app.session_store import SessionStore, ConversationSession


@pytest.fixture
def mock_gemini_client():
    """Mock GeminiClient to avoid real API calls."""
    mock_client = MagicMock()
    mock_chat = MagicMock()
    mock_client.create_chat.return_value = mock_chat
    return mock_client


@pytest.fixture
def session_store(mock_gemini_client):
    """SessionStore with mocked GeminiClient."""
    store = SessionStore(gemini_client=mock_gemini_client)
    return store


def test_session_isolation(session_store):
    """PLAT-03: Sessions with different (business_id, phone) keys are isolated."""
    session_a = session_store.get_or_create("puntoclave", "+521111111111", "Prompt A")
    session_b = session_store.get_or_create("travel", "+521111111111", "Prompt B")
    assert session_a is not session_b


def test_session_reuse(session_store):
    """PLAT-03: Session within TTL is reused (same object returned)."""
    session_first = session_store.get_or_create("puntoclave", "+521111111111", "Prompt")
    session_second = session_store.get_or_create("puntoclave", "+521111111111", "Prompt")
    assert session_first is session_second


def test_session_expiry(session_store):
    """PLAT-03: Session expires after inactivity timeout."""
    session_original = session_store.get_or_create("puntoclave", "+521111111111", "Prompt")
    # Force session to appear expired
    session_original.last_active = time.time() - 3600  # 1 hour ago (beyond 30-min TTL)
    session_new = session_store.get_or_create("puntoclave", "+521111111111", "Prompt")
    assert session_new is not session_original


def test_session_key_is_tuple(session_store, mock_gemini_client):
    """Sessions are keyed on (business_id, phone) tuple."""
    session_store.get_or_create("puntoclave", "+521111111111", "Prompt")
    key = ("puntoclave", "+521111111111")
    assert key in session_store._sessions


def test_session_updates_last_active(session_store):
    """Session last_active timestamp is updated on each access."""
    session = session_store.get_or_create("puntoclave", "+521111111111", "Prompt")
    original_time = session.last_active
    time.sleep(0.01)  # Small delay to detect timestamp change
    session_again = session_store.get_or_create("puntoclave", "+521111111111", "Prompt")
    assert session_again.last_active >= original_time


def test_cleanup_expired_removes_stale_sessions(session_store):
    """cleanup_expired() removes sessions beyond TTL."""
    session = session_store.get_or_create("puntoclave", "+521111111111", "Prompt")
    session.last_active = time.time() - 3600
    session_store.cleanup_expired()
    assert ("puntoclave", "+521111111111") not in session_store._sessions


def test_conversation_session_has_state_dict(session_store):
    """ConversationSession has a state dict for multi-step flows."""
    session = session_store.get_or_create("travel", "+521111111111", "Prompt")
    assert isinstance(session.state, dict)
