"""
Inventory Management Models

Complete data models for inventory tracking, stock management, and supplier operations.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any
from datetime import datetime, date
from enum import Enum
from decimal import Decimal


class InventoryUnit(str, Enum):
    """Unit of measurement"""
    PIECE = "piece"
    KILOGRAM = "kg"
    GRAM = "g"
    POUND = "lb"
    OUNCE = "oz"
    LITER = "liter"
    MILLILITER = "ml"
    GALLON = "gallon"
    CASE = "case"
    BOX = "box"
    DOZEN = "dozen"


class TransactionType(str, Enum):
    """Inventory transaction type"""
    PURCHASE = "purchase"
    SALE = "sale"
    ADJUSTMENT = "adjustment"
    TRANSFER = "transfer"
    WASTE = "waste"
    RETURN = "return"
    COUNT = "count"


class AlertType(str, Enum):
    """Stock alert type"""
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    EXPIRING_SOON = "expiring_soon"
    EXPIRED = "expired"
    OVERSTOCK = "overstock"


class PurchaseOrderStatus(str, Enum):
    """Purchase order status"""
    DRAFT = "draft"
    SENT = "sent"
    CONFIRMED = "confirmed"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class InventoryItem(BaseModel):
    """Inventory item model"""
    id: Optional[str] = None
    business_id: str
    location_id: Optional[str] = None
    
    # Item details
    name: str
    description: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    category: Optional[str] = None
    
    # Stock information
    unit: InventoryUnit
    current_stock: Decimal = Field(ge=0)
    min_stock: Decimal = Field(ge=0)  # Reorder point
    max_stock: Optional[Decimal] = None
    reorder_quantity: Optional[Decimal] = None
    
    # Pricing
    unit_cost: Decimal = Field(ge=0)
    unit_price: Optional[Decimal] = None
    
    # Supplier
    supplier_id: Optional[str] = None
    supplier_sku: Optional[str] = None
    lead_time_days: Optional[int] = None
    
    # Tracking
    is_tracked: bool = Field(default=True)
    track_expiry: bool = Field(default=False)
    expiry_date: Optional[date] = None
    last_counted_at: Optional[datetime] = None
    last_ordered_at: Optional[datetime] = None
    
    # Metadata
    notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)
    
    @property
    def is_low_stock(self) -> bool:
        """Check if item is low on stock"""
        return self.current_stock <= self.min_stock
    
    @property
    def stock_value(self) -> Decimal:
        """Calculate total stock value"""
        return self.current_stock * self.unit_cost


class InventoryTransaction(BaseModel):
    """Inventory transaction record"""
    id: Optional[str] = None
    business_id: str
    inventory_item_id: str
    
    # Transaction details
    transaction_type: TransactionType
    quantity: Decimal
    unit_cost: Optional[Decimal] = None
    
    # Reference
    reference_type: Optional[str] = None  # order, purchase_order, manual
    reference_id: Optional[str] = None
    
    # Metadata
    notes: Optional[str] = None
    performed_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class StockAlert(BaseModel):
    """Stock alert model"""
    id: Optional[str] = None
    business_id: str
    inventory_item_id: str
    
    # Alert details
    alert_type: AlertType
    threshold: Optional[Decimal] = None
    current_value: Decimal
    
    # Status
    is_active: bool = Field(default=True)
    resolved: bool = Field(default=False)
    resolved_at: Optional[datetime] = None
    
    # Notification
    last_triggered_at: Optional[datetime] = None
    notification_sent: bool = Field(default=False)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Supplier(BaseModel):
    """Supplier model"""
    id: Optional[str] = None
    business_id: str
    
    # Supplier details
    name: str
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    
    # Address
    address: Optional[Dict[str, str]] = None
    
    # Terms
    payment_terms: Optional[str] = None
    delivery_terms: Optional[str] = None
    minimum_order_value: Optional[Decimal] = None
    
    # Rating
    rating: Optional[float] = Field(default=None, ge=0, le=5)
    
    # Status
    is_active: bool = Field(default=True)
    
    # Metadata
    notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PurchaseOrderItem(BaseModel):
    """Purchase order item"""
    inventory_item_id: str
    item_name: str
    quantity: Decimal
    unit_cost: Decimal
    total_cost: Decimal


class PurchaseOrder(BaseModel):
    """Purchase order model"""
    id: Optional[str] = None
    business_id: str
    supplier_id: str
    
    # Order details
    order_number: str
    status: PurchaseOrderStatus = PurchaseOrderStatus.DRAFT
    
    # Items
    items: List[PurchaseOrderItem]
    
    # Pricing
    subtotal: Decimal
    tax_amount: Decimal = Field(default=Decimal("0.00"))
    shipping_cost: Decimal = Field(default=Decimal("0.00"))
    total_amount: Decimal
    
    # Dates
    order_date: date
    expected_delivery_date: Optional[date] = None
    actual_delivery_date: Optional[date] = None
    
    # Tracking
    tracking_number: Optional[str] = None
    
    # Metadata
    notes: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CreateInventoryItemRequest(BaseModel):
    """Request to create inventory item"""
    business_id: str
    name: str
    description: Optional[str] = None
    sku: Optional[str] = None
    category: Optional[str] = None
    unit: InventoryUnit
    current_stock: Decimal
    min_stock: Decimal
    unit_cost: Decimal
    supplier_id: Optional[str] = None


class UpdateInventoryStockRequest(BaseModel):
    """Request to update inventory stock"""
    quantity: Decimal
    transaction_type: TransactionType
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    notes: Optional[str] = None


class InventoryResponse(BaseModel):
    """Inventory API response"""
    item: InventoryItem
    message: str


class InventoryListResponse(BaseModel):
    """List of inventory items response"""
    items: List[InventoryItem]
    total_count: int
    total_value: Decimal
    low_stock_count: int
