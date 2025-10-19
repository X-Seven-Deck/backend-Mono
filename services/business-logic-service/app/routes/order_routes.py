"""
Order Management Routes

Complete REST API endpoints for order operations.
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Query
from typing import List, Optional
from datetime import datetime

from app.models.orders import (
    CreateOrderRequest, UpdateOrderRequest, OrderResponse,
    OrderListResponse, OrderStatus
)
from app.services.order_service import get_order_service
from app.middleware.tenant_middleware import get_tenant_context

router = APIRouter(prefix="/api/v1/orders", tags=["Orders"])


@router.post("", response_model=OrderResponse)
async def create_order(
    request: CreateOrderRequest,
    req: Request
):
    """
    Create new order
    
    - Validates menu items
    - Calculates totals
    - Checks inventory
    - Triggers Temporal workflow
    - Sends notifications
    """
    try:
        tenant_context = get_tenant_context(req)
        order_service = get_order_service()
        
        result = await order_service.create_order(
            request=request,
            tenant_id=tenant_context.tenant_id
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{order_id}")
async def get_order(
    order_id: str,
    req: Request
):
    """Get order by ID"""
    try:
        order_service = get_order_service()
        order = await order_service.get_order(order_id)
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        return order
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{order_id}")
async def update_order(
    order_id: str,
    request: UpdateOrderRequest,
    req: Request
):
    """Update order"""
    try:
        order_service = get_order_service()
        order = await order_service.update_order(order_id, request)
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        return order
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def list_orders(
    business_id: str = Query(..., description="Business ID"),
    status: Optional[OrderStatus] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    req: Request = None
):
    """List orders for business"""
    try:
        order_service = get_order_service()
        orders = await order_service.get_business_orders(
            business_id=business_id,
            status=status,
            limit=limit,
            offset=offset
        )
        
        return OrderListResponse(
            orders=orders,
            total_count=len(orders),
            page=offset // limit + 1,
            page_size=limit
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{order_id}/cancel")
async def cancel_order(
    order_id: str,
    reason: str = Query(..., description="Cancellation reason"),
    req: Request = None
):
    """Cancel order"""
    try:
        order_service = get_order_service()
        success = await order_service.cancel_order(order_id, reason)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to cancel order")
        
        return {"message": "Order cancelled successfully", "order_id": order_id}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{order_id}/status")
async def get_order_status(
    order_id: str,
    req: Request = None
):
    """Get order status and tracking info"""
    try:
        order_service = get_order_service()
        order = await order_service.get_order(order_id)
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        return {
            "order_id": order_id,
            "order_number": order.order_number,
            "status": order.status,
            "estimated_ready_time": order.estimated_ready_time,
            "actual_ready_time": order.actual_ready_time,
            "created_at": order.created_at,
            "updated_at": order.updated_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
