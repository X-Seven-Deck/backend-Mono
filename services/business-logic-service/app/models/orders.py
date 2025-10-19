"""
Order Management Models

Complete data models for order processing, tracking, and fulfillment.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum
from decimal import Decimal


class OrderStatus(str, Enum):
    """Order status lifecycle"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class OrderType(str, Enum):
    """Type of order"""
    DINE_IN = "dine_in"
    TAKEOUT = "takeout"
    DELIVERY = "delivery"
    CURBSIDE = "curbside"
    RESERVATION = "reservation"


class PaymentStatus(str, Enum):
    """Payment status"""
    PENDING = "pending"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class OrderItemModifier(BaseModel):
    """Order item modification/customization"""
    modifier_id: str
    name: str
    price: Decimal = Field(default=Decimal("0.00"))
    quantity: int = Field(default=1, ge=1)


class OrderItem(BaseModel):
    """Individual order item"""
    menu_item_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    quantity: int = Field(ge=1)
    unit_price: Decimal = Field(ge=0)
    modifiers: List[OrderItemModifier] = Field(default_factory=list)
    special_instructions: Optional[str] = None
    prep_time_minutes: Optional[int] = None
    
    @property
    def total_price(self) -> Decimal:
        """Calculate total price including modifiers"""
        base_price = self.unit_price * self.quantity
        modifier_total = sum(
            m.price * m.quantity for m in self.modifiers
        ) * self.quantity
        return base_price + modifier_total


class OrderCustomer(BaseModel):
    """Customer information for order"""
    customer_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    delivery_address: Optional[Dict[str, str]] = None


class OrderPayment(BaseModel):
    """Payment information"""
    payment_method: str  # card, cash, digital_wallet
    amount: Decimal
    tip_amount: Decimal = Field(default=Decimal("0.00"))
    tax_amount: Decimal = Field(default=Decimal("0.00"))
    discount_amount: Decimal = Field(default=Decimal("0.00"))
    total_amount: Decimal
    payment_status: PaymentStatus = PaymentStatus.PENDING
    transaction_id: Optional[str] = None
    processor: Optional[str] = None  # stripe, square, etc


class Order(BaseModel):
    """Complete order model"""
    id: Optional[str] = None
    order_number: str
    business_id: str
    customer: OrderCustomer
    order_type: OrderType
    status: OrderStatus = OrderStatus.PENDING
    
    # Items
    items: List[OrderItem]
    
    # Pricing
    subtotal: Decimal
    tax_rate: Decimal = Field(default=Decimal("0.10"))
    tax_amount: Decimal
    tip_amount: Decimal = Field(default=Decimal("0.00"))
    discount_amount: Decimal = Field(default=Decimal("0.00"))
    delivery_fee: Decimal = Field(default=Decimal("0.00"))
    total_amount: Decimal
    
    # Payment
    payment: Optional[OrderPayment] = None
    
    # Delivery/Fulfillment
    table_number: Optional[str] = None
    estimated_ready_time: Optional[datetime] = None
    actual_ready_time: Optional[datetime] = None
    delivery_address: Optional[Dict[str, str]] = None
    delivery_instructions: Optional[str] = None
    
    # Metadata
    notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    @validator('tax_amount', always=True)
    def calculate_tax(cls, v, values):
        if 'subtotal' in values and 'tax_rate' in values:
            return values['subtotal'] * values['tax_rate']
        return v
    
    @validator('total_amount', always=True)
    def calculate_total(cls, v, values):
        subtotal = values.get('subtotal', Decimal("0"))
        tax = values.get('tax_amount', Decimal("0"))
        tip = values.get('tip_amount', Decimal("0"))
        discount = values.get('discount_amount', Decimal("0"))
        delivery = values.get('delivery_fee', Decimal("0"))
        return subtotal + tax + tip + delivery - discount


class CreateOrderRequest(BaseModel):
    """Request to create new order"""
    business_id: str
    customer_id: str
    customer_name: str
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    order_type: OrderType
    items: List[Dict[str, Any]]
    table_number: Optional[str] = None
    delivery_address: Optional[Dict[str, str]] = None
    delivery_instructions: Optional[str] = None
    payment_method: str
    tip_amount: Decimal = Field(default=Decimal("0.00"))
    notes: Optional[str] = None


class UpdateOrderRequest(BaseModel):
    """Request to update order"""
    status: Optional[OrderStatus] = None
    items: Optional[List[Dict[str, Any]]] = None
    notes: Optional[str] = None
    estimated_ready_time: Optional[datetime] = None
    actual_ready_time: Optional[datetime] = None


class OrderResponse(BaseModel):
    """Order API response"""
    order: Order
    message: str
    warnings: List[str] = Field(default_factory=list)


class OrderListResponse(BaseModel):
    """List of orders response"""
    orders: List[Order]
    total_count: int
    page: int
    page_size: int
