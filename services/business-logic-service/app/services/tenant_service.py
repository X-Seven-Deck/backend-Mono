"""
Tenant Management Service

Handles tenant lifecycle, isolation, and resource management.
"""

from typing import Dict, Optional, List
from datetime import datetime, timedelta
from app.models.tenant import (
    TenantContext, TenantRequest, TenantTier, TenantStatus,
    IsolationLevel, ResourceQuota, TenantUsage, TenantMetrics
)
import logging
import httpx

logger = logging.getLogger(__name__)


class TenantService:
    """
    Enterprise Tenant Management Service
    
    Responsibilities:
    - Tenant lifecycle management
    - Isolation strategy enforcement
    - Resource quota management
    - Usage tracking and billing
    """
    
    def __init__(self):
        self._tenants: Dict[str, TenantContext] = {}  # In-memory cache (future: Redis)
        self._usage_tracker: Dict[str, TenantUsage] = {}
        
        # Template Selection Service URL
        self.template_service_url = "http://template-selection-service:8090"
    
    async def create_tenant(self, request: TenantRequest) -> TenantContext:
        """
        Create new tenant with proper isolation and configuration.
        
        Steps:
        1. Determine isolation level based on tier
        2. Create database schema (if needed)
        3. Fetch template configuration
        4. Set resource quotas
        5. Initialize tenant context
        """
        logger.info(f"Creating tenant for business {request.business_id}")
        
        # Determine isolation level
        isolation_level = self._get_isolation_level(request.tier)
        
        # Generate tenant ID
        tenant_id = f"tenant_{request.business_id}"
        
        # Set resource quotas based on tier
        resource_quotas = self._get_resource_quotas(request.tier)
        
        # Fetch template configuration from Template Selection Service
        template_config = await self._fetch_template_config(
            request.business_id,
            request.template_type,
            request.tier
        )
        
        # Create schema if enterprise tier
        schema_name = None
        if isolation_level == IsolationLevel.SCHEMA_PER_TENANT:
            schema_name = await self._create_tenant_schema(tenant_id)
        
        # Create tenant context
        tenant_context = TenantContext(
            tenant_id=tenant_id,
            business_id=request.business_id,
            business_name=request.business_name,
            tier=request.tier,
            status=TenantStatus.ACTIVE,
            isolation_level=isolation_level,
            schema_name=schema_name,
            template_type=request.template_type,
            enabled_features=template_config.get("enabled_features", []),
            resource_quotas=resource_quotas,
            current_usage={},
            data_residency=request.data_residency,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            feature_flags={}
        )
        
        # Cache tenant context
        self._tenants[tenant_id] = tenant_context
        
        # Initialize usage tracking
        self._usage_tracker[tenant_id] = TenantUsage(
            tenant_id=tenant_id,
            period_start=datetime.utcnow(),
            period_end=datetime.utcnow() + timedelta(days=30)
        )
        
        logger.info(
            f"Tenant created: {tenant_id}, tier: {request.tier}, "
            f"isolation: {isolation_level}, template: {request.template_type}"
        )
        
        return tenant_context
    
    async def get_tenant_context(self, tenant_id: str) -> Optional[TenantContext]:
        """
        Get tenant context with caching.
        """
        # Check cache
        if tenant_id in self._tenants:
            return self._tenants[tenant_id]
        
        # Future: Load from database
        logger.warning(f"Tenant {tenant_id} not found in cache")
        return None
    
    async def update_tenant(
        self,
        tenant_id: str,
        updates: Dict
    ) -> TenantContext:
        """
        Update tenant configuration.
        """
        tenant = await self.get_tenant_context(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(tenant, key):
                setattr(tenant, key, value)
        
        tenant.updated_at = datetime.utcnow()
        
        # Update cache
        self._tenants[tenant_id] = tenant
        
        logger.info(f"Tenant {tenant_id} updated: {list(updates.keys())}")
        
        return tenant
    
    async def check_resource_quota(
        self,
        tenant_id: str,
        resource_type: str
    ) -> bool:
        """
        Check if tenant has available quota for resource.
        
        Returns True if quota available, False if exceeded.
        """
        tenant = await self.get_tenant_context(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")
        
        usage = self._usage_tracker.get(tenant_id)
        if not usage:
            return True
        
        quotas = tenant.resource_quotas
        
        # Check specific resource
        quota_checks = {
            "api_call": (usage.api_calls, quotas.max_api_calls_per_day),
            "ai_request": (usage.ai_requests, quotas.max_ai_requests_per_day),
            "storage": (usage.storage_used_gb, quotas.max_storage_gb),
            "workflow": (usage.workflows_executed, quotas.max_concurrent_workflows)
        }
        
        if resource_type in quota_checks:
            current, limit = quota_checks[resource_type]
            if current >= limit:
                logger.warning(
                    f"Quota exceeded for tenant {tenant_id}: "
                    f"{resource_type} ({current}/{limit})"
                )
                return False
        
        return True
    
    async def track_usage(
        self,
        tenant_id: str,
        resource_type: str,
        amount: float = 1.0
    ):
        """
        Track resource usage for billing and quota enforcement.
        """
        if tenant_id not in self._usage_tracker:
            self._usage_tracker[tenant_id] = TenantUsage(
                tenant_id=tenant_id,
                period_start=datetime.utcnow(),
                period_end=datetime.utcnow() + timedelta(days=30)
            )
        
        usage = self._usage_tracker[tenant_id]
        
        # Update usage
        if resource_type == "api_call":
            usage.api_calls += int(amount)
        elif resource_type == "ai_request":
            usage.ai_requests += int(amount)
        elif resource_type == "storage":
            usage.storage_used_gb += amount
        elif resource_type == "workflow":
            usage.workflows_executed += int(amount)
    
    async def get_tenant_usage(self, tenant_id: str) -> Optional[TenantUsage]:
        """Get current usage for tenant"""
        return self._usage_tracker.get(tenant_id)
    
    async def get_tenant_metrics(self, tenant_id: str) -> TenantMetrics:
        """
        Get performance and business metrics for tenant.
        Future: Query from analytics database.
        """
        # Placeholder: Return mock metrics
        return TenantMetrics(
            tenant_id=tenant_id,
            avg_response_time_ms=120.5,
            error_rate=0.01,
            uptime_percent=99.9,
            total_orders=150,
            total_revenue=7500.00,
            active_customers=45,
            daily_active_users=8,
            feature_usage={
                "menu_management": 250,
                "reservations": 120,
                "ai_copilot": 80
            }
        )
    
    def _get_isolation_level(self, tier: TenantTier) -> IsolationLevel:
        """Determine isolation level based on tier"""
        if tier == TenantTier.ENTERPRISE:
            return IsolationLevel.SCHEMA_PER_TENANT
        else:
            return IsolationLevel.ROW_LEVEL_SECURITY
    
    def _get_resource_quotas(self, tier: TenantTier) -> ResourceQuota:
        """Get resource quotas based on tier"""
        quotas = {
            TenantTier.BASIC: ResourceQuota(
                max_users=5,
                max_api_calls_per_day=5000,
                max_storage_gb=5,
                max_ai_requests_per_day=500,
                max_concurrent_workflows=2,
                max_custom_features=2
            ),
            TenantTier.PREMIUM: ResourceQuota(
                max_users=25,
                max_api_calls_per_day=50000,
                max_storage_gb=50,
                max_ai_requests_per_day=5000,
                max_concurrent_workflows=10,
                max_custom_features=5
            ),
            TenantTier.ENTERPRISE: ResourceQuota(
                max_users=-1,  # Unlimited
                max_api_calls_per_day=-1,
                max_storage_gb=-1,
                max_ai_requests_per_day=-1,
                max_concurrent_workflows=-1,
                max_custom_features=-1
            )
        }
        return quotas[tier]
    
    async def _fetch_template_config(
        self,
        business_id: str,
        template_type: str,
        tier: TenantTier
    ) -> Dict:
        """
        Fetch template configuration from Template Selection Service.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.template_service_url}/api/v1/template-selection/templates/{template_type}",
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    config = response.json()
                    
                    # Extract enabled features based on tier
                    enabled_features = [
                        f["feature_type"]
                        for f in config.get("ai_features", [])
                        if self._is_feature_available(f, tier)
                    ]
                    
                    return {
                        "template_type": template_type,
                        "enabled_features": enabled_features,
                        "api_endpoints": config.get("api_endpoints", []),
                        "workflows": config.get("langgraph_workflows", [])
                    }
                else:
                    logger.error(f"Failed to fetch template config: {response.status_code}")
                    return {"enabled_features": []}
        except Exception as e:
            logger.error(f"Error fetching template config: {e}")
            return {"enabled_features": []}
    
    def _is_feature_available(self, feature: Dict, tier: TenantTier) -> bool:
        """Check if feature is available for tier"""
        tier_hierarchy = {"basic": 1, "premium": 2, "enterprise": 3}
        feature_min_tier = feature.get("min_tier", "basic")
        
        return tier_hierarchy.get(tier.value, 1) >= tier_hierarchy.get(feature_min_tier, 1)
    
    async def _create_tenant_schema(self, tenant_id: str) -> str:
        """
        Create dedicated database schema for enterprise tenant.
        Future: Execute actual DDL.
        """
        schema_name = f"tenant_{tenant_id}"
        
        # Future: Execute CREATE SCHEMA statement
        logger.info(f"Created schema: {schema_name}")
        
        return schema_name


# Singleton instance
_tenant_service = None

def get_tenant_service() -> TenantService:
    """Get singleton instance of TenantService"""
    global _tenant_service
    if _tenant_service is None:
        _tenant_service = TenantService()
    return _tenant_service
