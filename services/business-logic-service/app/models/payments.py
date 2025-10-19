"""
Payment Processing Models

Complete data models for payment processing, transactions, and refunds.
"""

from pydantic import BaseModel, Field
from typing import Dict, Optional, Any, List
from datetime import datetime
from enum import Enum
from decimal import Decimal


class PaymentMethod(str, Enum):
    """Payment method types"""
    CARD = "card"
    CASH = "cash"
    DIGITAL_WALLET = "digital_wallet"
    BANK_TRANSFER = "bank_transfer"
    CHECK = "check"
    STORE_CREDIT = "store_credit"


class PaymentProcessor(str, Enum):
    """Payment processor"""
    STRIPE = "stripe"
    SQUARE = "square"
    PAYPAL = "paypal"
    MANUAL = "manual"


class TransactionStatus(str, Enum):
    """Transaction status"""
    PENDING = "pending"
    PROCESSING = "processing"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class RefundStatus(str, Enum):
    """Refund status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CardBrand(str, Enum):
    """Card brand"""
    VISA = "visa"
    MASTERCARD = "mastercard"
    AMEX = "amex"
    DISCOVER = "discover"
    DINERS = "diners"
    JCB = "jcb"
    UNKNOWN = "unknown"


class PaymentCard(BaseModel):
    """Payment card information"""
    brand: CardBrand
    last_four: str
    exp_month: int = Field(ge=1, le=12)
    exp_year: int
    cardholder_name: Optional[str] = None
    
    @property
    def is_expired(self) -> bool:
        """Check if card is expired"""
        now = datetime.utcnow()
        return now.year > self.exp_year or (
            now.year == self.exp_year and now.month > self.exp_month
        )


class PaymentTransaction(BaseModel):
    """Payment transaction model"""
    id: Optional[str] = None
    business_id: str
    
    # Transaction details
    transaction_id: str
    processor: PaymentProcessor
    payment_method: PaymentMethod
    status: TransactionStatus = TransactionStatus.PENDING
    
    # Amounts
    amount: Decimal = Field(ge=0)
    tip_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    fee_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    total_amount: Decimal
    
    # Currency
    currency: str = Field(default="USD")
    
    # Reference
    reference_type: str  # order, reservation, invoice
    reference_id: str
    customer_id: str
    
    # Card details (if applicable)
    card_details: Optional[PaymentCard] = None
    
    # Processing
    processor_transaction_id: Optional[str] = None
    processor_response: Optional[Dict[str, Any]] = None
    authorization_code: Optional[str] = None
    
    # Timestamps
    processed_at: Optional[datetime] = None
    authorized_at: Optional[datetime] = None
    captured_at: Optional[datetime] = None
    
    # Receipt
    receipt_url: Optional[str] = None
    receipt_number: Optional[str] = None
    
    # Metadata
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PaymentRefund(BaseModel):
    """Refund model"""
    id: Optional[str] = None
    business_id: str
    transaction_id: str
    
    # Refund details
    refund_id: str
    amount: Decimal = Field(gt=0)
    reason: str
    status: RefundStatus = RefundStatus.PENDING
    
    # Processing
    processor_refund_id: Optional[str] = None
    processor_response: Optional[Dict[str, Any]] = None
    
    # Timestamps
    processed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Metadata
    notes: Optional[str] = None
    initiated_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ProcessPaymentRequest(BaseModel):
    """Request to process payment"""
    business_id: str
    reference_type: str
    reference_id: str
    customer_id: str
    payment_method: PaymentMethod
    amount: Decimal
    tip_amount: Decimal = Field(default=Decimal("0.00"))
    tax_amount: Decimal = Field(default=Decimal("0.00"))
    currency: str = Field(default="USD")
    payment_token: Optional[str] = None  # For card payments
    description: Optional[str] = None


class ProcessRefundRequest(BaseModel):
    """Request to process refund"""
    transaction_id: str
    amount: Decimal
    reason: str
    notes: Optional[str] = None


class PaymentResponse(BaseModel):
    """Payment API response"""
    transaction: PaymentTransaction
    success: bool
    message: str
    receipt_url: Optional[str] = None


class RefundResponse(BaseModel):
    """Refund API response"""
    refund: PaymentRefund
    success: bool
    message: str


class PaymentSummary(BaseModel):
    """Payment summary for reporting"""
    business_id: str
    period_start: datetime
    period_end: datetime
    total_transactions: int
    total_amount: Decimal
    total_refunds: Decimal
    net_amount: Decimal
    breakdown_by_method: Dict[str, Decimal]
    breakdown_by_status: Dict[str, int]
