"""
Enhanced Supabase Service

Production-grade database operations with connection pooling, 
RLS support, and comprehensive CRUD operations.
"""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid

# Import shared Supabase client
import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
shared_path = os.path.join(project_root, 'shared')
sys.path.append(shared_path)

from libs.supabase_client import SupabaseManager
from app.config.settings import get_settings
from app.models.orders import Order, CreateOrderRequest, OrderStatus
from app.models.reservations import Reservation, CreateReservationRequest, ReservationStatus
from app.models.inventory import InventoryItem, InventoryTransaction
from app.models.payments import PaymentTransaction, PaymentRefund

logger = logging.getLogger(__name__)
settings = get_settings()


class SupabaseService:
    """
    Enhanced Supabase service for business logic operations
    
    Provides CRUD operations for:
    - Orders
    - Reservations
    - Inventory
    - Payments
    - Analytics
    """
    
    def __init__(self):
        self.db = SupabaseManager(use_service_key=True)
        logger.info("Supabase service initialized")
    
    # ========================================================================
    # ORDER OPERATIONS
    # ========================================================================
    
    async def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new order in database"""
        try:
            order_record = {
                "id": str(uuid.uuid4()),
                "business_id": order_data["business_id"],
                "customer_id": order_data["customer_id"],
                "order_number": order_data["order_number"],
                "status": order_data.get("status", OrderStatus.PENDING.value),
                "total_amount": float(order_data["total_amount"]),
                "currency": order_data.get("currency", "USD"),
                "items": order_data["items"],
                "metadata": order_data.get("metadata", {}),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = await self.db.insert("orders", order_record)
            logger.info(f"Order created: {order_record['order_number']}")
            return result[0] if result else {}
        
        except Exception as e:
            logger.error(f"Error creating order: {e}", exc_info=True)
            raise
    
    async def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order by ID"""
        try:
            result = await self.db.select(
                "orders",
                columns="*",
                filters={"id": order_id}
            )
            return result[0] if result else None
        
        except Exception as e:
            logger.error(f"Error getting order: {e}")
            return None
    
    async def update_order(
        self,
        order_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update order"""
        try:
            updates["updated_at"] = datetime.utcnow().isoformat()
            
            result = await self.db.update(
                "orders",
                data=updates,
                filters={"id": order_id}
            )
            
            logger.info(f"Order updated: {order_id}")
            return result[0] if result else None
        
        except Exception as e:
            logger.error(f"Error updating order: {e}")
            raise
    
    async def get_business_orders(
        self,
        business_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get orders for a business"""
        try:
            result = await self.db.select(
                "orders",
                columns="*",
                filters={"business_id": business_id}
            )
            return result[offset:offset+limit]
        
        except Exception as e:
            logger.error(f"Error getting business orders: {e}")
            return []
    
    # ========================================================================
    # RESERVATION OPERATIONS
    # ========================================================================
    
    async def create_reservation(
        self,
        reservation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create new reservation"""
        try:
            reservation_record = {
                "id": str(uuid.uuid4()),
                "business_id": reservation_data["business_id"],
                "customer_id": reservation_data["customer_id"],
                "reservation_number": reservation_data["reservation_number"],
                "status": reservation_data.get("status", ReservationStatus.PENDING.value),
                "reservation_date": reservation_data["reservation_date"],
                "party_size": reservation_data["party_size"],
                "notes": reservation_data.get("notes"),
                "metadata": reservation_data.get("metadata", {}),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = await self.db.insert("reservations", reservation_record)
            logger.info(f"Reservation created: {reservation_record['reservation_number']}")
            return result[0] if result else {}
        
        except Exception as e:
            logger.error(f"Error creating reservation: {e}", exc_info=True)
            raise
    
    async def get_reservation(self, reservation_id: str) -> Optional[Dict[str, Any]]:
        """Get reservation by ID"""
        try:
            result = await self.db.select(
                "reservations",
                columns="*",
                filters={"id": reservation_id}
            )
            return result[0] if result else None
        
        except Exception as e:
            logger.error(f"Error getting reservation: {e}")
            return None
    
    async def update_reservation(
        self,
        reservation_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update reservation"""
        try:
            updates["updated_at"] = datetime.utcnow().isoformat()
            
            result = await self.db.update(
                "reservations",
                data=updates,
                filters={"id": reservation_id}
            )
            
            logger.info(f"Reservation updated: {reservation_id}")
            return result[0] if result else None
        
        except Exception as e:
            logger.error(f"Error updating reservation: {e}")
            raise
    
    # ========================================================================
    # INVENTORY OPERATIONS
    # ========================================================================
    
    async def create_inventory_item(
        self,
        item_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create inventory item"""
        try:
            item_record = {
                "id": str(uuid.uuid4()),
                "business_id": item_data["business_id"],
                "name": item_data["name"],
                "sku": item_data.get("sku"),
                "unit": item_data["unit"],
                "current_stock": float(item_data["current_stock"]),
                "min_stock": float(item_data["min_stock"]),
                "unit_cost": float(item_data["unit_cost"]),
                "is_tracked": item_data.get("is_tracked", True),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = await self.db.insert("inventory_items", item_record)
            logger.info(f"Inventory item created: {item_record['name']}")
            return result[0] if result else {}
        
        except Exception as e:
            logger.error(f"Error creating inventory item: {e}")
            raise
    
    async def update_inventory_stock(
        self,
        item_id: str,
        quantity: float,
        transaction_type: str
    ) -> Dict[str, Any]:
        """Update inventory stock and create transaction"""
        try:
            # Get current item
            item = await self.db.select(
                "inventory_items",
                columns="*",
                filters={"id": item_id}
            )
            
            if not item:
                raise ValueError(f"Inventory item {item_id} not found")
            
            current_stock = item[0]["current_stock"]
            
            # Calculate new stock based on transaction type
            if transaction_type in ["purchase", "adjustment", "return"]:
                new_stock = current_stock + quantity
            elif transaction_type in ["sale", "waste"]:
                new_stock = current_stock - quantity
            else:
                new_stock = quantity  # For 'count' type
            
            # Update stock
            await self.db.update(
                "inventory_items",
                data={
                    "current_stock": new_stock,
                    "updated_at": datetime.utcnow().isoformat()
                },
                filters={"id": item_id}
            )
            
            # Create transaction record
            transaction = {
                "id": str(uuid.uuid4()),
                "business_id": item[0]["business_id"],
                "inventory_item_id": item_id,
                "transaction_type": transaction_type,
                "quantity": quantity,
                "created_at": datetime.utcnow().isoformat()
            }
            
            await self.db.insert("inventory_transactions", transaction)
            
            logger.info(f"Inventory updated: {item_id}, new stock: {new_stock}")
            return {
                "item_id": item_id,
                "previous_stock": current_stock,
                "new_stock": new_stock,
                "transaction_id": transaction["id"]
            }
        
        except Exception as e:
            logger.error(f"Error updating inventory: {e}")
            raise
    
    # ========================================================================
    # PAYMENT OPERATIONS
    # ========================================================================
    
    async def create_payment(
        self,
        payment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create payment transaction"""
        try:
            payment_record = {
                "id": str(uuid.uuid4()),
                "business_id": payment_data["business_id"],
                "transaction_id": payment_data["transaction_id"],
                "payment_method": payment_data["payment_method"],
                "amount": float(payment_data["amount"]),
                "status": payment_data.get("status", "pending"),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = await self.db.insert("payments", payment_record)
            logger.info(f"Payment created: {payment_record['transaction_id']}")
            return result[0] if result else {}
        
        except Exception as e:
            logger.error(f"Error creating payment: {e}")
            raise
    
    # ========================================================================
    # MENU OPERATIONS (Food & Hospitality)
    # ========================================================================
    
    async def get_menu_items(
        self,
        business_id: str,
        category_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get menu items for business"""
        try:
            filters = {"business_id": business_id}
            if category_id:
                filters["category_id"] = category_id
            
            result = await self.db.select(
                "menu_items",
                columns="*",
                filters=filters
            )
            return result
        
        except Exception as e:
            logger.error(f"Error getting menu items: {e}")
            return []
    
    # ========================================================================
    # TABLE OPERATIONS (Food & Hospitality)
    # ========================================================================
    
    async def get_tables(
        self,
        business_id: str,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get tables for business"""
        try:
            filters = {"business_id": business_id}
            if status:
                filters["status"] = status
            
            result = await self.db.select(
                "tables",
                columns="*",
                filters=filters
            )
            return result
        
        except Exception as e:
            logger.error(f"Error getting tables: {e}")
            return []
    
    async def update_table_status(
        self,
        table_id: str,
        status: str
    ) -> Optional[Dict[str, Any]]:
        """Update table status"""
        try:
            result = await self.db.update(
                "tables",
                data={
                    "status": status,
                    "updated_at": datetime.utcnow().isoformat()
                },
                filters={"id": table_id}
            )
            
            logger.info(f"Table status updated: {table_id} -> {status}")
            return result[0] if result else None
        
        except Exception as e:
            logger.error(f"Error updating table status: {e}")
            raise


# Singleton instance
_supabase_service: Optional[SupabaseService] = None


def get_supabase_service() -> SupabaseService:
    """Get Supabase service singleton"""
    global _supabase_service
    if _supabase_service is None:
        _supabase_service = SupabaseService()
    return _supabase_service
