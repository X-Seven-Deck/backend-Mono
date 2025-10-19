"""
Inventory Management Routes

Complete REST API endpoints for inventory operations.
"""

from fastapi import APIRouter, HTTPException, Request, Query
from typing import Optional

from app.models.inventory import (
    CreateInventoryItemRequest, UpdateInventoryStockRequest,
    InventoryResponse, InventoryListResponse
)
from app.services.inventory_service import get_inventory_service
from app.middleware.tenant_middleware import get_tenant_context

router = APIRouter(prefix="/api/v1/inventory", tags=["Inventory"])


@router.post("", response_model=InventoryResponse)
async def create_inventory_item(
    request: CreateInventoryItemRequest,
    req: Request
):
    """Create new inventory item"""
    try:
        tenant_context = get_tenant_context(req)
        inventory_service = get_inventory_service()
        
        result = await inventory_service.create_item(
            request=request,
            tenant_id=tenant_context.tenant_id
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def list_inventory(
    business_id: str = Query(...),
    category: Optional[str] = Query(None),
    low_stock_only: bool = Query(False),
    req: Request = None
):
    """List inventory items"""
    try:
        inventory_service = get_inventory_service()
        
        result = await inventory_service.get_business_inventory(
            business_id=business_id,
            category=category,
            low_stock_only=low_stock_only
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{item_id}")
async def get_inventory_item(
    item_id: str,
    req: Request = None
):
    """Get inventory item by ID"""
    try:
        inventory_service = get_inventory_service()
        item = await inventory_service.get_item(item_id)
        
        if not item:
            raise HTTPException(status_code=404, detail="Inventory item not found")
        
        return item
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{item_id}/adjust")
async def adjust_stock(
    item_id: str,
    request: UpdateInventoryStockRequest,
    business_id: str = Query(...),
    req: Request = None
):
    """Adjust inventory stock"""
    try:
        inventory_service = get_inventory_service()
        
        result = await inventory_service.update_stock(
            item_id=item_id,
            request=request,
            business_id=business_id
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts")
async def get_stock_alerts(
    business_id: str = Query(...),
    active_only: bool = Query(True),
    req: Request = None
):
    """Get stock alerts"""
    try:
        inventory_service = get_inventory_service()
        
        alerts = await inventory_service.get_low_stock_alerts(
            business_id=business_id,
            active_only=active_only
        )
        
        return {"alerts": alerts, "count": len(alerts)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reorder-suggestions")
async def get_reorder_suggestions(
    business_id: str = Query(...),
    req: Request = None
):
    """Get automated reorder suggestions"""
    try:
        inventory_service = get_inventory_service()
        
        suggestions = await inventory_service.suggest_reorder_items(
            business_id=business_id
        )
        
        return {
            "suggestions": suggestions,
            "count": len(suggestions)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/purchase-orders")
async def create_purchase_order(
    business_id: str = Query(...),
    supplier_id: str = Query(...),
    items: list = Query(...),
    req: Request = None
):
    """Create purchase order"""
    try:
        inventory_service = get_inventory_service()
        
        po = await inventory_service.create_purchase_order(
            business_id=business_id,
            supplier_id=supplier_id,
            items=items
        )
        
        return po
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
