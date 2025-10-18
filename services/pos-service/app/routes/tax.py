"""
Tax Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID

from ..models.tax import TaxRuleCreate, TaxRuleUpdate, TaxRuleResponse, TaxCalculationRequest, TaxCalculation
from ..core.security import require_staff_role, get_current_business_id
from ..services.database import DatabaseService, get_database_service
from ..services.tax_engine import TaxEngine, get_tax_engine

router = APIRouter(prefix="/api/v1/pos/tax", tags=["Tax"])


@router.post("/rules", response_model=TaxRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_tax_rule(
    rule: TaxRuleCreate,
    current_user: dict = Depends(require_staff_role),
    db: DatabaseService = Depends(get_database_service)
):
    """Create tax rule"""
    rule_data = {
        "business_id": str(rule.business_id),
        "location_id": str(rule.location_id) if rule.location_id else None,
        "name": rule.name,
        "rate": float(rule.rate),
        "type": rule.type.value,
        "is_active": rule.is_active
    }
    
    created_rule = await db.create_tax_rule(rule_data)
    return TaxRuleResponse(**created_rule)


@router.get("/rules", response_model=List[TaxRuleResponse])
async def get_tax_rules(
    location_id: UUID = None,
    is_active: bool = True,
    business_id: UUID = Depends(get_current_business_id),
    db: DatabaseService = Depends(get_database_service)
):
    """Get tax rules"""
    rules = await db.get_tax_rules(business_id, location_id, is_active)
    return [TaxRuleResponse(**rule) for rule in rules]


@router.post("/calculate", response_model=TaxCalculation)
async def calculate_tax(
    calc_req: TaxCalculationRequest,
    current_user: dict = Depends(require_staff_role),
    tax_engine: TaxEngine = Depends(get_tax_engine)
):
    """Calculate tax for amount"""
    result = await tax_engine.calculate_tax(
        business_id=calc_req.business_id,
        subtotal=calc_req.subtotal,
        location_id=calc_req.location_id
    )
    
    return TaxCalculation(
        subtotal=calc_req.subtotal,
        tax_rate=result["tax_rate"],
        tax_amount=result["tax_amount"],
        total_with_tax=result["total_with_tax"],
        tax_breakdown=result["tax_breakdown"]
    )
