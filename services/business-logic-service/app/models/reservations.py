"""
Reservation Management Models

Complete data models for reservation system, table management, and scheduling.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any
from datetime import datetime, date, time
from enum import Enum


class ReservationStatus(str, Enum):
    """Reservation status"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SEATED = "seated"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class TableStatus(str, Enum):
    """Table availability status"""
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    RESERVED = "reserved"
    CLEANING = "cleaning"
    OUT_OF_SERVICE = "out_of_service"


class ReservationGuest(BaseModel):
    """Guest information"""
    guest_id: Optional[str] = None
    name: str
    email: Optional[str] = None
    phone: str
    vip_status: bool = Field(default=False)
    preferences: Dict[str, Any] = Field(default_factory=dict)
    dietary_restrictions: List[str] = Field(default_factory=list)


class TableInfo(BaseModel):
    """Table information"""
    table_id: str
    table_number: str
    capacity: int
    location: Optional[str] = None  # window, patio, indoor
    shape: Optional[str] = None  # round, square, rectangle


class Reservation(BaseModel):
    """Complete reservation model"""
    id: Optional[str] = None
    reservation_number: str
    business_id: str
    location_id: Optional[str] = None
    
    # Guest information
    guest: ReservationGuest
    party_size: int = Field(ge=1)
    
    # Timing
    reservation_date: date
    reservation_time: time
    duration_minutes: int = Field(default=90)
    
    # Status
    status: ReservationStatus = ReservationStatus.PENDING
    
    # Table assignment
    assigned_table: Optional[TableInfo] = None
    table_preferences: List[str] = Field(default_factory=list)
    
    # Special requests
    occasion: Optional[str] = None  # birthday, anniversary, etc
    special_requests: Optional[str] = None
    
    # Confirmation
    confirmation_code: Optional[str] = None
    confirmed_at: Optional[datetime] = None
    confirmation_sent: bool = Field(default=False)
    
    # Reminders
    reminder_sent: bool = Field(default=False)
    reminder_sent_at: Optional[datetime] = None
    
    # Check-in/out
    checked_in_at: Optional[datetime] = None
    seated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Metadata
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    
    @property
    def is_upcoming(self) -> bool:
        """Check if reservation is upcoming"""
        now = datetime.utcnow()
        reservation_datetime = datetime.combine(self.reservation_date, self.reservation_time)
        return reservation_datetime > now and self.status in [ReservationStatus.PENDING, ReservationStatus.CONFIRMED]


class CreateReservationRequest(BaseModel):
    """Request to create reservation"""
    business_id: str
    guest_name: str
    guest_email: Optional[str] = None
    guest_phone: str
    party_size: int = Field(ge=1)
    reservation_date: str  # ISO date format
    reservation_time: str  # HH:MM format
    duration_minutes: int = Field(default=90)
    occasion: Optional[str] = None
    special_requests: Optional[str] = None
    table_preferences: List[str] = Field(default_factory=list)
    dietary_restrictions: List[str] = Field(default_factory=list)


class UpdateReservationRequest(BaseModel):
    """Request to update reservation"""
    status: Optional[ReservationStatus] = None
    party_size: Optional[int] = None
    reservation_date: Optional[str] = None
    reservation_time: Optional[str] = None
    assigned_table_id: Optional[str] = None
    special_requests: Optional[str] = None
    notes: Optional[str] = None


class Table(BaseModel):
    """Restaurant table model"""
    id: Optional[str] = None
    business_id: str
    location_id: Optional[str] = None
    floor_plan_id: Optional[str] = None
    
    # Table details
    table_number: str
    capacity: int
    min_capacity: int = Field(default=1)
    max_capacity: int
    
    # Visual/Location
    position: Optional[Dict[str, float]] = None  # {x: 0, y: 0}
    shape: str = "rectangle"  # rectangle, round, square
    location_type: Optional[str] = None  # window, patio, bar, private
    
    # Status
    status: TableStatus = TableStatus.AVAILABLE
    current_reservation_id: Optional[str] = None
    current_order_id: Optional[str] = None
    
    # Features
    features: List[str] = Field(default_factory=list)  # booth, highchair, accessible
    
    # Metadata
    notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)


class TableAvailability(BaseModel):
    """Table availability for specific time slot"""
    table_id: str
    table_number: str
    capacity: int
    available: bool
    reason: Optional[str] = None  # If not available, why?


class AvailabilityCheckRequest(BaseModel):
    """Request to check availability"""
    business_id: str
    date: str
    time: str
    party_size: int
    duration_minutes: int = Field(default=90)


class AvailabilityCheckResponse(BaseModel):
    """Response for availability check"""
    available: bool
    available_tables: List[TableAvailability]
    suggested_times: List[str] = Field(default_factory=list)
    message: Optional[str] = None


class ReservationResponse(BaseModel):
    """Reservation API response"""
    reservation: Reservation
    message: str
    confirmation_sent: bool = Field(default=False)


class ReservationListResponse(BaseModel):
    """List of reservations response"""
    reservations: List[Reservation]
    total_count: int
    page: int
    page_size: int
