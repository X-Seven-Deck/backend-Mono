"""
Business models for the Auth Service.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field, HttpUrl
from uuid import UUID
from datetime import datetime
from enum import Enum

class BusinessCategory(str, Enum):
    """Business category enumeration."""
    RESTAURANT = "restaurant"
    SALON = "salon"
    FREELANCING = "freelancing"
    LOCAL_SHOP = "local_shop"
    OTHER = "other"

class BusinessBase(BaseModel):
    """Base business model."""
    name: str
    description: Optional[str] = None
    category: Optional[BusinessCategory] = BusinessCategory.OTHER
    business_type: Optional[str] = None  # Alternative to category
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[HttpUrl] = None
    logo_url: Optional[HttpUrl] = None
    operating_hours: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None

class BusinessCreate(BusinessBase):
    """Business creation model."""
    owner_id: Optional[UUID] = None  # Will be set from current user if not provided

class BusinessUpdate(BaseModel):
    """Business update model."""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[BusinessCategory] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[HttpUrl] = None
    logo_url: Optional[HttpUrl] = None
    operating_hours: Optional[Dict[str, Any]] = None

class BusinessProfile(BusinessBase):
    """Business profile model."""
    id: UUID
    owner_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BusinessResponse(BaseModel):
    """Business response model."""
    id: UUID
    name: str
    slug: Optional[str] = None
    category_id: Optional[int] = None
    status: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
