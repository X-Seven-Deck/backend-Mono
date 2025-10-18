"""
Tenant Management Routes

API endpoints for tenant lifecycle management.
"""

from fastapi import APIRouter, HTTPException, status, Request
from typing import Optional
from app.models.tenant import TenantRequest, TenantContext, TenantUsage, TenantMetrics
from app.services.tenant_service import get_tenant_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/tenants", tags=["Tenant Management"])


@router.post("", response_model=TenantContext, status_code=status.HTTP_201_CREATED)
async def create_tenant(request: TenantRequest):
    """
    Create new tenant with proper isolation and configuration.
    
    This endpoint:
    1. Determines isolation level based on tier
    2. Creates database schema (if enterprise)
    3. Fetches template configuration
    4. Sets resource quotas
    5. Initializes tenant context
    """
    try:
        service = get_tenant_service()
        tenant_context = await service.create_tenant(request)
        return tenant_context
    except Exception as e:
        logger.error(f"Error creating tenant: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating tenant: {str(e)}"
        )


@router.get("/{tenant_id}", response_model=TenantContext)
async def get_tenant(tenant_id: str):
    """
    Get tenant context and configuration.
    """
    try:
        service = get_tenant_service()
        tenant_context = await service.get_tenant_context(tenant_id)
        
        if not tenant_context:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant {tenant_id} not found"
            )
        
        return tenant_context
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching tenant: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching tenant: {str(e)}"
        )


@router.put("/{tenant_id}", response_model=TenantContext)
async def update_tenant(tenant_id: str, updates: dict):
    """
    Update tenant configuration.
    
    Allowed updates:
    - status
    - tier (with migration)
    - enabled_features
    - feature_flags
    - custom_config
    """
    try:
        service = get_tenant_service()
        tenant_context = await service.update_tenant(tenant_id, updates)
        return tenant_context
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating tenant: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating tenant: {str(e)}"
        )


@router.get("/{tenant_id}/usage", response_model=TenantUsage)
async def get_tenant_usage(tenant_id: str):
    """
    Get current resource usage for tenant.
    
    Returns:
    - API calls
    - AI requests
    - Storage used
    - Active users
    - Workflows executed
    - Quota exceeded flags
    """
    try:
        service = get_tenant_service()
        usage = await service.get_tenant_usage(tenant_id)
        
        if not usage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usage data not found for tenant {tenant_id}"
            )
        
        return usage
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching usage: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching usage: {str(e)}"
        )


@router.get("/{tenant_id}/metrics", response_model=TenantMetrics)
async def get_tenant_metrics(tenant_id: str):
    """
    Get performance and business metrics for tenant.
    
    Returns:
    - Performance metrics (response time, error rate, uptime)
    - Business metrics (orders, revenue, customers)
    - Engagement metrics (DAU, feature usage)
    """
    try:
        service = get_tenant_service()
        metrics = await service.get_tenant_metrics(tenant_id)
        return metrics
    except Exception as e:
        logger.error(f"Error fetching metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching metrics: {str(e)}"
        )


@router.post("/{tenant_id}/quota-check")
async def check_quota(tenant_id: str, resource_type: str):
    """
    Check if tenant has available quota for resource.
    
    Resource types:
    - api_call
    - ai_request
    - storage
    - workflow
    """
    try:
        service = get_tenant_service()
        available = await service.check_resource_quota(tenant_id, resource_type)
        
        return {
            "tenant_id": tenant_id,
            "resource_type": resource_type,
            "quota_available": available
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error checking quota: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking quota: {str(e)}"
        )


@router.get("/context/current", response_model=TenantContext)
async def get_current_tenant_context(request: Request):
    """
    Get current tenant context from request.
    
    Useful for debugging and validation.
    """
    if not hasattr(request.state, "tenant_context"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No tenant context in request"
        )
    
    return request.state.tenant_context
