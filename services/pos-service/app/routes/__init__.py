"""
POS API Routes
"""

from .orders import router as orders_router
from .payments import router as payments_router
from .receipts import router as receipts_router
from .tax import router as tax_router

__all__ = [
    "orders_router",
    "payments_router",
    "receipts_router",
    "tax_router",
]
