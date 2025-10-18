"""
Multi-Tenancy Models

Enterprise-grade tenant isolation and context management.
"""

from pydantic import BaseModel, Field
from typing import Dict, Optional, List, Any
from enum import Enum
from datetime import datetime


class IsolationLevel(str, Enum):
    """Tenant Isolation Levels"""
    SCHEMA_PER_TENANT = "schema_per_tenant"  # Enterprise: Dedicated schema
    ROW_LEVEL_SECURITY = "row_level_security"  # Premium/Basic: Shared schema with RLS


class TenantTier(str, Enum):
    """Tenant Subscription Tiers"""
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class TenantStatus(str, Enum):
    """Tenant Status"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    CHURNED = "churned"


class ResourceQuota(BaseModel):
    """Resource Quotas per Tenant"""
    max_users: int = 10
    max_api_calls_per_day: int = 10000
    max_storage_gb: int = 10
    max_ai_requests_per_day: int = 1000
    max_concurrent_workflows: int = 5
    max_custom_features: int = 2


class TenantContext(BaseModel):
    """Complete Tenant Context"""
    tenant_id: str
    business_id: str
    business_name: str
    
    # Tier and Status
    tier: TenantTier
    status: TenantStatus
    
    # Isolation
    isolation_level: IsolationLevel
    schema_name: Optional[str] = None  # For schema-per-tenant
    
    # Template Configuration
    template_type: str
    enabled_features: List[str] = Field(default_factory=list)
    
    # Resource Management
    resource_quotas: ResourceQuota
    current_usage: Dict[str, Any] = Field(default_factory=dict)
    
    # Security
    encryption_key_id: Optional[str] = None
    data_residency: str = "us-east-1"  # Geographic data location
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    last_active_at: Optional[datetime] = None
    
    # Feature Flags
    feature_flags: Dict[str, bool] = Field(default_factory=dict)
    
    # Custom Configuration
    custom_config: Dict[str, Any] = Field(default_factory=dict)


class TenantRequest(BaseModel):
    """Request to create or update tenant"""
    business_id: str
    business_name: str
    tier: TenantTier
    template_type: str
    data_residency: Optional[str] = "us-east-1"


class TenantUsage(BaseModel):
    """Tenant Resource Usage"""
    tenant_id: str
    period_start: datetime
    period_end: datetime
    
    api_calls: int = 0
    ai_requests: int = 0
    storage_used_gb: float = 0.0
    active_users: int = 0
    workflows_executed: int = 0
    
    quota_exceeded: List[str] = Field(default_factory=list)


class TenantMetrics(BaseModel):
    """Tenant Performance Metrics"""
    tenant_id: str
    
    # Performance
    avg_response_time_ms: float
    error_rate: float
    uptime_percent: float
    
    # Business Metrics
    total_orders: int = 0
    total_revenue: float = 0.0
    active_customers: int = 0
    
    # Engagement
    daily_active_users: int = 0
    feature_usage: Dict[str, int] = Field(default_factory=dict)
