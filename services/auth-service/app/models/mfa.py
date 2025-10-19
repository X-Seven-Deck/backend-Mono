"""
Multi-Factor Authentication (MFA) Models for Auth Service

Supports:
- TOTP (Time-based One-Time Password)
- SMS/Email OTP
- Backup codes
- Recovery codes
"""

from typing import Optional, List
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, validator


class MFASetupRequest(BaseModel):
    """Request to setup MFA for a user."""
    method: str = Field(..., description="MFA method: totp, sms, email")
    phone_number: Optional[str] = Field(None, description="Phone number for SMS")
    
    @validator('method')
    def validate_method(cls, v):
        allowed_methods = ['totp', 'sms', 'email']
        if v not in allowed_methods:
            raise ValueError(f'Method must be one of: {", ".join(allowed_methods)}')
        return v


class MFASetupResponse(BaseModel):
    """Response containing MFA setup information."""
    secret: Optional[str] = Field(None, description="TOTP secret (only for TOTP)")
    qr_code: Optional[str] = Field(None, description="QR code data URL (only for TOTP)")
    backup_codes: List[str] = Field(..., description="Backup codes for account recovery")
    method: str = Field(..., description="MFA method configured")


class MFAVerifyRequest(BaseModel):
    """Request to verify MFA code."""
    code: str = Field(..., description="MFA code to verify", min_length=6, max_length=8)
    method: Optional[str] = Field(None, description="MFA method (auto-detected if not provided)")


class MFADisableRequest(BaseModel):
    """Request to disable MFA."""
    password: str = Field(..., description="User password for verification")
    code: Optional[str] = Field(None, description="Current MFA code for verification")


class BackupCodeUseRequest(BaseModel):
    """Request to use a backup code."""
    code: str = Field(..., description="Backup code")


class MFAStatusResponse(BaseModel):
    """Response containing user's MFA status."""
    enabled: bool = Field(..., description="Whether MFA is enabled")
    methods: List[str] = Field(..., description="List of enabled MFA methods")
    backup_codes_remaining: int = Field(..., description="Number of unused backup codes")
    last_verified: Optional[datetime] = Field(None, description="Last MFA verification time")


class TOTPSecret(BaseModel):
    """TOTP secret configuration."""
    user_id: UUID
    secret: str
    created_at: datetime
    last_verified: Optional[datetime] = None
    is_active: bool = True


class BackupCode(BaseModel):
    """Backup code for MFA recovery."""
    user_id: UUID
    code: str
    used: bool = False
    used_at: Optional[datetime] = None
    created_at: datetime
