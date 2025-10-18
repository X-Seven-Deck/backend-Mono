"""
Receipt Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Response
from uuid import UUID

from ..models.receipts import ReceiptCreate, ReceiptResponse
from ..core.security import require_staff_role
from ..services.database import DatabaseService, get_database_service
from ..services.receipt_generator import ReceiptGenerator, get_receipt_generator

router = APIRouter(prefix="/api/v1/pos/receipts", tags=["Receipts"])


@router.post("/", response_model=ReceiptResponse, status_code=status.HTTP_201_CREATED)
async def generate_receipt(
    receipt_req: ReceiptCreate,
    current_user: dict = Depends(require_staff_role),
    db: DatabaseService = Depends(get_database_service),
    receipt_gen: ReceiptGenerator = Depends(get_receipt_generator)
):
    """Generate receipt for order"""
    # Check if receipt already exists
    existing = await db.get_receipt_by_order(receipt_req.order_id)
    if existing:
        return ReceiptResponse(**existing)
    
    receipt = await receipt_gen.generate_receipt(
        order_id=receipt_req.order_id,
        business_id=receipt_req.business_id,
        generated_by=UUID(current_user["user_id"]) if current_user.get("user_id") else None
    )
    
    return ReceiptResponse(**receipt)


@router.get("/{receipt_id}", response_model=ReceiptResponse)
async def get_receipt(
    receipt_id: UUID,
    current_user: dict = Depends(require_staff_role),
    db: DatabaseService = Depends(get_database_service)
):
    """Get receipt by ID"""
    receipt = await db.get_receipt(receipt_id)
    if not receipt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receipt not found")
    
    return ReceiptResponse(**receipt)


@router.get("/{receipt_id}/html")
async def get_receipt_html(
    receipt_id: UUID,
    current_user: dict = Depends(require_staff_role),
    db: DatabaseService = Depends(get_database_service),
    receipt_gen: ReceiptGenerator = Depends(get_receipt_generator)
):
    """Get receipt as HTML"""
    receipt = await db.get_receipt(receipt_id)
    if not receipt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receipt not found")
    
    from ..models.receipts import ReceiptData
    receipt_data = ReceiptData(**receipt["receipt_data"])
    html = receipt_gen.generate_receipt_html(receipt_data)
    
    return Response(content=html, media_type="text/html")


@router.get("/order/{order_id}", response_model=ReceiptResponse)
async def get_receipt_by_order(
    order_id: UUID,
    current_user: dict = Depends(require_staff_role),
    db: DatabaseService = Depends(get_database_service)
):
    """Get receipt for order"""
    receipt = await db.get_receipt_by_order(order_id)
    if not receipt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receipt not found for this order")
    
    return ReceiptResponse(**receipt)
