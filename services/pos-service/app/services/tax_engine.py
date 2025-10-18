"""
Tax Calculation Engine
Location-based tax calculation with multiple tax types
"""

from typing import List, Optional, Dict
from uuid import UUID
from decimal import Decimal, ROUND_HALF_UP

from ..core.config import settings
from .database import DatabaseService, get_database_service


class TaxEngine:
    """Tax calculation engine"""
    
    def __init__(self, db_service: DatabaseService):
        self.db = db_service
    
    async def calculate_tax(
        self,
        business_id: UUID,
        subtotal: Decimal,
        location_id: Optional[UUID] = None
    ) -> Dict[str, Decimal]:
        """Calculate tax for order"""
        # Get applicable tax rules
        tax_rules = await self.db.get_tax_rules(
            business_id=business_id,
            location_id=location_id,
            is_active=True
        )
        
        if not tax_rules:
            # Use default tax rate if no rules found
            default_rate = Decimal(str(settings.DEFAULT_TAX_RATE))
            tax_amount = (subtotal * default_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            return {
                "tax_rate": default_rate,
                "tax_amount": tax_amount,
                "total_with_tax": subtotal + tax_amount,
                "tax_breakdown": {
                    "default": tax_amount
                }
            }
        
        # Calculate tax from rules
        total_tax = Decimal("0")
        tax_breakdown = {}
        combined_rate = Decimal("0")
        
        for rule in tax_rules:
            rate = Decimal(str(rule["rate"]))
            tax_for_rule = (subtotal * rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            total_tax += tax_for_rule
            combined_rate += rate
            tax_breakdown[rule["name"]] = tax_for_rule
        
        return {
            "tax_rate": combined_rate,
            "tax_amount": total_tax,
            "total_with_tax": subtotal + total_tax,
            "tax_breakdown": tax_breakdown
        }
    
    async def calculate_item_level_tax(
        self,
        business_id: UUID,
        items: List[Dict],
        location_id: Optional[UUID] = None
    ) -> Dict[str, Decimal]:
        """Calculate tax at item level (for future enhancement)"""
        # For now, calculate on total
        subtotal = sum(
            Decimal(str(item.get("quantity", 1))) * Decimal(str(item.get("unit_price", 0)))
            for item in items
        )
        
        return await self.calculate_tax(business_id, subtotal, location_id)
    
    def apply_discount(
        self,
        subtotal: Decimal,
        discount_amount: Decimal = Decimal("0"),
        discount_percent: Optional[Decimal] = None
    ) -> Decimal:
        """Apply discount to subtotal"""
        if discount_percent:
            discount_amount = (subtotal * discount_percent).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        discounted_total = subtotal - discount_amount
        return max(discounted_total, Decimal("0"))


# Singleton instance
_tax_engine: Optional[TaxEngine] = None


def get_tax_engine() -> TaxEngine:
    """Get tax engine singleton"""
    global _tax_engine
    if _tax_engine is None:
        db_service = get_database_service()
        _tax_engine = TaxEngine(db_service)
    return _tax_engine
