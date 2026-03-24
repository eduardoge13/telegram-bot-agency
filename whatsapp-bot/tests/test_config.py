"""Tests for business registry (PLAT-01, PLAT-04)."""
import pytest
from app.businesses import BusinessConfig, BUSINESSES


def test_business_lookup():
    """PLAT-01: BUSINESSES dict resolves correct config by Twilio number."""
    config = BUSINESSES.get("whatsapp:+15005550006")
    assert config is not None
    assert isinstance(config, BusinessConfig)
    assert config.business_id == "puntoclave"
    assert config.handlers == ["product", "order", "qa"]


def test_business_lookup_unknown():
    """PLAT-01: Unknown Twilio number returns None."""
    config = BUSINESSES.get("whatsapp:+19999999999")
    assert config is None


def test_new_business_no_code_change():
    """PLAT-04: Adding a third entry to BUSINESSES makes it resolvable without code change."""
    # Add a third business dynamically — simulates what config-driven onboarding does
    test_number = "whatsapp:+15005550099"
    new_business = BusinessConfig(
        business_id="testbiz",
        twilio_number=test_number,
        system_prompt="Test system prompt",
        sheets_id=None,
        handlers=["qa"],
    )
    BUSINESSES[test_number] = new_business
    try:
        resolved = BUSINESSES.get(test_number)
        assert resolved is not None
        assert resolved.business_id == "testbiz"
    finally:
        # Clean up — don't pollute other tests
        del BUSINESSES[test_number]


def test_business_config_has_required_fields():
    """BusinessConfig dataclass has expected fields."""
    config = BUSINESSES.get("whatsapp:+15005550006")
    assert config is not None
    assert hasattr(config, "business_id")
    assert hasattr(config, "twilio_number")
    assert hasattr(config, "system_prompt")
    assert hasattr(config, "handlers")
    assert hasattr(config, "language")
    assert config.language == "es"


def test_travel_business_exists():
    """Travel agency business is configured."""
    config = BUSINESSES.get("whatsapp:+15005550007")
    assert config is not None
    assert config.business_id == "travel"
    assert "flight" in config.handlers
    assert "qa" in config.handlers
