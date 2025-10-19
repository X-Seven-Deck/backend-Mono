"""
POS API Routes
"""

from .orders import router as orders_router
from .payments import router as payments_router
from .receipts import router as receipts_router
from .tax import router as tax_router
from .websocket import router as websocket_router
from .offline import router as offline_router
from .analytics import router as analytics_router
from .customers import router as customers_router

__all__ = [
    "orders_router",
    "payments_router",
    "receipts_router",
    "tax_router",
    "websocket_router",
    "offline_router",
    "analytics_router",
    "customers_router",
]
