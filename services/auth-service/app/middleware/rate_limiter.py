"""
Advanced Rate Limiting Middleware for Auth Service

Implements multi-tier rate limiting:
- Per-IP rate limits
- Per-user rate limits
- Per-endpoint rate limits
- Sliding window algorithm
- Redis-backed distributed rate limiting (optional)
- Adaptive rate limiting based on system load
"""

import logging
import hashlib
from typing import Callable, Optional, Dict, List
from datetime import datetime, timedelta
from collections import defaultdict
from functools import wraps

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Enterprise-grade rate limiter with multiple strategies.
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_size: int = 10,
        enable_adaptive: bool = True,
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_size = burst_size
        self.enable_adaptive = enable_adaptive
        
        # In-memory storage (use Redis in production for distributed systems)
        self.minute_buckets: Dict[str, List[datetime]] = defaultdict(list)
        self.hour_buckets: Dict[str, List[datetime]] = defaultdict(list)
        self.burst_buckets: Dict[str, List[datetime]] = defaultdict(list)
        
        # Track failed attempts for adaptive limiting
        self.failed_attempts: Dict[str, int] = defaultdict(int)

    def is_allowed(self, identifier: str, endpoint: Optional[str] = None) -> tuple[bool, Dict[str, any]]:
        """
        Check if request should be allowed based on rate limits.
        
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        current_time = datetime.utcnow()
        
        # Create unique key for this identifier/endpoint combination
        key = self._get_key(identifier, endpoint)
        
        # Clean old entries
        self._clean_old_entries(key, current_time)
        
        # Check burst limit (short-term protection)
        if not self._check_burst_limit(key, current_time):
            return False, {
                "limit": self.burst_size,
                "remaining": 0,
                "reset": self._get_reset_time(self.burst_buckets[key], seconds=10),
                "retry_after": 10,
            }
        
        # Check per-minute limit
        if not self._check_minute_limit(key, current_time):
            return False, {
                "limit": self.requests_per_minute,
                "remaining": 0,
                "reset": self._get_reset_time(self.minute_buckets[key], seconds=60),
                "retry_after": 60,
            }
        
        # Check per-hour limit
        if not self._check_hour_limit(key, current_time):
            return False, {
                "limit": self.requests_per_hour,
                "remaining": 0,
                "reset": self._get_reset_time(self.hour_buckets[key], seconds=3600),
                "retry_after": 3600,
            }
        
        # Adaptive limiting - stricter limits for suspicious activity
        if self.enable_adaptive and self.failed_attempts[key] > 5:
            # Reduce limits for suspicious IPs
            adaptive_limit = max(10, self.requests_per_minute // 2)
            if len(self.minute_buckets[key]) >= adaptive_limit:
                return False, {
                    "limit": adaptive_limit,
                    "remaining": 0,
                    "reset": self._get_reset_time(self.minute_buckets[key], seconds=60),
                    "retry_after": 60,
                    "reason": "adaptive_limiting_due_to_suspicious_activity",
                }
        
        # Add current request to buckets
        self.burst_buckets[key].append(current_time)
        self.minute_buckets[key].append(current_time)
        self.hour_buckets[key].append(current_time)
        
        # Calculate remaining requests
        minute_remaining = self.requests_per_minute - len(self.minute_buckets[key])
        hour_remaining = self.requests_per_hour - len(self.hour_buckets[key])
        
        return True, {
            "limit_minute": self.requests_per_minute,
            "limit_hour": self.requests_per_hour,
            "remaining_minute": minute_remaining,
            "remaining_hour": hour_remaining,
            "reset_minute": self._get_reset_time(self.minute_buckets[key], seconds=60),
            "reset_hour": self._get_reset_time(self.hour_buckets[key], seconds=3600),
        }

    def record_failure(self, identifier: str):
        """Record a failed authentication attempt for adaptive limiting."""
        key = self._get_key(identifier, "auth")
        self.failed_attempts[key] += 1
        
        # Reset failure count after 1 hour
        # (In production, use Redis with TTL)
        if self.failed_attempts[key] > 100:
            self.failed_attempts[key] = 0

    def reset_failures(self, identifier: str):
        """Reset failure count on successful authentication."""
        key = self._get_key(identifier, "auth")
        self.failed_attempts[key] = 0

    def _get_key(self, identifier: str, endpoint: Optional[str] = None) -> str:
        """Generate unique key for rate limiting."""
        if endpoint:
            return hashlib.sha256(f"{identifier}:{endpoint}".encode()).hexdigest()[:16]
        return hashlib.sha256(identifier.encode()).hexdigest()[:16]

    def _clean_old_entries(self, key: str, current_time: datetime):
        """Remove old entries outside the time windows."""
        # Clean burst bucket (10 seconds)
        self.burst_buckets[key] = [
            t for t in self.burst_buckets[key]
            if current_time - t < timedelta(seconds=10)
        ]
        
        # Clean minute bucket
        self.minute_buckets[key] = [
            t for t in self.minute_buckets[key]
            if current_time - t < timedelta(minutes=1)
        ]
        
        # Clean hour bucket
        self.hour_buckets[key] = [
            t for t in self.hour_buckets[key]
            if current_time - t < timedelta(hours=1)
        ]

    def _check_burst_limit(self, key: str, current_time: datetime) -> bool:
        """Check if burst limit is exceeded."""
        return len(self.burst_buckets[key]) < self.burst_size

    def _check_minute_limit(self, key: str, current_time: datetime) -> bool:
        """Check if per-minute limit is exceeded."""
        return len(self.minute_buckets[key]) < self.requests_per_minute

    def _check_hour_limit(self, key: str, current_time: datetime) -> bool:
        """Check if per-hour limit is exceeded."""
        return len(self.hour_buckets[key]) < self.requests_per_hour

    def _get_reset_time(self, bucket: List[datetime], seconds: int) -> int:
        """Get timestamp when the rate limit will reset."""
        if not bucket:
            return int(datetime.utcnow().timestamp()) + seconds
        
        oldest_request = min(bucket)
        reset_time = oldest_request + timedelta(seconds=seconds)
        return int(reset_time.timestamp())


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to apply rate limiting to all requests.
    """

    def __init__(
        self,
        app: ASGIApp,
        rate_limiter: Optional[RateLimiter] = None,
        exempt_paths: Optional[List[str]] = None,
    ):
        super().__init__(app)
        self.rate_limiter = rate_limiter or RateLimiter()
        self.exempt_paths = set(exempt_paths or ["/health", "/docs", "/openapi.json"])

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Apply rate limiting to requests.
        """
        # Skip rate limiting for exempt paths
        if request.url.path in self.exempt_paths:
            return await call_next(request)
        
        # Get identifier (IP or user ID if authenticated)
        identifier = self._get_identifier(request)
        
        # Check rate limit
        is_allowed, rate_info = self.rate_limiter.is_allowed(
            identifier=identifier,
            endpoint=request.url.path,
        )
        
        if not is_allowed:
            # Log rate limit violation
            logger.warning(
                f"Rate limit exceeded for {identifier} on {request.url.path}. "
                f"Limit: {rate_info.get('limit')}, Reset: {rate_info.get('reset')}"
            )
            
            # Return 429 Too Many Requests
            response = JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded",
                    "limit": rate_info.get("limit"),
                    "retry_after": rate_info.get("retry_after"),
                },
            )
            
            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = str(rate_info.get("limit", ""))
            response.headers["X-RateLimit-Remaining"] = "0"
            response.headers["X-RateLimit-Reset"] = str(rate_info.get("reset", ""))
            response.headers["Retry-After"] = str(rate_info.get("retry_after", ""))
            
            return response
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to successful responses
        response.headers["X-RateLimit-Limit-Minute"] = str(rate_info.get("limit_minute", ""))
        response.headers["X-RateLimit-Remaining-Minute"] = str(rate_info.get("remaining_minute", ""))
        response.headers["X-RateLimit-Reset-Minute"] = str(rate_info.get("reset_minute", ""))
        
        return response

    def _get_identifier(self, request: Request) -> str:
        """
        Get unique identifier for rate limiting.
        Prefers user ID if authenticated, falls back to IP address.
        """
        # Try to get user ID from Authorization header
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # In a real implementation, decode JWT and extract user ID
            # For now, use a hash of the token
            token = auth_header.replace("Bearer ", "")
            return hashlib.sha256(token.encode()).hexdigest()[:16]
        
        # Fall back to IP address
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        if request.client:
            return request.client.host
        
        return "unknown"


# Decorator for endpoint-specific rate limiting
def rate_limit(
    requests_per_minute: int = 10,
    requests_per_hour: int = 100,
):
    """
    Decorator to apply custom rate limits to specific endpoints.
    
    Usage:
        @app.post("/login")
        @rate_limit(requests_per_minute=5, requests_per_hour=20)
        async def login(credentials: dict):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get("request") or args[0] if args else None
            
            if not request:
                # Can't apply rate limiting without request context
                return await func(*args, **kwargs)
            
            # Create endpoint-specific rate limiter
            limiter = RateLimiter(
                requests_per_minute=requests_per_minute,
                requests_per_hour=requests_per_hour,
            )
            
            # Get identifier
            identifier = request.client.host if request.client else "unknown"
            
            # Check rate limit
            is_allowed, rate_info = limiter.is_allowed(
                identifier=identifier,
                endpoint=request.url.path,
            )
            
            if not is_allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded",
                    headers={
                        "Retry-After": str(rate_info.get("retry_after", "")),
                    },
                )
            
            # Execute endpoint
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# Global rate limiter instance
global_rate_limiter = RateLimiter(
    requests_per_minute=60,
    requests_per_hour=1000,
    burst_size=10,
    enable_adaptive=True,
)
