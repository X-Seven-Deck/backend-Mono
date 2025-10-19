"""
Reservation Management Routes

Complete REST API endpoints for reservation operations.
"""

from fastapi import APIRouter, HTTPException, Request, Query
from typing import Optional
from datetime import datetime

from app.models.reservations import (
    CreateReservationRequest, UpdateReservationRequest,
    AvailabilityCheckRequest, AvailabilityCheckResponse,
    ReservationResponse, ReservationStatus
)
from app.services.reservation_service import get_reservation_service
from app.middleware.tenant_middleware import get_tenant_context

router = APIRouter(prefix="/api/v1/reservations", tags=["Reservations"])


@router.post("", response_model=ReservationResponse)
async def create_reservation(
    request: CreateReservationRequest,
    req: Request
):
    """Create new reservation"""
    try:
        tenant_context = get_tenant_context(req)
        reservation_service = get_reservation_service()
        
        result = await reservation_service.create_reservation(
            request=request,
            tenant_id=tenant_context.tenant_id
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{reservation_id}")
async def get_reservation(
    reservation_id: str,
    req: Request = None
):
    """Get reservation by ID"""
    try:
        reservation_service = get_reservation_service()
        reservation = await reservation_service.get_reservation(reservation_id=reservation_id)
        
        if not reservation:
            raise HTTPException(status_code=404, detail="Reservation not found")
        
        return reservation
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{reservation_id}")
async def update_reservation(
    reservation_id: str,
    request: UpdateReservationRequest,
    req: Request = None
):
    """Update reservation"""
    try:
        reservation_service = get_reservation_service()
        reservation = await reservation_service.update_reservation(
            reservation_id,
            request
        )
        
        if not reservation:
            raise HTTPException(status_code=404, detail="Reservation not found")
        
        return reservation
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{reservation_id}")
async def cancel_reservation(
    reservation_id: str,
    reason: str = Query(..., description="Cancellation reason"),
    req: Request = None
):
    """Cancel reservation"""
    try:
        reservation_service = get_reservation_service()
        success = await reservation_service.cancel_reservation(
            reservation_id,
            reason
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to cancel reservation")
        
        return {
            "message": "Reservation cancelled successfully",
            "reservation_id": reservation_id
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check-availability")
async def check_availability(
    business_id: str = Query(...),
    reservation_time: datetime = Query(...),
    party_size: int = Query(..., ge=1),
    duration_minutes: int = Query(90, ge=30),
    req: Request = None
):
    """Check reservation availability"""
    try:
        reservation_service = get_reservation_service()
        
        availability = await reservation_service.check_availability(
            business_id=business_id,
            reservation_time=reservation_time,
            party_size=party_size,
            duration_minutes=duration_minutes
        )
        
        return availability
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def list_reservations(
    business_id: str = Query(...),
    status: Optional[ReservationStatus] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    req: Request = None
):
    """List reservations for business"""
    try:
        # TODO: Implement list_reservations in service
        return {
            "reservations": [],
            "total_count": 0,
            "page": offset // limit + 1,
            "page_size": limit
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
