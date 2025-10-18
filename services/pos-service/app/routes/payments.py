"""
Payment Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from datetime import datetime

from ..models.payments import PaymentCreate, PaymentUpdate, PaymentResponse
from ..core.security import require_staff_role, get_current_business_id
from ..services.database import DatabaseService, get_database_service

router = APIRouter(prefix="/api/v1/pos/payments", tags=["Payments"])


@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment: PaymentCreate,
    current_user: dict = Depends(require_staff_role),
    db: DatabaseService = Depends(get_database_service)
):
    """Record payment for order"""
    # Verify order exists
    order = await db.get_order(payment.order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    
    # Check if payment already exists
    existing_payment = await db.get_payment_by_order(payment.order_id)
    if existing_payment:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment already exists for this order")
    
    payment_data = {
        "business_id": order["business_id"],
        "order_id": str(payment.order_id),
        "payment_method": payment.payment_method.value,
        "amount": float(payment.amount),
        "tip_amount": float(payment.tip_amount or 0),
        "tax_amount": float(order.get("tax_amount", 0)),
        "status": "completed",
        "transaction_id": payment.transaction_id,
        "metadata": {"notes": payment.notes} if payment.notes else {},
        "processed_at": datetime.utcnow().isoformat()
    }
    
    created_payment = await db.create_payment(payment_data)
    
    # Update order status to completed
    await db.update_order_status(payment.order_id, "completed")
    
    return PaymentResponse(**created_payment)


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: UUID,
    current_user: dict = Depends(require_staff_role),
    db: DatabaseService = Depends(get_database_service)
):
    """Get payment by ID"""
    payment = await db.get_payment(payment_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    
    return PaymentResponse(**payment)


@router.get("/order/{order_id}", response_model=PaymentResponse)
async def get_payment_by_order(
    order_id: UUID,
    current_user: dict = Depends(require_staff_role),
    db: DatabaseService = Depends(get_database_service)
):
    """Get payment for order"""
    payment = await db.get_payment_by_order(order_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found for this order")
    
    return PaymentResponse(**payment)
