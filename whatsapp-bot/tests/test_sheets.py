"""Tests for ProductSheetsClient — product search with mocked Sheets API."""
import pytest
from unittest.mock import MagicMock
from app.sheets.client import ProductSheetsClient


MOCK_SHEET_DATA = {
    "values": [
        ["nombre", "precio", "disponible", "descripcion"],
        ["Laptop Dell Inspiron 15", "18500", "si", "Laptop 15 pulgadas Intel i5"],
        ["Laptop HP Pavilion", "22000", "si", "Laptop 14 pulgadas AMD Ryzen 5"],
        ["Mouse Logitech M185", "350", "si", "Mouse inalámbrico compacto"],
        ["Teclado Mecánico Redragon", "1200", "no", "Teclado gaming RGB"],
        ["Monitor LG 24 pulgadas", "4500", "si", "Monitor IPS Full HD"],
    ]
}


def make_client(mock_service):
    """Helper to create a ProductSheetsClient with a mocked service (injected via _service)."""
    client = ProductSheetsClient(spreadsheet_id="test-sheet-id", _service=mock_service)
    return client


def test_product_search_returns_matching_products():
    """ProductSheetsClient.search_product returns matching products by name substring."""
    mock_service = MagicMock()
    mock_service.spreadsheets().values().get().execute.return_value = MOCK_SHEET_DATA
    client = make_client(mock_service)
    # Clear cache to force fresh fetch
    client._cache = None
    client._cache_time = 0

    results = client._fetch_and_search("laptop")

    assert len(results) == 2
    names = [r["nombre"] for r in results]
    assert "Laptop Dell Inspiron 15" in names
    assert "Laptop HP Pavilion" in names


def test_product_search_case_insensitive():
    """LAPTOP and laptop return the same results."""
    mock_service = MagicMock()
    mock_service.spreadsheets().values().get().execute.return_value = MOCK_SHEET_DATA
    client = make_client(mock_service)
    client._cache = None
    client._cache_time = 0

    results_lower = client._fetch_and_search("laptop")
    client._cache = None
    client._cache_time = 0
    mock_service.spreadsheets().values().get().execute.return_value = MOCK_SHEET_DATA
    results_upper = client._fetch_and_search("LAPTOP")

    assert len(results_lower) == len(results_upper)
    assert {r["nombre"] for r in results_lower} == {r["nombre"] for r in results_upper}


def test_product_search_no_match():
    """search_product returns empty list when no products match."""
    mock_service = MagicMock()
    mock_service.spreadsheets().values().get().execute.return_value = MOCK_SHEET_DATA
    client = make_client(mock_service)
    client._cache = None
    client._cache_time = 0

    results = client._fetch_and_search("xyznonexistent")

    assert results == []


def test_product_search_partial_match():
    """Partial name match works — 'mouse' matches 'Mouse Logitech M185'."""
    mock_service = MagicMock()
    mock_service.spreadsheets().values().get().execute.return_value = MOCK_SHEET_DATA
    client = make_client(mock_service)
    client._cache = None
    client._cache_time = 0

    results = client._fetch_and_search("mouse")

    assert len(results) == 1
    assert results[0]["nombre"] == "Mouse Logitech M185"


def test_format_price_with_comma_separators():
    """_format_price returns price in '$X,XXX MXN' format with comma separators."""
    mock_service = MagicMock()
    client = make_client(mock_service)

    assert client._format_price("18500") == "$18,500 MXN"
    assert client._format_price("350") == "$350 MXN"
    assert client._format_price("1200000") == "$1,200,000 MXN"
    assert client._format_price("22000") == "$22,000 MXN"


def test_cache_prevents_duplicate_api_calls():
    """Second call uses cached data — API is only called once."""
    mock_service = MagicMock()
    mock_service.spreadsheets().values().get().execute.return_value = MOCK_SHEET_DATA
    client = make_client(mock_service)
    client._cache = None
    client._cache_time = 0

    client._fetch_and_search("laptop")
    client._fetch_and_search("mouse")

    # The execute() should have been called only once (cache on second call)
    assert mock_service.spreadsheets().values().get().execute.call_count == 1
