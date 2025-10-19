"""
Comprehensive Audit Logging Middleware for Auth Service

Tracks all security-relevant events:
- Authentication attempts (success/failure)
- Authorization decisions
- Data access
- Configuration changes
- Security events
- Compliance-relevant activities
"""

import logging
import json
import hashlib
from typing import Callable, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import sys
import os

# Add shared directory to path
file_dir = os.path.dirname(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(file_dir))))
shared_path = os.path.join(project_root, 'shared')
sys.path.append(shared_path)
from libs.supabase_client import SupabaseManager

logger = logging.getLogger(__name__)


class AuditEvent:
    """
    Structured audit event model.
    """

    def __init__(
        self,
        event_type: str,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        user_id: Optional[str] = None,
        business_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_method: Optional[str] = None,
        request_path: Optional[str] = None,
        status_code: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        result: str = "success",
    ):
        self.event_type = event_type
        self.action = action
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.user_id = user_id
        self.business_id = business_id
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.request_method = request_method
        self.request_path = request_path
        self.status_code = status_code
        self.metadata = metadata or {}
        self.result = result
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert audit event to dictionary."""
        return {
            "event_type": self.event_type,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "user_id": self.user_id,
            "business_id": self.business_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "request_method": self.request_method,
            "request_path": self.request_path,
            "status_code": self.status_code,
            "metadata": self.metadata,
            "result": self.result,
            "timestamp": self.timestamp.isoformat(),
        }


class AuditLogger:
    """
    Enterprise audit logger with database persistence.
    """

    def __init__(self):
        try:
            self.supabase = SupabaseManager(use_service_key=True)
        except Exception as e:
            logger.warning(f"Failed to initialize Supabase for audit logging: {e}")
            self.supabase = None

    async def log_event(self, event: AuditEvent):
        """
        Log audit event to database and file system.
        """
        try:
            # Log to file (always)
            logger.info(
                f"AUDIT: {event.action} | User: {event.user_id} | "
                f"IP: {event.ip_address} | Result: {event.result} | "
                f"Resource: {event.resource_type}/{event.resource_id}"
            )

            # Log to database
            if self.supabase:
                await self._log_to_database(event)
            
        except Exception as e:
            logger.error(f"Failed to log audit event: {str(e)}", exc_info=True)

    async def _log_to_database(self, event: AuditEvent):
        """Log event to audit_logs table."""
        try:
            audit_data = {
                "action": event.action,
                "resource_type": event.resource_type,
                "resource_id": event.resource_id,
                "user_id": event.user_id,
                "business_id": event.business_id,
                "ip_address": event.ip_address,
                "user_agent": event.user_agent,
                "metadata": {
                    "event_type": event.event_type,
                    "request_method": event.request_method,
                    "request_path": event.request_path,
                    "status_code": event.status_code,
                    "result": event.result,
                    **event.metadata,
                },
            }

            await self.supabase.insert("audit_logs", audit_data)
            
        except Exception as e:
            logger.error(f"Database audit logging failed: {str(e)}")

    async def log_authentication(
        self,
        action: str,
        email: str,
        ip_address: str,
        user_agent: str,
        result: str = "success",
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Log authentication event."""
        event = AuditEvent(
            event_type="authentication",
            action=action,
            resource_type="user",
            resource_id=user_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            result=result,
            metadata={
                "email": email,
                **(metadata or {}),
            },
        )
        await self.log_event(event)

    async def log_authorization(
        self,
        action: str,
        resource_type: str,
        resource_id: str,
        user_id: str,
        ip_address: str,
        result: str = "allowed",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Log authorization decision."""
        event = AuditEvent(
            event_type="authorization",
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            ip_address=ip_address,
            result=result,
            metadata=metadata,
        )
        await self.log_event(event)

    async def log_data_access(
        self,
        action: str,
        resource_type: str,
        resource_id: str,
        user_id: str,
        ip_address: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Log data access event."""
        event = AuditEvent(
            event_type="data_access",
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            ip_address=ip_address,
            metadata=metadata,
        )
        await self.log_event(event)

    async def log_security_event(
        self,
        action: str,
        ip_address: str,
        user_agent: str,
        result: str = "blocked",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Log security event."""
        event = AuditEvent(
            event_type="security",
            action=action,
            ip_address=ip_address,
            user_agent=user_agent,
            result=result,
            metadata=metadata,
        )
        await self.log_event(event)


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically audit all requests.
    """

    def __init__(
        self,
        app: ASGIApp,
        exempt_paths: Optional[list] = None,
    ):
        super().__init__(app)
        self.audit_logger = AuditLogger()
        self.exempt_paths = set(exempt_paths or ["/health", "/metrics"])

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Audit request and response.
        """
        # Skip exempt paths
        if request.url.path in self.exempt_paths:
            return await call_next(request)

        # Extract request context
        ip_address = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "unknown")
        user_id = await self._extract_user_id(request)

        # Record request start time
        start_time = datetime.utcnow()

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration = (datetime.utcnow() - start_time).total_seconds()

            # Log successful request
            await self._log_request(
                request=request,
                response=response,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                duration=duration,
            )

            return response

        except Exception as e:
            # Log failed request
            await self._log_error(
                request=request,
                error=e,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            raise

    async def _log_request(
        self,
        request: Request,
        response: Response,
        user_id: Optional[str],
        ip_address: str,
        user_agent: str,
        duration: float,
    ):
        """Log successful request."""
        # Determine if request should be audited based on path and method
        should_audit = self._should_audit_request(request)

        if should_audit:
            event = AuditEvent(
                event_type="api_request",
                action=f"{request.method} {request.url.path}",
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                request_method=request.method,
                request_path=str(request.url.path),
                status_code=response.status_code,
                result="success" if response.status_code < 400 else "error",
                metadata={
                    "duration_seconds": duration,
                    "query_params": dict(request.query_params),
                },
            )
            await self.audit_logger.log_event(event)

    async def _log_error(
        self,
        request: Request,
        error: Exception,
        user_id: Optional[str],
        ip_address: str,
        user_agent: str,
    ):
        """Log request error."""
        event = AuditEvent(
            event_type="api_error",
            action=f"{request.method} {request.url.path}",
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            request_method=request.method,
            request_path=str(request.url.path),
            result="error",
            metadata={
                "error_type": type(error).__name__,
                "error_message": str(error),
            },
        )
        await self.audit_logger.log_event(event)

    def _should_audit_request(self, request: Request) -> bool:
        """
        Determine if request should be audited based on path and method.
        """
        # Always audit authentication/authorization endpoints
        auth_paths = ["/auth/", "/users/", "/business/"]
        for path in auth_paths:
            if path in request.url.path:
                return True

        # Audit all write operations
        if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            return True

        # Audit sensitive read operations
        sensitive_paths = ["/api-keys/", "/sessions/", "/audit/"]
        for path in sensitive_paths:
            if path in request.url.path:
                return True

        return False

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        if request.client:
            return request.client.host

        return "unknown"

    async def _extract_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request if authenticated."""
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        # In production, decode JWT and extract user ID
        # For now, return None (will be populated by auth middleware)
        return None


# Global audit logger instance
audit_logger = AuditLogger()
