"""
Analytics Routes
Business intelligence and reporting endpoints
"""

from fastapi import APIRouter, Depends, Query
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, date, timedelta
from decimal import Decimal
from pydantic import BaseModel, Field

from ..core.security import require_staff_role, get_current_business_id
from ..services.database import DatabaseService, get_database_service

router = APIRouter(prefix="/api/v1/pos/analytics", tags=["Analytics"])


class SalesAnalytics(BaseModel):
    """Sales analytics response"""
    period: str
    start_date: datetime
    end_date: datetime
    total_revenue: Decimal
    total_orders: int
    average_order_value: Decimal
    total_tax: Decimal
    total_tips: Decimal
    payment_breakdown: Dict[str, Decimal]
    hourly_breakdown: List[Dict[str, Any]] = Field(default_factory=list)


class ItemPerformance(BaseModel):
    """Item performance metrics"""
    item_id: UUID
    item_name: str
    quantity_sold: int
    revenue: Decimal
    percentage_of_total: float
    rank: int


class StaffPerformance(BaseModel):
    """Staff performance metrics"""
    staff_id: UUID
    staff_name: str
    orders_processed: int
    total_revenue: Decimal
    average_order_value: Decimal
    tips_earned: Decimal


class TableAnalytics(BaseModel):
    """Table turnover analytics"""
    table_id: UUID
    table_number: str
    total_orders: int
    total_revenue: Decimal
    average_occupancy_time: float  # minutes
    turnover_rate: float


@router.get("/sales", response_model=SalesAnalytics)
async def get_sales_analytics(
    start_date: Optional[date] = Query(None, description="Start date (defaults to today)"),
    end_date: Optional[date] = Query(None, description="End date (defaults to today)"),
    period: str = Query("day", description="Period: day, week, month"),
    business_id: UUID = Depends(get_current_business_id),
    current_user: dict = Depends(require_staff_role),
    db: DatabaseService = Depends(get_database_service)
):
    """
    Get sales analytics for a time period
    
    Returns comprehensive sales metrics including revenue, orders, and breakdowns
    """
    # Set default dates
    if not start_date:
        start_date = date.today()
    if not end_date:
        end_date = start_date
    
    # Convert to datetime
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    # Get orders for the period
    orders_result = db.client.table("orders")\
        .select("*")\
        .eq("business_id", str(business_id))\
        .gte("created_at", start_datetime.isoformat())\
        .lte("created_at", end_datetime.isoformat())\
        .in_("status", ["completed"])\
        .execute()
    
    orders = orders_result.data
    
    # Calculate metrics
    total_revenue = Decimal("0")
    total_tax = Decimal("0")
    total_orders = len(orders)
    hourly_counts: Dict[int, int] = {}
    hourly_revenue: Dict[int, Decimal] = {}
    
    for order in orders:
        total_revenue += Decimal(str(order.get("total_amount", 0)))
        total_tax += Decimal(str(order.get("tax_amount", 0)))
        
        # Hourly breakdown
        order_time = datetime.fromisoformat(order["created_at"].replace('Z', '+00:00'))
        hour = order_time.hour
        hourly_counts[hour] = hourly_counts.get(hour, 0) + 1
        hourly_revenue[hour] = hourly_revenue.get(hour, Decimal("0")) + Decimal(str(order.get("total_amount", 0)))
    
    # Get payment breakdown
    payments_result = await db.get_daily_payment_summary(business_id, start_datetime)
    
    # Calculate average order value
    average_order_value = total_revenue / total_orders if total_orders > 0 else Decimal("0")
    
    # Build hourly breakdown
    hourly_breakdown = []
    for hour in range(24):
        if hour in hourly_counts:
            hourly_breakdown.append({
                "hour": hour,
                "orders": hourly_counts[hour],
                "revenue": float(hourly_revenue[hour])
            })
    
    return SalesAnalytics(
        period=period,
        start_date=start_datetime,
        end_date=end_datetime,
        total_revenue=total_revenue,
        total_orders=total_orders,
        average_order_value=average_order_value,
        total_tax=total_tax,
        total_tips=payments_result["total"]["tips"],
        payment_breakdown={
            "cash": float(payments_result["cash"]["amount"]),
            "card": float(payments_result["card"]["amount"])
        },
        hourly_breakdown=hourly_breakdown
    )


@router.get("/items/top", response_model=List[ItemPerformance])
async def get_top_items(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    business_id: UUID = Depends(get_current_business_id),
    current_user: dict = Depends(require_staff_role),
    db: DatabaseService = Depends(get_database_service)
):
    """
    Get top-selling items for a time period
    
    Returns items ranked by quantity sold
    """
    # Set default dates
    if not start_date:
        start_date = date.today()
    if not end_date:
        end_date = start_date
    
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    # Get completed orders
    orders_result = db.client.table("orders")\
        .select("id")\
        .eq("business_id", str(business_id))\
        .gte("created_at", start_datetime.isoformat())\
        .lte("created_at", end_datetime.isoformat())\
        .eq("status", "completed")\
        .execute()
    
    order_ids = [order["id"] for order in orders_result.data]
    
    if not order_ids:
        return []
    
    # Get order items
    items_result = db.client.table("order_items")\
        .select("menu_item_id, name, quantity, unit_price")\
        .in_("order_id", order_ids)\
        .execute()
    
    # Aggregate by menu item
    item_stats: Dict[str, Dict] = {}
    total_revenue = Decimal("0")
    
    for item in items_result.data:
        item_id = item.get("menu_item_id") or "unknown"
        item_name = item["name"]
        quantity = item["quantity"]
        revenue = Decimal(str(item["quantity"])) * Decimal(str(item["unit_price"]))
        
        if item_id not in item_stats:
            item_stats[item_id] = {
                "item_id": item_id,
                "item_name": item_name,
                "quantity_sold": 0,
                "revenue": Decimal("0")
            }
        
        item_stats[item_id]["quantity_sold"] += quantity
        item_stats[item_id]["revenue"] += revenue
        total_revenue += revenue
    
    # Sort by quantity sold
    sorted_items = sorted(
        item_stats.values(),
        key=lambda x: x["quantity_sold"],
        reverse=True
    )[:limit]
    
    # Build response with rankings
    results = []
    for rank, item in enumerate(sorted_items, 1):
        percentage = float(item["revenue"] / total_revenue * 100) if total_revenue > 0 else 0
        results.append(ItemPerformance(
            item_id=UUID(item["item_id"]) if item["item_id"] != "unknown" else UUID('00000000-0000-0000-0000-000000000000'),
            item_name=item["item_name"],
            quantity_sold=item["quantity_sold"],
            revenue=item["revenue"],
            percentage_of_total=percentage,
            rank=rank
        ))
    
    return results


@router.get("/staff", response_model=List[StaffPerformance])
async def get_staff_performance(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    business_id: UUID = Depends(get_current_business_id),
    current_user: dict = Depends(require_staff_role),
    db: DatabaseService = Depends(get_database_service)
):
    """
    Get staff performance metrics
    
    Returns orders processed and revenue by staff member
    """
    # Set default dates
    if not start_date:
        start_date = date.today()
    if not end_date:
        end_date = start_date
    
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    # Get orders with staff assignments
    orders_result = db.client.table("orders")\
        .select("staff_id, total_amount")\
        .eq("business_id", str(business_id))\
        .gte("created_at", start_datetime.isoformat())\
        .lte("created_at", end_datetime.isoformat())\
        .eq("status", "completed")\
        .not_.is_("staff_id", "null")\
        .execute()
    
    # Get payments for tips
    payments_result = db.client.table("payments")\
        .select("order_id, tip_amount")\
        .execute()
    
    tips_by_order = {p["order_id"]: Decimal(str(p.get("tip_amount", 0))) for p in payments_result.data}
    
    # Aggregate by staff
    staff_stats: Dict[str, Dict] = {}
    
    for order in orders_result.data:
        staff_id = order["staff_id"]
        revenue = Decimal(str(order["total_amount"]))
        tips = tips_by_order.get(order["id"], Decimal("0"))
        
        if staff_id not in staff_stats:
            staff_stats[staff_id] = {
                "staff_id": staff_id,
                "orders_processed": 0,
                "total_revenue": Decimal("0"),
                "tips_earned": Decimal("0")
            }
        
        staff_stats[staff_id]["orders_processed"] += 1
        staff_stats[staff_id]["total_revenue"] += revenue
        staff_stats[staff_id]["tips_earned"] += tips
    
    # Get staff names
    staff_ids = list(staff_stats.keys())
    staff_result = db.client.table("staff_members")\
        .select("id, first_name, last_name")\
        .in_("id", staff_ids)\
        .execute()
    
    staff_names = {
        s["id"]: f"{s.get('first_name', '')} {s.get('last_name', '')}".strip()
        for s in staff_result.data
    }
    
    # Build response
    results = []
    for staff_id, stats in staff_stats.items():
        avg_order_value = (stats["total_revenue"] / stats["orders_processed"]) if stats["orders_processed"] > 0 else Decimal("0")
        
        results.append(StaffPerformance(
            staff_id=UUID(staff_id),
            staff_name=staff_names.get(staff_id, "Unknown"),
            orders_processed=stats["orders_processed"],
            total_revenue=stats["total_revenue"],
            average_order_value=avg_order_value,
            tips_earned=stats["tips_earned"]
        ))
    
    # Sort by revenue
    results.sort(key=lambda x: x.total_revenue, reverse=True)
    
    return results


@router.get("/tables", response_model=List[TableAnalytics])
async def get_table_analytics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    business_id: UUID = Depends(get_current_business_id),
    current_user: dict = Depends(require_staff_role),
    db: DatabaseService = Depends(get_database_service)
):
    """
    Get table turnover analytics
    
    Returns orders and revenue by table
    """
    # Set default dates
    if not start_date:
        start_date = date.today()
    if not end_date:
        end_date = start_date
    
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    # Get orders with tables
    orders_result = db.client.table("orders")\
        .select("table_id, total_amount, created_at, updated_at")\
        .eq("business_id", str(business_id))\
        .gte("created_at", start_datetime.isoformat())\
        .lte("created_at", end_datetime.isoformat())\
        .eq("status", "completed")\
        .not_.is_("table_id", "null")\
        .execute()
    
    # Aggregate by table
    table_stats: Dict[str, Dict] = {}
    
    for order in orders_result.data:
        table_id = order["table_id"]
        revenue = Decimal(str(order["total_amount"]))
        
        # Calculate occupancy time
        created = datetime.fromisoformat(order["created_at"].replace('Z', '+00:00'))
        updated = datetime.fromisoformat(order["updated_at"].replace('Z', '+00:00'))
        occupancy_minutes = (updated - created).total_seconds() / 60
        
        if table_id not in table_stats:
            table_stats[table_id] = {
                "table_id": table_id,
                "total_orders": 0,
                "total_revenue": Decimal("0"),
                "total_occupancy_minutes": 0
            }
        
        table_stats[table_id]["total_orders"] += 1
        table_stats[table_id]["total_revenue"] += revenue
        table_stats[table_id]["total_occupancy_minutes"] += occupancy_minutes
    
    # Get table info
    table_ids = list(table_stats.keys())
    tables_result = db.client.table("tables")\
        .select("id, table_number")\
        .in_("id", table_ids)\
        .execute()
    
    table_numbers = {t["id"]: t["table_number"] for t in tables_result.data}
    
    # Build response
    results = []
    hours_in_period = (end_datetime - start_datetime).total_seconds() / 3600
    
    for table_id, stats in table_stats.items():
        avg_occupancy = stats["total_occupancy_minutes"] / stats["total_orders"] if stats["total_orders"] > 0 else 0
        turnover_rate = stats["total_orders"] / hours_in_period if hours_in_period > 0 else 0
        
        results.append(TableAnalytics(
            table_id=UUID(table_id),
            table_number=table_numbers.get(table_id, "Unknown"),
            total_orders=stats["total_orders"],
            total_revenue=stats["total_revenue"],
            average_occupancy_time=avg_occupancy,
            turnover_rate=turnover_rate
        ))
    
    # Sort by revenue
    results.sort(key=lambda x: x.total_revenue, reverse=True)
    
    return results
