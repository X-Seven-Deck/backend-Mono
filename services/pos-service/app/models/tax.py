"""
Tax Models
Tax calculation and rule management
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, List, Any
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from enum import Enum


class TaxType(str, Enum):
    """Tax type enumeration"""
    VAT = "vat"
    GST = "gst"
    SALES_TAX = "sales_tax"
    SERVICE_TAX = "service_tax"


class TaxRuleCreate(BaseModel):
    """Create tax rule"""
    business_id: UUID
    location_id: Optional[UUID] = None
    name: str = Field(..., min_length=1, max_length=100)
    rate: Decimal = Field(..., ge=0, le=1, description="Tax rate as decimal (e.g., 0.10 for 10%)")
    type: TaxType
    is_active: bool = True
    
    @validator('rate')
    def validate_rate(cls, v):
        """Validate tax rate is reasonable"""
        if v < 0 or v > 1:
            raise ValueError('Tax rate must be between 0 and 1 (0% to 100%)')
        return v


class TaxRuleUpdate(BaseModel):
    """Update tax rule"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    rate: Optional[Decimal] = Field(None, ge=0, le=1)
    type: Optional[TaxType] = None
    is_active: Optional[bool] = None


class TaxRuleResponse(BaseModel):
    """Tax rule response"""
    id: UUID
    business_id: UUID
    location_id: Optional[UUID] = None
    name: str
    rate: Decimal
    type: TaxType
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class TaxCalculation(BaseModel):
    """Tax calculation result"""
    subtotal: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    total_with_tax: Decimal
    tax_breakdown: Dict[str, Decimal] = Field(default_factory=dict, description="Breakdown by tax type")
    
    class Config:
        from_attributes = True


class TaxCalculationRequest(BaseModel):
    """Request tax calculation"""
    business_id: UUID
    location_id: Optional[UUID] = None
    subtotal: Decimal = Field(..., gt=0)
    items: List[Dict[str, Any]] = Field(default_factory=list, description="Item-level tax calculation if needed")
