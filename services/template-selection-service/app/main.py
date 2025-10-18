"""
X-sevenAI Template Selection Service

Enterprise-grade microservice for business template selection and feature provisioning.
Handles 50+ business categories mapped to 4 core templates with 13 AI features.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
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
from app.routes.template_routes import router as template_router

# Configuration
SERVICE_NAME = "template-selection-service"
SERVICE_PORT = int(os.getenv("TEMPLATE_SELECTION_PORT", 8090))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Prometheus metrics
REQUEST_COUNT = Counter(
    'template_selection_requests_total',
    'Total requests',
    ['method', 'endpoint', 'status']
)
REQUEST_DURATION = Histogram(
    'template_selection_request_duration_seconds',
    'Request duration',
    ['method', 'endpoint']
)
TEMPLATE_SELECTIONS = Counter(
    'template_selections_total',
    'Total template selections',
    ['template_type', 'subscription_tier']
)
FEATURE_TOGGLES = Counter(
    'feature_toggles_total',
    'Total feature toggles',
    ['feature_type', 'action']
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management"""
    logger.info(f"🚀 Starting {SERVICE_NAME}")
    logger.info(f"📊 Service running on port {SERVICE_PORT}")
    
    # Initialize services
    from app.services.category_mapper import get_category_mapper
    from app.services.template_config import get_template_config_service
    from app.services.feature_engine import get_feature_engine
    from app.services.template_service import get_template_service
    
    try:
        # Initialize singletons
        mapper = get_category_mapper()
        config = get_template_config_service()
        engine = get_feature_engine()
        service = get_template_service()
        
        logger.info("✅ Category Mapper initialized")
        logger.info("✅ Template Configuration Service initialized")
        logger.info("✅ Feature Availability Engine initialized")
        logger.info("✅ Template Selection Service initialized")
        
        # Log statistics
        categories = mapper.get_all_categories()
        templates = config.get_all_templates()
        
        logger.info(f"📋 Loaded {len(categories)} business categories")
        logger.info(f"📦 Loaded {len(templates)} template configurations")
        
        for template_type, template_config in templates.items():
            logger.info(
                f"  - {template_config.name}: "
                f"{len(template_config.ai_features)} features, "
                f"{len(template_config.api_endpoints)} endpoints, "
                f"{len(template_config.dashboard_widgets)} widgets"
            )
        
        logger.info(f"✅ {SERVICE_NAME} started successfully")
        
    except Exception as e:
        logger.error(f"❌ Initialization failed: {e}", exc_info=True)
        raise
    
    yield
    
    logger.info(f"🛑 Shutting down {SERVICE_NAME}")


# Create FastAPI app
app = FastAPI(
    title="X-sevenAI Template Selection Service",
    description=(
        "Enterprise-grade template selection and feature provisioning service. "
        "Maps 50+ business categories to 4 core templates with 13 AI features. "
        "Provides real-time feature toggles, customization, and analytics."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware for metrics and logging
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Collect metrics and log requests"""
    method = request.method
    path = request.url.path
    
    # Skip metrics for health and metrics endpoints
    if path in ["/health", "/health/live", "/health/ready", "/metrics"]:
        return await call_next(request)
    
    logger.info(f"📨 {method} {path}")
    
    with REQUEST_DURATION.labels(method=method, endpoint=path).time():
        response = await call_next(request)
    
    REQUEST_COUNT.labels(
        method=method,
        endpoint=path,
        status=response.status_code
    ).inc()
    
    logger.info(f"✅ {method} {path} - {response.status_code}")
    
    return response


# Error handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"❌ Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url)
        },
    )


# Include routers
app.include_router(template_router)


# Health endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health/live", tags=["Health"])
async def liveness():
    """Kubernetes liveness probe"""
    return {"status": "alive"}


@app.get("/health/ready", tags=["Health"])
async def readiness():
    """Kubernetes readiness probe"""
    # Check if services are initialized
    try:
        from app.services.template_service import get_template_service
        service = get_template_service()
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "error": str(e)}
        )


@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with service information"""
    return {
        "service": SERVICE_NAME,
        "version": "1.0.0",
        "status": "running",
        "description": "Enterprise Template Selection & Feature Provisioning Service",
        "capabilities": {
            "business_categories": 50,
            "template_types": 4,
            "ai_features": 13,
            "universal_features": 6,
            "category_specific_features": 7
        },
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
            "health": "/health",
            "metrics": "/metrics"
        },
        "timestamp": datetime.utcnow().isoformat()
    }


# Service information endpoint
@app.get("/info", tags=["Root"])
async def service_info():
    """Detailed service information"""
    from app.services.category_mapper import get_category_mapper
    from app.services.template_config import get_template_config_service
    
    mapper = get_category_mapper()
    config = get_template_config_service()
    
    categories = mapper.get_all_categories()
    templates = config.get_all_templates()
    
    return {
        "service": SERVICE_NAME,
        "version": "1.0.0",
        "statistics": {
            "total_categories": len(categories),
            "total_templates": len(templates),
            "templates": [
                {
                    "type": t.template_type.value,
                    "name": t.name,
                    "features": len(t.ai_features),
                    "endpoints": len(t.api_endpoints),
                    "widgets": len(t.dashboard_widgets)
                }
                for t in templates.values()
            ]
        },
        "features": {
            "category_mapping": "50+ business categories",
            "template_selection": "ML-enhanced with confidence scoring",
            "feature_provisioning": "Tier-based with real-time toggles",
            "customization": "Custom widgets, endpoints, and workflows",
            "caching": "In-memory with <100ms response time",
            "analytics": "Usage tracking and adoption metrics"
        },
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=SERVICE_PORT,
        reload=True,
        log_level=LOG_LEVEL.lower()
    )
