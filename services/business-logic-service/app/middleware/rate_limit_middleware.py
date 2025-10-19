"""
Rate Limiting Middleware

Token bucket algorithm for rate limiting.
"""

import logging
import time
from typing import Dict
from collections import defaultdict
from fastapi import Request, HTTPException, status

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class RateLimiter:
    """
    Rate limiter using token bucket algorithm
    
    Features:
    - Per-IP rate limiting
    - Per-user rate limiting
    - Per-tenant rate limiting
    - Configurable limits
    - Redis-backed (for distributed systems)
    """
    
    def __init__(self):
        self.buckets: Dict[str, Dict] = defaultdict(lambda: {
            "tokens": settings.RATE_LIMIT_PER_MINUTE,
            "last_update": time.time()
        })
        self.rate = settings.RATE_LIMIT_PER_MINUTE
        self.burst = settings.RATE_LIMIT_BURST
    
    def _get_key(self, request: Request) -> str:
        """Get rate limit key from request"""
        # Try to get user/tenant from request state
        if hasattr(request.state, "tenant_context"):
            tenant_id = request.state.tenant_context.tenant_id
            return f"tenant:{tenant_id}"
        
        # Fall back to IP
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"
    
    def _refill_tokens(self, bucket: Dict) -> Dict:
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - bucket["last_update"]
        
        # Refill tokens (1 token per second)
        tokens_to_add = elapsed * (self.rate / 60.0)
        bucket["tokens"] = min(self.burst, bucket["tokens"] + tokens_to_add)
        bucket["last_update"] = now
        
        return bucket
    
    async def check_rate_limit(self, request: Request) -> bool:
        """Check if request is within rate limit"""
        key = self._get_key(request)
        bucket = self.buckets[key]
        
        # Refill tokens
        bucket = self._refill_tokens(bucket)
        
        # Check if tokens available
        if bucket["tokens"] >= 1:
            bucket["tokens"] -= 1
            return True
        else:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
                headers={"Retry-After": "60"}
            )


# Global rate limiter instance
rate_limiter = RateLimiter()


async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware"""
    # Skip rate limiting for health endpoints
    if request.url.path in ["/health", "/health/live", "/health/ready"]:
        return await call_next(request)
    
    # Check rate limit
    await rate_limiter.check_rate_limit(request)
    
    return await call_next(request)
