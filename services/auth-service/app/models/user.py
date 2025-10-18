"""
User models for the Auth Service.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, validator, constr, root_validator, model_validator
# Password constraints
PASSWORD_MIN_LENGTH = 12
PASSWORD_MAX_LENGTH = 128


class UserBase(BaseModel):
    """Base user model with common fields."""
    email: EmailStr = Field(..., description="User's email address")
    full_name: Optional[str] = Field(
        None,
        max_length=100,
        description="User's full name"
    )
    phone_number: Optional[str] = Field(
        None,
        pattern=r'^\+?[1-9]\d{1,14}$',
        description="User's phone number in E.164 format"
    )
    avatar_url: Optional[str] = Field(
        None,
        description="URL to user's avatar image"
    )
    role: str = Field(
        "business_owner",
        description="User's role in the system"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional user metadata"
    )


class UserCreate(UserBase):
    """User creation model with password validation."""
    password: constr(
        min_length=PASSWORD_MIN_LENGTH,
        max_length=PASSWORD_MAX_LENGTH
    ) = Field(..., description="User's password")
    
    confirm_password: str = Field(..., description="Password confirmation")
    
    @validator('password')
    def validate_password_strength(cls, v):
        """Ensure password meets security requirements."""
        if len(v) < PASSWORD_MIN_LENGTH:
            raise ValueError(f'Password must be at least {PASSWORD_MIN_LENGTH} characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?/' for c in v):
            raise ValueError('Password must contain at least one special character')
        return v
    
    @model_validator(mode='before')
    @classmethod
    def passwords_match(cls, values):
        """Ensure password and confirmation match."""
        password = values.get('password')
        confirm_password = values.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            raise ValueError('passwords do not match')
        return values


class UserLogin(BaseModel):
    """User login model with rate limiting support."""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")
    remember_me: bool = Field(
        False,
        description="Whether to create a long-lived session"
    )


class UserUpdate(BaseModel):
    """User update model with validation."""
    email: Optional[EmailStr] = Field(
        None,
        description="New email address"
    )
    full_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Updated full name"
    )
    phone_number: Optional[str] = Field(
        None,
        pattern=r'^\+?[1-9]\d{1,14}$',
        description="Updated phone number in E.164 format"
    )
    avatar_url: Optional[str] = Field(
        None,
        description="Updated avatar URL"
    )
    role: Optional[str] = Field(
        None,
        description="Updated user role"
    )
    current_password: Optional[str] = Field(
        None,
        description="Current password for verification"
    )
    new_password: Optional[str] = Field(
        None,
        min_length=PASSWORD_MIN_LENGTH,
        max_length=PASSWORD_MAX_LENGTH,
        description="New password"
    )
    confirm_password: Optional[str] = Field(
        None,
        description="New password confirmation"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata to update"
    )
    
    @model_validator(mode='before')
    @classmethod
    def validate_password_update(cls, values):
        """Validate password update fields."""
        new_password = values.get('new_password')
        confirm_password = values.get('confirm_password')
        current_password = values.get('current_password')
        
        # If trying to update password, all password fields are required
        if any([new_password, confirm_password, current_password]):
            if not all([new_password, confirm_password, current_password]):
                raise ValueError('current_password, new_password, and confirm_password are all required for password updates')
            
            if new_password != confirm_password:
                raise ValueError('new_password and confirm_password do not match')
                
        return values


class UserResponse(UserBase):
    """User response model with additional metadata."""
    id: UUID = Field(..., description="User's unique identifier")
    email_confirmed: bool = Field(
        False,
        description="Whether the user's email has been confirmed"
    )
    last_sign_in_at: Optional[datetime] = Field(
        None,
        description="Timestamp of last successful sign-in"
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when the user was created"
    )
    updated_at: datetime = Field(
        ...,
        description="Timestamp when the user was last updated"
    )
    is_active: bool = Field(
        True,
        description="Whether the user account is active"
    )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "full_name": "John Doe",
                "phone_number": "+1234567890",
                "avatar_url": "https://example.com/avatar.jpg",
                "role": "customer",
                "email_confirmed": True,
                "last_sign_in_at": "2023-01-01T12:00:00Z",
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T12:00:00Z",
                "is_active": True
            }
        }
        from_attributes = True
