"""
Xseven POS Microservice
Enterprise-grade Point of Sale system for SMBs
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram
import uvicorn
from datetime import datetime

from .core.config import settings
from .routes import (
    orders_router,
    payments_router,
    receipts_router,
    tax_router
)
from .routes.websocket import router as websocket_router
from .routes.offline import router as offline_router
from .routes.analytics import router as analytics_router
from .routes.customers import router as customers_router

# Service metadata
SERVICE_NAME = "pos-service"
SERVICE_VERSION = "1.0.0"

# Prometheus metrics
REQUEST_COUNT = Counter(
    'pos_requests_total',
    'Total POS requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'pos_request_duration_seconds',
    'POS request duration',
    ['method', 'endpoint']
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management"""
    print(f"🚀 Starting {SERVICE_NAME} v{SERVICE_VERSION}")
    print(f"📍 Service running on port {settings.POS_SERVICE_PORT}")
    print(f"🌍 Environment: {settings.ENVIRONMENT}")
    
    # Initialize database service
    from .services.database import get_database_service
    try:
        db = get_database_service()
        print("✅ Database service initialized")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
    
    # Initialize tax engine
    from .services.tax_engine import get_tax_engine
    try:
        tax_engine = get_tax_engine()
        print("✅ Tax engine initialized")
    except Exception as e:
        print(f"❌ Tax engine initialization failed: {e}")
    
    # Initialize receipt generator
    from .services.receipt_generator import get_receipt_generator
    try:
        receipt_gen = get_receipt_generator()
        print("✅ Receipt generator initialized")
    except Exception as e:
        print(f"❌ Receipt generator initialization failed: {e}")
    
    print(f"✅ {SERVICE_NAME} started successfully")
    
    yield
    
    print(f"🛑 Shutting down {SERVICE_NAME}")


# Create FastAPI app
app = FastAPI(
    title="Xseven POS Microservice",
    description="Enterprise-grade Point of Sale system for SMBs",
    version=SERVICE_VERSION,
    lifespan=lifespan,
    docs_url="/docs",  # Explicitly enable Swagger UI at /docs
    redoc_url="/redoc",  # Enable ReDoc at /redoc
    openapi_url="/openapi.json"  # Enable OpenAPI schema at /openapi.json
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware for request tracking
@app.middleware("http")
async def track_requests(request: Request, call_next):
    """Track request metrics"""
    start_time = datetime.utcnow()
    
    response = await call_next(request)
    
    duration = (datetime.utcnow() - start_time).total_seconds()
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response


# Include routers
app.include_router(orders_router)
app.include_router(payments_router)
app.include_router(receipts_router)
app.include_router(tax_router)
app.include_router(websocket_router)  # WebSocket for real-time updates
app.include_router(offline_router)    # Offline order queueing
app.include_router(analytics_router)  # Business analytics
app.include_router(customers_router)  # Customer management


# Health endpoints
@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "description": "Xseven POS Microservice - Enterprise Point of Sale",
        "status": "operational",
        "features": [
            "Order Management",
            "Payment Processing",
            "Receipt Generation",
            "Tax Calculation",
            "Real-time Updates (WebSocket)",
            "Offline Order Queueing",
            "Business Analytics",
            "Customer Management"
        ],
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "metrics": "/metrics",
            "orders": "/api/v1/pos/orders",
            "payments": "/api/v1/pos/payments",
            "receipts": "/api/v1/pos/receipts",
            "tax": "/api/v1/pos/tax",
            "websocket_orders": "/api/v1/pos/ws/orders",
            "websocket_tables": "/api/v1/pos/ws/tables",
            "offline": "/api/v1/pos/offline",
            "analytics": "/api/v1/pos/analytics",
            "customers": "/api/v1/pos/customers"
        }
    }


# Error handlers
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    print(f"❌ Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.POS_SERVICE_HOST,
        port=settings.POS_SERVICE_PORT,
        reload=settings.ENVIRONMENT == "development",
        log_level=settings.LOG_LEVEL.lower()
    )
