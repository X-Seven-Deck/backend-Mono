"""
X-sevenAI Business Logic Service

Handles core business operations: orders, reservations, inventory management.
Uses Temporal for durable workflows and Kafka for event streaming.
Implements enterprise multi-tenancy with isolation and resource quotas.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram
import uvicorn
from datetime import datetime
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import routes
from app.routes.tenant_routes import router as tenant_router
from app.routes.template_routes import router as template_router
from app.routes.ai_features_routes import router as ai_features_router
from app.routes.order_routes import router as order_router
from app.routes.reservation_routes import router as reservation_router
from app.routes.inventory_routes import router as inventory_router
from app.routes.payment_routes import router as payment_router

# Import middleware
from app.middleware.tenant_middleware import TenantContextMiddleware, ResourceQuotaMiddleware
from app.middleware.logging_middleware import RequestLoggingMiddleware
from app.middleware.rate_limit_middleware import rate_limit_middleware

# Import DevOps client
import sys
import os
# Add shared directory to path
file_dir = os.path.dirname(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(file_dir)))
shared_path = os.path.join(project_root, 'shared')
sys.path.append(shared_path)
from libs.devops_client import get_devops_client, IncidentSeverity

# Configuration
from app.config.settings import get_settings

SERVICE_NAME = "business-logic-service"
settings = get_settings()
SERVICE_PORT = settings.PORT
LOG_LEVEL = settings.LOG_LEVEL

# Prometheus metrics
REQUEST_COUNT = Counter(
    'business_logic_requests_total',
    'Total requests',
    ['method', 'endpoint', 'status']
)
REQUEST_DURATION = Histogram(
    'business_logic_request_duration_seconds',
    'Request duration',
    ['method', 'endpoint']
)
TENANT_REQUESTS = Counter(
    'tenant_requests_total',
    'Total tenant requests',
    ['tenant_id', 'tier']
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management"""
    logger.info(f"🚀 Starting {SERVICE_NAME}")
    
    # Initialize DevOps client
    devops_client = get_devops_client()
    devops_client.configure(SERVICE_NAME)
    logger.info("✅ DevOps client initialized")
    
    # Initialize services
    from app.services.tenant_service import get_tenant_service
    from app.services.kafka_service import get_kafka_service
    from app.services.temporal_service import get_temporal_service
    
    try:
        tenant_service = get_tenant_service()
        logger.info("✅ Tenant Service initialized")
        
        # Initialize Kafka if enabled
        if settings.ENABLE_KAFKA_EVENTS:
            kafka_service = get_kafka_service()
            await kafka_service.start()
            logger.info("✅ Kafka service started")
        
        # Initialize Temporal if enabled
        if settings.ENABLE_TEMPORAL_WORKFLOWS:
            temporal_service = get_temporal_service()
            await temporal_service.start()
            logger.info("✅ Temporal service started")
        
        logger.info(f"✅ {SERVICE_NAME} started successfully")
        
    except Exception as e:
        logger.error(f"❌ Initialization failed: {e}", exc_info=True)
        # Report critical incident
        await devops_client.report_incident(
            title=f"{SERVICE_NAME} initialization failed",
            description=str(e),
            severity=IncidentSeverity.CRITICAL
        )
        raise
    
    yield
    
    logger.info(f"🛑 Shutting down {SERVICE_NAME}")
    
    # Cleanup
    if settings.ENABLE_KAFKA_EVENTS:
        try:
            kafka_service = get_kafka_service()
            await kafka_service.stop()
        except:
            pass
    
    if settings.ENABLE_TEMPORAL_WORKFLOWS:
        try:
            temporal_service = get_temporal_service()
            await temporal_service.stop()
        except:
            pass


# Create FastAPI app
app = FastAPI(
    title="X-sevenAI Business Logic Service",
    description="Core business operations with enterprise multi-tenancy, Temporal workflows and Kafka events",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add tenant middleware
app.add_middleware(TenantContextMiddleware)
app.add_middleware(ResourceQuotaMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.middleware("http")(rate_limit_middleware)


# Include routers
app.include_router(tenant_router)
app.include_router(template_router)
app.include_router(ai_features_router)
app.include_router(order_router)
app.include_router(reservation_router)
app.include_router(inventory_router)
app.include_router(payment_router)


# Middleware for metrics
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Collect metrics"""
    method = request.method
    path = request.url.path
    
    # Skip metrics for health endpoints
    if path in ["/health", "/health/live", "/health/ready", "/metrics"]:
        return await call_next(request)
    
    with REQUEST_DURATION.labels(method=method, endpoint=path).time():
        response = await call_next(request)
    
    REQUEST_COUNT.labels(
        method=method,
        endpoint=path,
        status=response.status_code
    ).inc()
    
    # Track tenant-specific metrics
    if hasattr(request.state, "tenant_context"):
        tenant_context = request.state.tenant_context
        TENANT_REQUESTS.labels(
            tenant_id=tenant_context.tenant_id,
            tier=tenant_context.tier.value
        ).inc()
    
    return response


# Error handling
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    # Report to DevOps service
    devops_client = get_devops_client()
    await devops_client.report_incident(
        title=f"Unhandled exception in {SERVICE_NAME}",
        description=f"Path: {request.url.path}\nError: {str(exc)}",
        severity=IncidentSeverity.HIGH,
        metadata={
            "path": str(request.url.path),
            "method": request.method,
            "error_type": type(exc).__name__
        }
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        },
    )


# Health endpoints
@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health/live")
async def liveness():
    """Liveness probe"""
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness():
    """Readiness probe"""
    return {"status": "ready"}


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": SERVICE_NAME,
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "features": {
            "kafka_events": settings.ENABLE_KAFKA_EVENTS,
            "temporal_workflows": settings.ENABLE_TEMPORAL_WORKFLOWS,
            "ai_features": settings.ENABLE_AI_FEATURES
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=SERVICE_PORT,
        reload=True,
        log_level=LOG_LEVEL.lower()
    )
