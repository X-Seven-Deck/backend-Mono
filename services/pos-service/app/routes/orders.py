"""
Order Management Routes
Enterprise-grade order API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from uuid import UUID
from decimal import Decimal

from ..models.orders import (
    OrderCreate,
    OrderUpdate,
    OrderResponse,
    OrderWithDetails,
    OrderSummary,
    OrderStatus
)
from ..core.security import get_current_user, get_current_business_id, require_staff_role
from ..services.database import DatabaseService, get_database_service
from ..services.tax_engine import TaxEngine, get_tax_engine

router = APIRouter(prefix="/api/v1/pos/orders", tags=["Orders"])


@router.post("/", response_model=OrderWithDetails, status_code=status.HTTP_201_CREATED)
async def create_order(
    order: OrderCreate,
    current_user: dict = Depends(require_staff_role),
    db: DatabaseService = Depends(get_database_service),
    tax_engine: TaxEngine = Depends(get_tax_engine)
):
    """Create new order with items"""
    try:
        # Validate business access
        if str(order.business_id) != current_user.get("business_id"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot create order for different business"
            )
        
        # Calculate subtotal from items
        subtotal = Decimal("0")
        for item in order.items:
            subtotal += item.quantity * item.unit_price
        
        # Calculate tax
        tax_calc = await tax_engine.calculate_tax(
            business_id=order.business_id,
            subtotal=subtotal,
            location_id=None  # TODO: Get from table location
        )
        
        # Create order
        order_data = {
            "business_id": str(order.business_id),
            "table_id": str(order.table_id) if order.table_id else None,
            "customer_id": str(order.customer_id) if order.customer_id else None,
            "customer_count": order.customer_count,
            "notes": order.notes,
            "staff_id": str(order.staff_id) if order.staff_id else current_user.get("user_id"),
            "status": OrderStatus.NEW.value,
            "subtotal": float(subtotal),
            "tax_amount": float(tax_calc["tax_amount"]),
            "discount_amount": 0,
            "total_amount": float(tax_calc["total_with_tax"])
        }
        
        created_order = await db.create_order(order_data)
        
        # Create order items
        order_items = []
        for item in order.items:
            # Get menu item details
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
        
        # Update table status if table assigned
        if order.table_id:
            await db.update_table_status(
                table_id=order.table_id,
                status="occupied",
                order_id=UUID(created_order["id"])
            )
        
        # Get complete order with items
        complete_order = await db.get_order_with_items(UUID(created_order["id"]))
        
        return OrderWithDetails(**complete_order)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create order: {str(e)}"
        )


@router.get("/{order_id}", response_model=OrderWithDetails)
async def get_order(
    order_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: DatabaseService = Depends(get_database_service)
):
    """Get order by ID with full details"""
    order = await db.get_order_with_items(order_id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found"
        )
    
    # Verify business access
    if order["business_id"] != current_user.get("business_id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return OrderWithDetails(**order)


@router.get("/", response_model=List[OrderResponse])
async def list_orders(
    status: Optional[OrderStatus] = None,
    table_id: Optional[UUID] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    business_id: UUID = Depends(get_current_business_id),
    db: DatabaseService = Depends(get_database_service)
):
    """List orders with filtering"""
    orders = await db.get_orders(
        business_id=business_id,
        status=status.value if status else None,
        table_id=table_id,
        limit=limit,
        offset=offset
    )
    
    return [OrderResponse(**order) for order in orders]


@router.get("/active/summary", response_model=List[OrderSummary])
async def get_active_orders(
    business_id: UUID = Depends(get_current_business_id),
    db: DatabaseService = Depends(get_database_service)
):
    """Get active orders summary (mobile-optimized)"""
    orders = await db.get_active_orders(business_id)
    
    summaries = []
    for order in orders:
        # Calculate item count
        totals = await db.calculate_order_totals(UUID(order["id"]))
        
        summaries.append(OrderSummary(
            id=order["id"],
            order_number=order.get("order_number"),
            status=order["status"],
            table_number=order.get("table_number"),
            total_amount=Decimal(str(order["total_amount"])),
            item_count=totals["item_count"],
            created_at=order["created_at"]
        ))
    
    return summaries


@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: UUID,
    updates: OrderUpdate,
    current_user: dict = Depends(require_staff_role),
    db: DatabaseService = Depends(get_database_service)
):
    """Update order"""
    # Verify order exists and business access
    order = await db.get_order(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found"
        )
    
    if order["business_id"] != current_user.get("business_id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Prepare updates
    update_data = updates.model_dump(exclude_unset=True)
    
    # Convert enums to values
    if "status" in update_data:
        update_data["status"] = update_data["status"].value
    
    # Convert UUIDs to strings
    for key in ["table_id"]:
        if key in update_data and update_data[key]:
            update_data[key] = str(update_data[key])
    
    # Convert Decimals to floats
    for key in ["subtotal", "tax_amount", "discount_amount", "total_amount"]:
        if key in update_data and update_data[key] is not None:
            update_data[key] = float(update_data[key])
    
    updated_order = await db.update_order(order_id, update_data)
    
    return OrderResponse(**updated_order)


@router.put("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: UUID,
    status: OrderStatus,
    current_user: dict = Depends(require_staff_role),
    db: DatabaseService = Depends(get_database_service)
):
    """Update order status"""
    # Verify order exists
    order = await db.get_order(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found"
        )
    
    # Update status
    updated_order = await db.update_order_status(order_id, status.value)
    
    # If order completed, free up table
    if status == OrderStatus.COMPLETED and order.get("table_id"):
        await db.update_table_status(
            table_id=UUID(order["table_id"]),
            status="available",
            order_id=None
        )
    
    return OrderResponse(**updated_order)


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_order(
    order_id: UUID,
    current_user: dict = Depends(require_staff_role),
    db: DatabaseService = Depends(get_database_service)
):
    """Cancel order"""
    # Verify order exists
    order = await db.get_order(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found"
        )
    
    # Cannot cancel completed orders
    if order["status"] in ["completed", "cancelled"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel order with status: {order['status']}"
        )
    
    # Update to cancelled
    await db.update_order_status(order_id, OrderStatus.CANCELLED.value)
    
    # Free up table if assigned
    if order.get("table_id"):
        await db.update_table_status(
            table_id=UUID(order["table_id"]),
            status="available",
            order_id=None
        )
    
    return None
