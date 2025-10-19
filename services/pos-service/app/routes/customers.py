"""
Customer Management Routes
Customer profiles, order history, and loyalty tracking
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, EmailStr

from ..core.security import require_staff_role, get_current_business_id
from ..services.database import DatabaseService, get_database_service

router = APIRouter(prefix="/api/v1/pos/customers", tags=["Customers"])


class CustomerCreate(BaseModel):
    """Create customer profile"""
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    first_name: str = Field(..., min_length=1, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None


class CustomerUpdate(BaseModel):
    """Update customer profile"""
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    first_name: Optional[str] = Field(None, min_length=1, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None


class CustomerResponse(BaseModel):
    """Customer profile response"""
    id: UUID
    business_id: UUID
    email: Optional[str] = None
    phone: Optional[str] = None
    first_name: str
    last_name: Optional[str] = None
    total_orders: int = 0
    total_spent: Decimal = Decimal("0")
    loyalty_points: int = 0
    last_visit: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CustomerOrderHistory(BaseModel):
    """Customer order history"""
    order_id: UUID
    order_number: Optional[str]
    order_date: datetime
    total_amount: Decimal
    status: str
    items_count: int


@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer: CustomerCreate,
    business_id: UUID = Depends(get_current_business_id),
    current_user: dict = Depends(require_staff_role),
    db: DatabaseService = Depends(get_database_service)
):
    """
    Create new customer profile
    
    Customer profiles enable order history tracking and loyalty programs
    """
    customer_data = {
        "business_id": str(business_id),
        "email": customer.email,
        "phone": customer.phone,
        "first_name": customer.first_name,
        "last_name": customer.last_name,
        "notes": customer.notes,
        "total_orders": 0,
        "total_spent": 0,
        "loyalty_points": 0
    }
    
    result = db.client.table("customers").insert(customer_data).execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create customer"
        )
    
    return CustomerResponse(**result.data[0])


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: UUID,
    business_id: UUID = Depends(get_current_business_id),
    current_user: dict = Depends(require_staff_role),
    db: DatabaseService = Depends(get_database_service)
):
    """Get customer profile by ID"""
    result = db.client.table("customers")\
        .select("*")\
        .eq("id", str(customer_id))\
        .eq("business_id", str(business_id))\
        .execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer {customer_id} not found"
        )
    
    return CustomerResponse(**result.data[0])


@router.get("/", response_model=List[CustomerResponse])
async def list_customers(
    search: Optional[str] = Query(None, description="Search by name, email, or phone"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    business_id: UUID = Depends(get_current_business_id),
    current_user: dict = Depends(require_staff_role),
    db: DatabaseService = Depends(get_database_service)
):
    """
    List customers with optional search
    
    Search is performed across name, email, and phone fields
    """
    query = db.client.table("customers")\
        .select("*")\
        .eq("business_id", str(business_id))
    
    if search:
        # Search in first_name, last_name, email, or phone
        # Note: This is a simplified search; in production, use full-text search
        query = query.or_(f"first_name.ilike.%{search}%,last_name.ilike.%{search}%,email.ilike.%{search}%,phone.ilike.%{search}%")
    
    query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
    result = query.execute()
    
    return [CustomerResponse(**customer) for customer in result.data]


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: UUID,
    updates: CustomerUpdate,
    business_id: UUID = Depends(get_current_business_id),
    current_user: dict = Depends(require_staff_role),
    db: DatabaseService = Depends(get_database_service)
):
    """Update customer profile"""
    # Verify customer exists
    existing = db.client.table("customers")\
        .select("*")\
        .eq("id", str(customer_id))\
        .eq("business_id", str(business_id))\
        .execute()
    
    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer {customer_id} not found"
        )
    
    # Prepare updates
    update_data = updates.model_dump(exclude_unset=True)
    if update_data:
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        result = db.client.table("customers")\
            .update(update_data)\
            .eq("id", str(customer_id))\
            .execute()
        
        return CustomerResponse(**result.data[0])
    
    return CustomerResponse(**existing.data[0])


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: UUID,
    business_id: UUID = Depends(get_current_business_id),
    current_user: dict = Depends(require_staff_role),
    db: DatabaseService = Depends(get_database_service)
):
    """Delete customer profile"""
    # Check if customer has orders
    orders = db.client.table("orders")\
        .select("id")\
        .eq("customer_id", str(customer_id))\
        .limit(1)\
        .execute()
    
    if orders.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete customer with existing orders"
        )
    
    db.client.table("customers")\
        .delete()\
        .eq("id", str(customer_id))\
        .eq("business_id", str(business_id))\
        .execute()
    
    return None


@router.get("/{customer_id}/orders", response_model=List[CustomerOrderHistory])
async def get_customer_orders(
    customer_id: UUID,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    business_id: UUID = Depends(get_current_business_id),
    current_user: dict = Depends(require_staff_role),
    db: DatabaseService = Depends(get_database_service)
):
    """
    Get customer order history
    
    Returns all orders for a specific customer
    """
    # Verify customer exists
    customer_result = db.client.table("customers")\
        .select("id")\
        .eq("id", str(customer_id))\
        .eq("business_id", str(business_id))\
        .execute()
    
    if not customer_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer {customer_id} not found"
        )
    
    # Get orders
    orders_result = db.client.table("orders")\
        .select("id, order_number, created_at, total_amount, status")\
        .eq("customer_id", str(customer_id))\
        .order("created_at", desc=True)\
        .range(offset, offset + limit - 1)\
        .execute()
    
    # Get item counts for each order
    history = []
    for order in orders_result.data:
        items_result = db.client.table("order_items")\
            .select("id")\
            .eq("order_id", order["id"])\
            .execute()
        
        history.append(CustomerOrderHistory(
            order_id=UUID(order["id"]),
            order_number=order.get("order_number"),
            order_date=datetime.fromisoformat(order["created_at"].replace('Z', '+00:00')),
            total_amount=Decimal(str(order["total_amount"])),
            status=order["status"],
            items_count=len(items_result.data)
        ))
    
    return history


@router.post("/{customer_id}/loyalty/add-points")
async def add_loyalty_points(
    customer_id: UUID,
    points: int = Query(..., ge=1, description="Points to add"),
    business_id: UUID = Depends(get_current_business_id),
    current_user: dict = Depends(require_staff_role),
    db: DatabaseService = Depends(get_database_service)
):
    """
    Add loyalty points to customer
    
    Loyalty points can be earned through purchases and promotions
    """
    # Get current points
    customer_result = db.client.table("customers")\
        .select("loyalty_points")\
        .eq("id", str(customer_id))\
        .eq("business_id", str(business_id))\
        .execute()
    
    if not customer_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer {customer_id} not found"
        )
    
    current_points = customer_result.data[0].get("loyalty_points", 0)
    new_points = current_points + points
    
    # Update points
    db.client.table("customers")\
        .update({
            "loyalty_points": new_points,
            "updated_at": datetime.utcnow().isoformat()
        })\
        .eq("id", str(customer_id))\
        .execute()
    
    return {
        "customer_id": str(customer_id),
        "previous_points": current_points,
        "points_added": points,
        "new_points": new_points
    }


@router.post("/{customer_id}/loyalty/redeem-points")
async def redeem_loyalty_points(
    customer_id: UUID,
    points: int = Query(..., ge=1, description="Points to redeem"),
    business_id: UUID = Depends(get_current_business_id),
    current_user: dict = Depends(require_staff_role),
    db: DatabaseService = Depends(get_database_service)
):
    """
    Redeem loyalty points for customer
    
    Deducts points from customer balance
    """
    # Get current points
    customer_result = db.client.table("customers")\
        .select("loyalty_points")\
        .eq("id", str(customer_id))\
        .eq("business_id", str(business_id))\
        .execute()
    
    if not customer_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer {customer_id} not found"
        )
    
    current_points = customer_result.data[0].get("loyalty_points", 0)
    
    if current_points < points:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient points. Customer has {current_points} points"
        )
    
    new_points = current_points - points
    
    # Update points
    db.client.table("customers")\
        .update({
            "loyalty_points": new_points,
            "updated_at": datetime.utcnow().isoformat()
        })\
        .eq("id", str(customer_id))\
        .execute()
    
    return {
        "customer_id": str(customer_id),
        "previous_points": current_points,
        "points_redeemed": points,
        "new_points": new_points
    }
