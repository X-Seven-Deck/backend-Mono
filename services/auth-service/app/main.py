"""
X-sevenAI Auth Service

Enterprise-grade authentication and authorization microservice with:
- Multi-Factor Authentication (MFA)
- Advanced rate limiting
- Comprehensive audit logging
- RBAC and permissions
- API key management
- Session management
- Security middleware
"""

import logging
import os
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from dotenv import load_dotenv

# Load environment variables from the project root .env file
project_root = os.path.join(os.path.dirname(__file__), "../../")
env_file = os.path.join(project_root, ".env")

if os.path.exists(env_file):
    load_dotenv(env_file)
else:
    # Fallback to current directory
    load_dotenv()

# Import routes
from app.routes.auth import router as auth
from app.routes.users import router as users
from app.routes.business import router as business

# Import middleware
from app.middleware.security import SecurityMiddleware
from app.middleware.rate_limiter import RateLimitMiddleware, global_rate_limiter
from app.middleware.audit import AuditMiddleware

# Configure logging
logging.basicConfig(
    level=logging.getLevelName(os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("auth-service")

# Create FastAPI app
app = FastAPI(
    title="X7AI Auth Service",
    description="Enterprise authentication and authorization service for X7AI platform",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS with security best practices
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
)

# Add security middleware
app.add_middleware(
    SecurityMiddleware,
    allowed_ips=os.getenv("ALLOWED_IPS", "").split(",") if os.getenv("ALLOWED_IPS") else None,
    blocked_ips=os.getenv("BLOCKED_IPS", "").split(",") if os.getenv("BLOCKED_IPS") else None,
    enable_csp=os.getenv("ENABLE_CSP", "true").lower() == "true",
    enable_hsts=os.getenv("ENABLE_HSTS", "true").lower() == "true",
)

# Add rate limiting middleware
app.add_middleware(
    RateLimitMiddleware,
    rate_limiter=global_rate_limiter,
    exempt_paths=["/health", "/docs", "/redoc", "/openapi.json"],
)

# Add audit logging middleware
app.add_middleware(
    AuditMiddleware,
    exempt_paths=["/health", "/docs", "/redoc", "/openapi.json"],
)

# Error handling
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": "auth-service",
        "version": "2.0.0",
    }


# Metrics endpoint (for Prometheus)
@app.get("/metrics")
async def metrics():
    """Metrics endpoint for monitoring."""
    # In production, integrate with Prometheus client
    return {
        "service": "auth-service",
        "version": "2.0.0",
        "status": "ok",
    }


# Include routers
app.include_router(auth, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users, prefix="/api/v1/users", tags=["Users"])
app.include_router(business, prefix="/api/v1/business", tags=["Business"])

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("="*60)
    logger.info("X7AI Auth Service v2.0.0 - Enterprise Edition")
    logger.info("="*60)
    logger.info("Features enabled:")
    logger.info("  ✓ Multi-Factor Authentication (MFA)")
    logger.info("  ✓ Advanced Rate Limiting")
    logger.info("  ✓ Comprehensive Audit Logging")
    logger.info("  ✓ Security Middleware (HSTS, CSP, etc.)")
    logger.info("  ✓ Role-Based Access Control (RBAC)")
    logger.info("  ✓ API Key Management")
    logger.info("  ✓ Session Management")
    logger.info("="*60)
    logger.info("Service starting up...")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Auth Service shutting down")


if __name__ == "__main__":
    host = os.getenv("AUTH_SERVICE_HOST", "0.0.0.0")
    port = int(os.getenv("AUTH_SERVICE_PORT", 8010))
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=os.getenv("DEBUG", "false").lower() == "true",
    )
