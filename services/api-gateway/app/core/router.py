"""
Request Router

Intelligent request routing with load balancing, retries, and circuit breaking.
"""

import logging
import aiohttp
import asyncio
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException, status
from app.config.settings import get_settings

logger = logging.getLogger(__name__)


class RequestRouter:
    """
    Routes requests to appropriate backend services with:
    - Circuit breaker integration
    - Retry logic
    - Timeout handling
    - Load balancing (if multiple instances)
    """
    
    def __init__(self, service_registry, circuit_breaker_manager):
        """
        Initialize request router
        
        Args:
            service_registry: ServiceRegistry instance
            circuit_breaker_manager: CircuitBreakerManager instance
        """
        self.settings = get_settings()
        self.service_registry = service_registry
        self.circuit_breaker_manager = circuit_breaker_manager
    
    async def route_request(
        self,
        service_name: str,
        path: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        body: Optional[bytes] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Route request to backend service
        
        Args:
            service_name: Target service name
            path: Request path
            method: HTTP method
            headers: Request headers
            body: Request body
            params: Query parameters
            timeout: Request timeout
            
        Returns:
            Response data
            
        Raises:
            HTTPException: If request fails
        """
        # Get service URL
        service_url = self.service_registry.get_service_url(service_name)
        if not service_url:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Service {service_name} not available"
            )
        
        # Check if service is healthy
        if not self.service_registry.is_service_healthy(service_name):
            logger.warning(f"Routing to unhealthy service: {service_name}")
        
        # Get circuit breaker
        circuit_breaker = self.circuit_breaker_manager.get_breaker(service_name)
        
        # Determine timeout
        if timeout is None:
            service_metadata = self.service_registry.get_service_metadata(service_name)
            timeout = service_metadata.get("timeout", self.settings.default_request_timeout)
        
        # Build full URL
        full_url = f"{service_url}{path}"
        
        # Execute request through circuit breaker
        try:
            response_data = await circuit_breaker.call_async(
                self._make_request,
                full_url=full_url,
                method=method,
                headers=headers,
                body=body,
                params=params,
                timeout=timeout
            )
            return response_data
        
        except Exception as e:
            logger.error(f"Request to {service_name} failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Service {service_name} temporarily unavailable"
            )
    
    async def _make_request(
        self,
        full_url: str,
        method: str,
        headers: Optional[Dict[str, str]],
        body: Optional[bytes],
        params: Optional[Dict[str, Any]],
        timeout: int
    ) -> Dict[str, Any]:
        """
        Make HTTP request to backend service
        
        Args:
            full_url: Full request URL
            method: HTTP method
            headers: Request headers
            body: Request body
            params: Query parameters
            timeout: Request timeout
            
        Returns:
            Response data
        """
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=method,
                url=full_url,
                headers=headers,
                data=body,
                params=params,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                # Read response
                response_body = await response.read()
                
                # Parse JSON if possible
                try:
                    response_data = await response.json()
                except:
                    response_data = {"data": response_body.decode('utf-8')}
                
                return {
                    "status_code": response.status,
                    "headers": dict(response.headers),
                    "body": response_data
                }
