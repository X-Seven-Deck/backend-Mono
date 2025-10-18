"""
Receipt Models
Digital receipt generation and storage
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from uuid import UUID


class ReceiptLineItem(BaseModel):
    """Receipt line item"""
    name: str
    quantity: int
    unit_price: Decimal
    total: Decimal
    modifiers: List[str] = Field(default_factory=list)


class ReceiptData(BaseModel):
    """Complete receipt data structure"""
    receipt_number: str
    order_number: Optional[str]
    business_name: str
    business_address: Optional[str]
    business_phone: Optional[str]
    date: datetime
    table_number: Optional[str]
    server_name: Optional[str]
    customer_count: int
    
    # Line items
    items: List[ReceiptLineItem]
    
    # Totals
    subtotal: Decimal
    tax_amount: Decimal
    tax_rate: float
    discount_amount: Decimal
    tip_amount: Decimal
    total_amount: Decimal
    
    # Payment
    payment_method: str
    
    # Footer
    footer_message: Optional[str] = "Thank you for your business!"
    
    class Config:
        from_attributes = True


class ReceiptCreate(BaseModel):
    """Create receipt"""
    order_id: UUID
    business_id: UUID
    generated_by: Optional[UUID] = None


class ReceiptResponse(BaseModel):
    """Receipt response"""
    id: UUID
    order_id: UUID
    receipt_number: str
    receipt_data: ReceiptData
    generated_at: datetime
    generated_by: Optional[UUID] = None
    
    class Config:
        from_attributes = True


class ReceiptPDFRequest(BaseModel):
    """Request to generate PDF receipt"""
    receipt_id: UUID
    format: str = Field(default="pdf", pattern="^(pdf|html)$")
