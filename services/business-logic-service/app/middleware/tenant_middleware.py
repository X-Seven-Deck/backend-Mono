"""
Tenant Context Middleware

Extracts and validates tenant context for every request.
Enforces resource quotas and isolation.
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from app.services.tenant_service import get_tenant_service
import logging

logger = logging.getLogger(__name__)


class TenantContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract and validate tenant context.
    
    Responsibilities:
    - Extract tenant_id from request (header, JWT, or path)
    - Load tenant context
    - Validate tenant status
    - Check resource quotas
    - Attach context to request state
    """
    
    async def dispatch(self, request: Request, call_next):
        # Skip middleware for health and docs endpoints
        if request.url.path in ["/health", "/health/live", "/health/ready", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Extract tenant_id from header or JWT
        tenant_id = self._extract_tenant_id(request)
        
        if not tenant_id:
            # For public endpoints, continue without tenant context
            if self._is_public_endpoint(request.url.path):
                return await call_next(request)
            
            logger.warning(f"No tenant_id found for {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tenant identification required"
            )
        
        # Load tenant context
        tenant_service = get_tenant_service()
        tenant_context = await tenant_service.get_tenant_context(tenant_id)
        
        if not tenant_context:
            logger.error(f"Tenant {tenant_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant {tenant_id} not found"
            )
        
        # Validate tenant status
        if tenant_context.status != "active":
            logger.warning(f"Tenant {tenant_id} is {tenant_context.status}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Tenant is {tenant_context.status}"
            )
        
        # Check resource quotas for write operations
        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            quota_available = await tenant_service.check_resource_quota(
                tenant_id,
                "api_call"
            )
            
            if not quota_available:
                logger.warning(f"Quota exceeded for tenant {tenant_id}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Resource quota exceeded. Please upgrade your plan."
                )
        
        # Attach tenant context to request state
        request.state.tenant_context = tenant_context
        request.state.tenant_id = tenant_id
        
        # Track usage
        await tenant_service.track_usage(tenant_id, "api_call", 1.0)
        
        # Process request
        response = await call_next(request)
        
        # Add tenant info to response headers (for debugging)
        response.headers["X-Tenant-ID"] = tenant_id
        response.headers["X-Tenant-Tier"] = tenant_context.tier.value
        
        return response
    
    def _extract_tenant_id(self, request: Request) -> str:
        """
        Extract tenant_id from request.
        Priority: Header > JWT > Query Param
        """
        # 1. Check X-Tenant-ID header
        tenant_id = request.headers.get("X-Tenant-ID")
        if tenant_id:
            return tenant_id
        
        # 2. Check Authorization header (JWT)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # Future: Decode JWT and extract tenant_id
            # For now, extract from custom claim
            pass
        
        # 3. Check query parameter
        tenant_id = request.query_params.get("tenant_id")
        if tenant_id:
            return tenant_id
        
        # 4. Check path parameter (e.g., /api/v1/tenants/{tenant_id}/...)
        path_parts = request.url.path.split("/")
        if "tenants" in path_parts:
            try:
                tenant_index = path_parts.index("tenants") + 1
                if tenant_index < len(path_parts):
                    return path_parts[tenant_index]
            except (ValueError, IndexError):
                pass
        
        return None
    
    def _is_public_endpoint(self, path: str) -> bool:
        """Check if endpoint is public (no tenant required)"""
        public_endpoints = [
            "/",
            "/health",
            "/metrics",
            "/api/v1/tenants"  # Tenant creation endpoint
        ]
        return path in public_endpoints or path.startswith("/docs") or path.startswith("/redoc")


class ResourceQuotaMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce resource quotas per tenant.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Skip for non-tenant requests
        if not hasattr(request.state, "tenant_context"):
            return await call_next(request)
        
        tenant_context = request.state.tenant_context
        tenant_service = get_tenant_service()
        
        # Determine resource type based on endpoint
        resource_type = self._get_resource_type(request.url.path)
        
        if resource_type:
            quota_available = await tenant_service.check_resource_quota(
                tenant_context.tenant_id,
                resource_type
            )
            
            if not quota_available:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"{resource_type} quota exceeded"
                )
        
        return await call_next(request)
    
    def _get_resource_type(self, path: str) -> str:
        """Determine resource type from path"""
        if "/ai/" in path or "/copilot" in path:
            return "ai_request"
        elif "/workflows/" in path:
            return "workflow"
        elif "/upload" in path or "/storage" in path:
            return "storage"
        return None
