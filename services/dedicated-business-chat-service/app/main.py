"""
X-sevenAI Dedicated Business Chat Service

Enterprise-grade business-specific chat with AI context awareness, RAG, and multi-category support.
Provides dedicated chat sessions starting from business_id with full business context.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest
from datetime import datetime
import logging
import sys

from app.config import settings
from app.routes import chat
from app.services.database import db_service
from app.services.ai_service import ai_service
from app.services.cache_service import cache_service

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'dedicated_chat_requests_total',
    'Total requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'dedicated_chat_request_latency_seconds',
    'Request latency',
    ['method', 'endpoint']
)

MESSAGE_COUNT = Counter(
    'dedicated_chat_messages_total',
    'Total messages processed',
    ['business_id', 'message_type']
)

SESSION_COUNT = Counter(
    'dedicated_chat_sessions_total',
    'Total chat sessions created',
    ['business_id']
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management"""
    logger.info(f"Starting {settings.service_name}")
    
    # Initialize services
    try:
        await db_service.initialize()
        logger.info("✓ Database service initialized")
    except Exception as e:
        logger.error(f"✗ Failed to initialize database service: {e}")
    
    try:
        await ai_service.initialize()
        logger.info("✓ AI service initialized")
    except Exception as e:
        logger.error(f"✗ Failed to initialize AI service: {e}")
    
    try:
        await cache_service.initialize()
        logger.info("✓ Cache service initialized")
    except Exception as e:
        logger.warning(f"⚠ Cache service not available: {e}")
    
    logger.info(f"🚀 {settings.service_name} is ready")
    
    yield
    
    # Cleanup
    logger.info(f"Shutting down {settings.service_name}")
    await cache_service.close()


# Create FastAPI app
app = FastAPI(
    title="X-sevenAI Dedicated Business Chat Service",
    description="""
    Enterprise-grade business-specific chat with AI context awareness.
    
    Features:
    - Business-context aware AI responses
    - RAG-powered knowledge base integration
    - Multi-category support (restaurants, salons, retail, etc.)
    - Real-time conversation management
    - Intent classification and entity extraction
    - Sentiment analysis
    - Human agent handover
    - Session caching with Redis
    - Comprehensive analytics
    
    This service provides dedicated chat sessions that start from a business_id,
    ensuring all conversations are fully aware of the business context, category,
    and available features.
    """,
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)


# Middleware for metrics
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Record metrics for all requests"""
    method = request.method
    path = request.url.path
    
    # Record request
    with REQUEST_LATENCY.labels(method=method, endpoint=path).time():
        response = await call_next(request)
    
    # Record status
    REQUEST_COUNT.labels(
        method=method,
        endpoint=path,
        status=response.status_code
    ).inc()
    
    return response


# Include routers
app.include_router(chat.router)


# Health endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.service_name,
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": db_service._initialized,
            "ai": ai_service._initialized,
            "cache": cache_service._initialized
        }
    }


@app.get("/health/live")
async def liveness():
    """Liveness probe for Kubernetes"""
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness():
    """Readiness probe for Kubernetes"""
    ready = db_service._initialized and ai_service._initialized
    
    if not ready:
        return JSONResponse(
            status_code=503,
            content={"status": "not ready"}
        )
    
    return {"status": "ready"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.service_name,
        "version": "1.0.0",
        "description": "Dedicated Business Chat Service with AI context awareness",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "chat": "/api/v1/chat"
        }
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    if not settings.enable_metrics:
        return JSONResponse(
            status_code=404,
            content={"error": "Metrics disabled"}
        )
    
    return generate_latest()


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.environment == "development" else "An error occurred",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.service_port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower()
    )
