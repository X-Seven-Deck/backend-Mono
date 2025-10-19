"""
Offline Order Queue Routes
Support for offline order creation and synchronization
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field

from ..core.security import require_staff_role, get_current_business_id
from ..services.database import DatabaseService, get_database_service
from ..models.orders import OrderCreate, OrderResponse

router = APIRouter(prefix="/api/v1/pos/offline", tags=["Offline"])


class OfflineOrder(BaseModel):
    """Offline order with client-side ID"""
    client_id: str = Field(..., description="Client-generated unique ID")
    order: OrderCreate
    created_at_client: datetime = Field(..., description="Client timestamp")
    device_info: Dict[str, Any] = Field(default_factory=dict)


class OfflineOrderBatch(BaseModel):
    """Batch of offline orders for synchronization"""
    orders: List[OfflineOrder]


class SyncResult(BaseModel):
    """Synchronization result"""
    client_id: str
    server_id: str | None
    status: str  # 'success', 'failed', 'duplicate'
    error: str | None = None


class BatchSyncResponse(BaseModel):
    """Batch synchronization response"""
    results: List[SyncResult]
    total_count: int
    success_count: int
    failed_count: int
    duplicate_count: int


# In-memory storage for processed client IDs (should use Redis in production)
_processed_client_ids: Dict[str, str] = {}  # client_id -> server_id


@router.post("/orders/queue", response_model=dict)
async def queue_offline_order(
    offline_order: OfflineOrder,
    current_user: dict = Depends(require_staff_role),
    business_id: UUID = Depends(get_current_business_id),
    db: DatabaseService = Depends(get_database_service)
):
    """
    Queue an offline order for later synchronization
    
    This endpoint is called when the mobile app is offline and needs to queue orders.
    The order will be synchronized when connectivity is restored.
    """
    # Check if already processed (idempotency)
    if offline_order.client_id in _processed_client_ids:
        return {
            "status": "duplicate",
            "client_id": offline_order.client_id,
            "server_id": _processed_client_ids[offline_order.client_id],
            "message": "Order already synchronized"
        }
    
    try:
        # Process order immediately since we have connectivity
        from ..services.tax_engine import get_tax_engine
        from decimal import Decimal
        
        tax_engine = get_tax_engine()
        order = offline_order.order
        
        # Calculate subtotal
        subtotal = Decimal("0")
        for item in order.items:
            subtotal += item.quantity * item.unit_price
        
        # Calculate tax
        tax_calc = await tax_engine.calculate_tax(
            business_id=order.business_id,
            subtotal=subtotal,
            location_id=None
        )
        
        # Create order
        order_data = {
            "business_id": str(order.business_id),
            "table_id": str(order.table_id) if order.table_id else None,
            "customer_id": str(order.customer_id) if order.customer_id else None,
            "customer_count": order.customer_count,
            "notes": f"{order.notes or ''}\n[Offline Order - Synced]",
            "staff_id": current_user.get("user_id"),
            "status": "new",
            "subtotal": float(subtotal),
            "tax_amount": float(tax_calc["tax_amount"]),
            "discount_amount": 0,
            "total_amount": float(tax_calc["total_with_tax"])
        }
        
        created_order = await db.create_order(order_data)
        
        # Create order items
        order_items = []
        for item in order.items:
            menu_item = await db.get_menu_item(item.menu_item_id)
            order_items.append({
                "order_id": created_order["id"],
                "menu_item_id": str(item.menu_item_id),
                "name": menu_item["name"] if menu_item else "Unknown Item",
                "quantity": item.quantity,
                "unit_price": float(item.unit_price),
                "modifiers": item.modifiers,
                "special_instructions": item.special_instructions,
                "status": "pending"
            })
        
        await db.create_order_items(order_items)
        
        # Mark as processed
        _processed_client_ids[offline_order.client_id] = created_order["id"]
        
        # Broadcast real-time update
        from .websocket import broadcast_order_event
        await broadcast_order_event(
            business_id=str(order.business_id),
            event_type="order_created",
            order_data={
                "order_id": created_order["id"],
                "status": "new",
                "offline_sync": True
            }
        )
        
        return {
            "status": "success",
            "client_id": offline_order.client_id,
            "server_id": created_order["id"],
            "message": "Order synchronized successfully"
        }
        
    except Exception as e:
        return {
            "status": "failed",
            "client_id": offline_order.client_id,
            "error": str(e),
            "message": "Order synchronization failed"
        }


@router.post("/orders/batch-sync", response_model=BatchSyncResponse)
async def batch_sync_offline_orders(
    batch: OfflineOrderBatch,
    current_user: dict = Depends(require_staff_role),
    business_id: UUID = Depends(get_current_business_id),
    db: DatabaseService = Depends(get_database_service)
):
    """
    Synchronize a batch of offline orders
    
    This endpoint is called when the mobile app reconnects and needs to sync
    multiple queued orders.
    """
    results: List[SyncResult] = []
    success_count = 0
    failed_count = 0
    duplicate_count = 0
    
    for offline_order in batch.orders:
        # Check if already processed
        if offline_order.client_id in _processed_client_ids:
            results.append(SyncResult(
                client_id=offline_order.client_id,
                server_id=_processed_client_ids[offline_order.client_id],
                status="duplicate",
                error=None
            ))
            duplicate_count += 1
            continue
        
        try:
            # Process order
            from ..services.tax_engine import get_tax_engine
            from decimal import Decimal
            
            tax_engine = get_tax_engine()
            order = offline_order.order
            
            # Calculate subtotal
            subtotal = Decimal("0")
            for item in order.items:
                subtotal += item.quantity * item.unit_price
            
            # Calculate tax
            tax_calc = await tax_engine.calculate_tax(
                business_id=order.business_id,
                subtotal=subtotal,
                location_id=None
            )
            
            # Create order
            order_data = {
                "business_id": str(order.business_id),
                "table_id": str(order.table_id) if order.table_id else None,
                "customer_id": str(order.customer_id) if order.customer_id else None,
                "customer_count": order.customer_count,
                "notes": f"{order.notes or ''}\n[Offline Order - Batch Sync]",
                "staff_id": current_user.get("user_id"),
                "status": "new",
                "subtotal": float(subtotal),
                "tax_amount": float(tax_calc["tax_amount"]),
                "discount_amount": 0,
                "total_amount": float(tax_calc["total_with_tax"])
            }
            
            created_order = await db.create_order(order_data)
            
            # Create order items
            order_items = []
            for item in order.items:
                menu_item = await db.get_menu_item(item.menu_item_id)
                order_items.append({
                    "order_id": created_order["id"],
                    "menu_item_id": str(item.menu_item_id),
                    "name": menu_item["name"] if menu_item else "Unknown Item",
                    "quantity": item.quantity,
                    "unit_price": float(item.unit_price),
                    "modifiers": item.modifiers,
                    "special_instructions": item.special_instructions,
                    "status": "pending"
                })
            
            await db.create_order_items(order_items)
            
            # Mark as processed
            _processed_client_ids[offline_order.client_id] = created_order["id"]
            
            results.append(SyncResult(
                client_id=offline_order.client_id,
                server_id=created_order["id"],
                status="success",
                error=None
            ))
            success_count += 1
            
        except Exception as e:
            results.append(SyncResult(
                client_id=offline_order.client_id,
                server_id=None,
                status="failed",
                error=str(e)
            ))
            failed_count += 1
    
    return BatchSyncResponse(
        results=results,
        total_count=len(batch.orders),
        success_count=success_count,
        failed_count=failed_count,
        duplicate_count=duplicate_count
    )


@router.get("/orders/status/{client_id}")
async def check_offline_order_status(
    client_id: str,
    current_user: dict = Depends(require_staff_role)
):
    """Check if an offline order has been synchronized"""
    if client_id in _processed_client_ids:
        return {
            "client_id": client_id,
            "server_id": _processed_client_ids[client_id],
            "status": "synchronized"
        }
    else:
        return {
            "client_id": client_id,
            "server_id": None,
            "status": "pending"
        }
