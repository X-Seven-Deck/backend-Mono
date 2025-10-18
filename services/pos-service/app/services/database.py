"""
Database Service Layer
Enterprise-grade database operations for POS
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from supabase import create_client, Client

from ..core.config import settings


class DatabaseService:
    """Centralized POS database operations"""
    
    def __init__(self):
        """Initialize Supabase client"""
        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
        
        self.client: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_KEY
        )
    
    # ========================================================================
    # ORDER OPERATIONS
    # ========================================================================
    
    async def create_order(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new order"""
        # Generate order number if not provided
        if "order_number" not in data:
            timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
            data["order_number"] = f"ORD-{timestamp}"
        
        result = self.client.table("orders").insert(data).execute()
        return result.data[0] if result.data else None
    
    async def create_order_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create order items in bulk"""
        result = self.client.table("order_items").insert(items).execute()
        return result.data
    
    async def get_order(self, order_id: UUID) -> Optional[Dict[str, Any]]:
        """Get order by ID"""
        result = self.client.table("orders").select("*").eq("id", str(order_id)).execute()
        return result.data[0] if result.data else None
    
    async def get_order_with_items(self, order_id: UUID) -> Optional[Dict[str, Any]]:
        """Get order with all items"""
        # Get order
        order_result = self.client.table("orders").select("*").eq("id", str(order_id)).execute()
        if not order_result.data:
            return None
        
        order = order_result.data[0]
        
        # Get order items
        items_result = self.client.table("order_items").select("*").eq("order_id", str(order_id)).execute()
        order["items"] = items_result.data
        
        # Get table info if exists
        if order.get("table_id"):
            table_result = self.client.table("tables").select("table_number").eq("id", order["table_id"]).execute()
            if table_result.data:
                order["table_number"] = table_result.data[0].get("table_number")
        
        return order
    
    async def get_orders(
        self,
        business_id: UUID,
        status: Optional[str] = None,
        table_id: Optional[UUID] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get orders with filtering"""
        query = self.client.table("orders").select("*").eq("business_id", str(business_id))
        
        if status:
            query = query.eq("status", status)
        if table_id:
            query = query.eq("table_id", str(table_id))
        
        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
        result = query.execute()
        return result.data
    
    async def get_active_orders(self, business_id: UUID) -> List[Dict[str, Any]]:
        """Get active orders (not completed or cancelled)"""
        query = self.client.table("orders").select("*").eq("business_id", str(business_id))
        query = query.in_("status", ["new", "confirmed", "preparing", "ready", "served"])
        query = query.order("created_at", desc=True)
        result = query.execute()
        return result.data
    
    async def update_order(self, order_id: UUID, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update order"""
        updates["updated_at"] = datetime.utcnow().isoformat()
        result = self.client.table("orders").update(updates).eq("id", str(order_id)).execute()
        return result.data[0] if result.data else None
    
    async def update_order_status(self, order_id: UUID, status: str) -> Dict[str, Any]:
        """Update order status"""
        return await self.update_order(order_id, {"status": status})
    
    async def calculate_order_totals(self, order_id: UUID) -> Dict[str, Decimal]:
        """Calculate order totals from items"""
        items_result = self.client.table("order_items").select("quantity, unit_price").eq("order_id", str(order_id)).execute()
        
        subtotal = Decimal("0")
        for item in items_result.data:
            quantity = Decimal(str(item["quantity"]))
            unit_price = Decimal(str(item["unit_price"]))
            subtotal += quantity * unit_price
        
        return {
            "subtotal": subtotal,
            "item_count": len(items_result.data)
        }
    
    # ========================================================================
    # PAYMENT OPERATIONS
    # ========================================================================
    
    async def create_payment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create payment record"""
        result = self.client.table("payments").insert(data).execute()
        return result.data[0] if result.data else None
    
    async def get_payment(self, payment_id: UUID) -> Optional[Dict[str, Any]]:
        """Get payment by ID"""
        result = self.client.table("payments").select("*").eq("id", str(payment_id)).execute()
        return result.data[0] if result.data else None
    
    async def get_payment_by_order(self, order_id: UUID) -> Optional[Dict[str, Any]]:
        """Get payment for order"""
        result = self.client.table("payments").select("*").eq("order_id", str(order_id)).execute()
        return result.data[0] if result.data else None
    
    async def update_payment(self, payment_id: UUID, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update payment"""
        result = self.client.table("payments").update(updates).eq("id", str(payment_id)).execute()
        return result.data[0] if result.data else None
    
    async def get_daily_payment_summary(
        self,
        business_id: UUID,
        date: datetime
    ) -> Dict[str, Any]:
        """Get daily payment summary"""
        start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        query = self.client.table("payments").select("payment_method, amount, tip_amount")
        query = query.eq("business_id", str(business_id))
        query = query.gte("created_at", start_date.isoformat())
        query = query.lte("created_at", end_date.isoformat())
        query = query.eq("status", "completed")
        
        result = query.execute()
        
        summary = {
            "cash": {"amount": Decimal("0"), "count": 0, "tips": Decimal("0")},
            "card": {"amount": Decimal("0"), "count": 0, "tips": Decimal("0")},
            "total": {"amount": Decimal("0"), "count": 0, "tips": Decimal("0")}
        }
        
        for payment in result.data:
            method = payment["payment_method"]
            amount = Decimal(str(payment["amount"]))
            tip = Decimal(str(payment.get("tip_amount", 0)))
            
            if method in summary:
                summary[method]["amount"] += amount
                summary[method]["count"] += 1
                summary[method]["tips"] += tip
            
            summary["total"]["amount"] += amount
            summary["total"]["count"] += 1
            summary["total"]["tips"] += tip
        
        return summary
    
    # ========================================================================
    # RECEIPT OPERATIONS
    # ========================================================================
    
    async def create_receipt(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create receipt"""
        result = self.client.table("receipts").insert(data).execute()
        return result.data[0] if result.data else None
    
    async def get_receipt(self, receipt_id: UUID) -> Optional[Dict[str, Any]]:
        """Get receipt by ID"""
        result = self.client.table("receipts").select("*").eq("id", str(receipt_id)).execute()
        return result.data[0] if result.data else None
    
    async def get_receipt_by_order(self, order_id: UUID) -> Optional[Dict[str, Any]]:
        """Get receipt for order"""
        result = self.client.table("receipts").select("*").eq("order_id", str(order_id)).execute()
        return result.data[0] if result.data else None
    
    # ========================================================================
    # TAX RULE OPERATIONS
    # ========================================================================
    
    async def create_tax_rule(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create tax rule"""
        result = self.client.table("tax_rules").insert(data).execute()
        return result.data[0] if result.data else None
    
    async def get_tax_rules(
        self,
        business_id: UUID,
        location_id: Optional[UUID] = None,
        is_active: bool = True
    ) -> List[Dict[str, Any]]:
        """Get tax rules"""
        query = self.client.table("tax_rules").select("*").eq("business_id", str(business_id))
        
        if location_id:
            query = query.eq("location_id", str(location_id))
        if is_active is not None:
            query = query.eq("is_active", is_active)
        
        result = query.execute()
        return result.data
    
    async def update_tax_rule(self, rule_id: UUID, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update tax rule"""
        result = self.client.table("tax_rules").update(updates).eq("id", str(rule_id)).execute()
        return result.data[0] if result.data else None
    
    # ========================================================================
    # MENU & TABLE OPERATIONS (Read-only from dashboard service)
    # ========================================================================
    
    async def get_menu_item(self, item_id: UUID) -> Optional[Dict[str, Any]]:
        """Get menu item"""
        result = self.client.table("menu_items").select("*").eq("id", str(item_id)).execute()
        return result.data[0] if result.data else None
    
    async def get_table(self, table_id: UUID) -> Optional[Dict[str, Any]]:
        """Get table"""
        result = self.client.table("tables").select("*").eq("id", str(table_id)).execute()
        return result.data[0] if result.data else None
    
    async def update_table_status(self, table_id: UUID, status: str, order_id: Optional[UUID] = None) -> Dict[str, Any]:
        """Update table status"""
        updates = {
            "status": status,
            "updated_at": datetime.utcnow().isoformat()
        }
        if order_id:
            updates["current_order_id"] = str(order_id)
        else:
            updates["current_order_id"] = None
        
        result = self.client.table("tables").update(updates).eq("id", str(table_id)).execute()
        return result.data[0] if result.data else None


# Singleton instance
_db_service: Optional[DatabaseService] = None


def get_database_service() -> DatabaseService:
    """Get database service singleton"""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service
