"""
Enterprise Security Middleware for Auth Service

Implements comprehensive security controls including:
- Security headers (HSTS, CSP, X-Frame-Options, etc.)
- Request validation and sanitization
- IP whitelisting/blacklisting
- DDoS protection
- Request size limits
- CORS enhancements
"""

import logging
import re
from typing import Callable, Optional, List, Dict, Any
from datetime import datetime, timedelta

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

# Security configuration
MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
SUSPICIOUS_PATTERNS = [
    r"<script",
    r"javascript:",
    r"onerror=",
    r"onload=",
    r"\.\./",  # Path traversal
    r"union\s+select",  # SQL injection
    r"exec\s*\(",  # Command injection
]


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Enterprise-grade security middleware with multiple protection layers.
    """

    def __init__(
        self,
        app: ASGIApp,
        allowed_ips: Optional[List[str]] = None,
        blocked_ips: Optional[List[str]] = None,
        enable_csp: bool = True,
        enable_hsts: bool = True,
        enable_request_validation: bool = True,
    ):
        super().__init__(app)
        self.allowed_ips = set(allowed_ips or [])
        self.blocked_ips = set(blocked_ips or [])
        self.enable_csp = enable_csp
        self.enable_hsts = enable_hsts
        self.enable_request_validation = enable_request_validation
        
        # Compile suspicious patterns for efficiency
        self.suspicious_patterns = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in SUSPICIOUS_PATTERNS
        ]
        
        # Track request statistics for DDoS detection
        self.request_stats: Dict[str, List[datetime]] = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request through security checks.
        """
        try:
            # 1. IP-based access control
            client_ip = self._get_client_ip(request)
            
            if not self._check_ip_access(client_ip):
                logger.warning(f"Blocked request from {client_ip}")
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": "Access denied"},
                )

            # 2. Method validation
            if request.method not in ALLOWED_METHODS:
                return JSONResponse(
                    status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                    content={"detail": "Method not allowed"},
                )

            # 3. Request size validation
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > MAX_REQUEST_SIZE:
                logger.warning(f"Request too large: {content_length} bytes from {client_ip}")
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={"detail": "Request too large"},
                )

            # 4. Request validation (XSS, SQL injection, etc.)
            if self.enable_request_validation:
                if not await self._validate_request(request):
                    logger.error(f"Suspicious request detected from {client_ip}")
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content={"detail": "Invalid request"},
                    )

            # 5. DDoS protection - simple rate-based detection
            if not self._check_request_rate(client_ip):
                logger.warning(f"Possible DDoS detected from {client_ip}")
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Too many requests"},
                )

            # 6. Process request
            response = await call_next(request)

            # 7. Add security headers
            response = self._add_security_headers(response)

            return response

        except Exception as e:
            logger.error(f"Security middleware error: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"},
            )

    def _get_client_ip(self, request: Request) -> str:
        """
        Extract client IP address from request, handling proxies.
        """
        # Check X-Forwarded-For header (common in reverse proxy setups)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For can contain multiple IPs, take the first one
            return forwarded_for.split(",")[0].strip()
        
        # Check X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        if request.client:
            return request.client.host
        
        return "unknown"

    def _check_ip_access(self, client_ip: str) -> bool:
        """
        Check if IP is allowed based on whitelist/blacklist.
        """
        # Block if in blacklist
        if client_ip in self.blocked_ips:
            return False
        
        # If whitelist exists, only allow IPs in whitelist
        if self.allowed_ips and client_ip not in self.allowed_ips:
            return False
        
        return True

    async def _validate_request(self, request: Request) -> bool:
        """
        Validate request for common security threats.
        """
        # Validate URL path
        if not self._is_safe_string(str(request.url.path)):
            return False
        
        # Validate query parameters
        for key, value in request.query_params.items():
            if not self._is_safe_string(key) or not self._is_safe_string(value):
                return False
        
        # Validate headers
        for key, value in request.headers.items():
            if not self._is_safe_string(value):
                return False
        
        # Validate body if present (only for JSON content)
        if request.headers.get("content-type") == "application/json":
            try:
                body = await request.body()
                if body and not self._is_safe_string(body.decode("utf-8")):
                    return False
            except Exception as e:
                logger.error(f"Error validating request body: {e}")
                return False
        
        return True

    def _is_safe_string(self, value: str) -> bool:
        """
        Check if string contains suspicious patterns.
        """
        for pattern in self.suspicious_patterns:
            if pattern.search(value):
                return False
        return True

    def _check_request_rate(self, client_ip: str, max_requests: int = 100, window_seconds: int = 60) -> bool:
        """
        Simple DDoS protection based on request rate.
        """
        current_time = datetime.utcnow()
        window_start = current_time - timedelta(seconds=window_seconds)
        
        # Initialize or clean old requests
        if client_ip not in self.request_stats:
            self.request_stats[client_ip] = []
        
        # Remove old requests outside the window
        self.request_stats[client_ip] = [
            req_time for req_time in self.request_stats[client_ip]
            if req_time > window_start
        ]
        
        # Add current request
        self.request_stats[client_ip].append(current_time)
        
        # Check if rate limit exceeded
        return len(self.request_stats[client_ip]) <= max_requests

    def _add_security_headers(self, response: Response) -> Response:
        """
        Add comprehensive security headers to response.
        """
        # HTTP Strict Transport Security (HSTS)
        if self.enable_hsts:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        
        # Content Security Policy (CSP)
        if self.enable_csp:
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self'; "
                "frame-ancestors 'none';"
            )
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # XSS Protection (legacy but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions Policy (formerly Feature Policy)
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=()"
        )
        
        # Remove server header
        response.headers.pop("server", None)
        
        # Add custom security header
        response.headers["X-Security-Level"] = "Enterprise"
        
        return response


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """
    Additional request validation middleware for JSON payloads.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Validate request content.
        """
        # Skip validation for non-JSON requests
        if request.headers.get("content-type") != "application/json":
            return await call_next(request)
        
        try:
            # Read and validate body
            body = await request.body()
            
            if body:
                # Attempt to parse JSON
                import json
                try:
                    json.loads(body.decode("utf-8"))
                except json.JSONDecodeError as e:
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content={"detail": f"Invalid JSON: {str(e)}"},
                    )
            
            # Continue processing
            return await call_next(request)
            
        except Exception as e:
            logger.error(f"Request validation error: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Invalid request"},
            )
