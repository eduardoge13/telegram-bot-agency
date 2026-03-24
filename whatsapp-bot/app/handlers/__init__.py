"""Handler package — exports all message handlers."""
from app.handlers.base import BaseHandler
from app.handlers.qa import QAHandler
from app.handlers.product import ProductHandler
from app.handlers.order import OrderHandler

__all__ = ["BaseHandler", "QAHandler", "ProductHandler", "OrderHandler"]

try:
    from app.handlers.flight import FlightHandler
    __all__.append("FlightHandler")
except ImportError:
    pass
