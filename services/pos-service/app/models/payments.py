"""
Payment Models
Payment method selection and tracking
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from enum import Enum


class PaymentMethod(str, Enum):
    """Payment method enumeration"""
    CASH = "cash"
    CARD = "card"


class PaymentStatus(str, Enum):
    """Payment status enumeration"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentCreate(BaseModel):
    """Create payment record"""
    order_id: UUID
    payment_method: PaymentMethod
    amount: Decimal = Field(..., gt=0, description="Payment amount must be greater than 0")
    tip_amount: Optional[Decimal] = Field(default=Decimal("0"), ge=0)
    staff_id: Optional[UUID] = None
    transaction_id: Optional[str] = Field(None, max_length=255, description="External transaction reference")
    notes: Optional[str] = Field(None, max_length=500)


class PaymentUpdate(BaseModel):
    """Update payment"""
    status: Optional[PaymentStatus] = None
    transaction_id: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = Field(None, max_length=500)


class PaymentResponse(BaseModel):
    """Payment response"""
    id: UUID
    business_id: UUID
    order_id: UUID
    payment_method: PaymentMethod
    amount: Decimal
    tip_amount: Decimal
    tax_amount: Decimal
    status: PaymentStatus
    transaction_id: Optional[str] = None
    processor: Optional[str] = None
    metadata: Dict = Field(default_factory=dict)
    processed_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class PaymentSummary(BaseModel):
    """Payment summary for reporting"""
    payment_method: PaymentMethod
    total_amount: Decimal
    transaction_count: int
    tip_total: Decimal
    
    class Config:
        from_attributes = True
