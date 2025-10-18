"""
Order Management Models
Enterprise-grade order data models with validation
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from enum import Enum


class OrderStatus(str, Enum):
    """Order status enumeration"""
    NEW = "new"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    SERVED = "served"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class OrderItemCreate(BaseModel):
    """Create order item"""
    menu_item_id: UUID
    quantity: int = Field(..., gt=0, description="Quantity must be greater than 0")
    unit_price: Decimal = Field(..., gt=0, description="Unit price must be greater than 0")
    modifiers: List[Dict[str, Any]] = Field(default_factory=list, description="Item modifiers/customizations")
    special_instructions: Optional[str] = Field(None, max_length=500)
    
    @validator('unit_price')
    def validate_price(cls, v):
        """Validate price has max 2 decimal places"""
        if v.as_tuple().exponent < -2:
            raise ValueError('Price cannot have more than 2 decimal places')
        return v


class OrderCreate(BaseModel):
    """Create new order"""
    business_id: UUID
    table_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None
    customer_count: int = Field(default=1, ge=1, le=50)
    items: List[OrderItemCreate] = Field(..., min_items=1, description="Order must have at least one item")
    notes: Optional[str] = Field(None, max_length=1000)
    staff_id: Optional[UUID] = None
    
    @validator('items')
    def validate_items(cls, v):
        """Validate order has items"""
        if not v:
            raise ValueError('Order must contain at least one item')
        return v


class OrderUpdate(BaseModel):
    """Update order"""
    status: Optional[OrderStatus] = None
    table_id: Optional[UUID] = None
    customer_count: Optional[int] = Field(None, ge=1, le=50)
    notes: Optional[str] = Field(None, max_length=1000)
    subtotal: Optional[Decimal] = Field(None, ge=0)
    tax_amount: Optional[Decimal] = Field(None, ge=0)
    discount_amount: Optional[Decimal] = Field(None, ge=0)
    total_amount: Optional[Decimal] = Field(None, ge=0)


class OrderItemResponse(BaseModel):
    """Order item response"""
    id: UUID
    order_id: UUID
    menu_item_id: Optional[UUID]
    name: str
    quantity: int
    unit_price: Decimal
    modifiers: List[Dict[str, Any]] = Field(default_factory=list)
    special_instructions: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    """Order response"""
    id: UUID
    business_id: UUID
    order_number: Optional[str] = None
    table_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None
    status: OrderStatus
    subtotal: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    customer_count: int
    notes: Optional[str] = None
    staff_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class OrderWithDetails(OrderResponse):
    """Order with full details including items"""
    items: List[OrderItemResponse] = Field(default_factory=list)
    table_number: Optional[str] = None
    customer_name: Optional[str] = None
    staff_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class OrderSummary(BaseModel):
    """Order summary for mobile/dashboard"""
    id: UUID
    order_number: Optional[str]
    status: OrderStatus
    table_number: Optional[str]
    total_amount: Decimal
    item_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True
