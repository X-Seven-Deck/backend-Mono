"""
Token models for the Auth Service with Supabase JWT support.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator
from uuid import UUID


class Token(BaseModel):
    """
    Access token response model.
    
    This model represents the standard JWT access token response
    from Supabase Auth.
    """
    access_token: str = Field(
        ...,
        description="JWT access token for API authentication"
    )
    token_type: str = Field(
        "bearer",
        description="Token type (always 'bearer' for JWT)"
    )
    expires_in: int = Field(
        ...,
        description="Number of seconds until the token expires"
    )
    expires_at: Optional[float] = Field(
        None,
        description="Timestamp when the token expires"
    )
    refresh_token: str = Field(
        ...,
        description="Refresh token that can be used to get a new access token"
    )
    user: Optional[dict] = Field(
        None,
        description="User information from the token"
    )

    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600,
                "expires_at": 1672531200,
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "user": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "email": "user@example.com",
                    "role": "user"
                }
            }
        }


class RefreshToken(BaseModel):
    """
    Refresh token request model.
    
    Used for refreshing an expired access token.
    """
    refresh_token: str = Field(
        ...,
        description="Valid refresh token"
    )

    class Config:
        schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class TokenData(BaseModel):
    """
    Token payload data model.
    
    Represents the decoded JWT payload.
    """
    user_id: str = Field(..., alias="sub")
    email: str
    role: str = "user"
    email_confirmed: bool = False
    exp: Optional[datetime] = None
    iat: Optional[datetime] = None
    
    class Config:
        allow_population_by_field_name = True
        
    @validator('exp', 'iat', pre=True)
    def parse_timestamps(cls, v):
        """Parse UNIX timestamps to datetime objects."""
        if isinstance(v, (int, float)):
            return datetime.fromtimestamp(v)
        return v
