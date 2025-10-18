"""
X-sevenAI Notification Integration Service

Enterprise-grade notification service supporting multiple channels:
- SMS (Twilio)
- Email (SendGrid)
- Push Notifications
- Webhook integrations (Zapier)
- Event-driven notifications via Kafka
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import uvicorn
from datetime import datetime

from app.config import settings
from app.utils import logger, setup_logger
from app.services.twilio_service import twilio_service
from app.services.sendgrid_service import sendgrid_service
from app.services.zapier_service import zapier_service
from app.services.kafka_consumer import kafka_consumer

# Import routes
from app.routes import notifications, webhooks, health

# Configure logging
setup_logger("notification-service", settings.log_level)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'notification_requests_total',
    'Total notification requests',
    ['method', 'endpoint', 'status']
)
REQUEST_DURATION = Histogram(
    'notification_request_duration_seconds',
    'Request duration',
    ['method', 'endpoint']
)
NOTIFICATION_COUNT = Counter(
    'notifications_sent_total',
    'Total notifications sent',
    ['channel', 'status']
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management for the application"""
    # Startup
    logger.info("Starting Notification Integration Service")
    logger.info(f"Environment: {settings.environment}")
    
    # Initialize services
    try:
        await twilio_service.initialize()
        logger.info("Twilio service initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Twilio: {e}")
    
    try:
        await sendgrid_service.initialize()
        logger.info("SendGrid service initialized")
    except Exception as e:
        logger.error(f"Failed to initialize SendGrid: {e}")
    
    try:
        await zapier_service.initialize()
        logger.info("Zapier service initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Zapier: {e}")
    
    # Start Kafka consumer for event-driven notifications
    try:
        await kafka_consumer.start()
        logger.info("Kafka consumer started")
    except Exception as e:
        logger.error(f"Failed to start Kafka consumer: {e}")
    
    logger.info("Notification Integration Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Notification Integration Service")
    await kafka_consumer.stop()
    logger.info("Notification Integration Service stopped")


# Create FastAPI app
app = FastAPI(
    title="X-sevenAI Notification Integration Service",
    description="Multi-channel notification service with Twilio, SendGrid, and Zapier",
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
    """Collect metrics for each request"""
    method = request.method
    path = request.url.path
    
    with REQUEST_DURATION.labels(method=method, endpoint=path).time():
        response = await call_next(request)
    
    REQUEST_COUNT.labels(
        method=method,
        endpoint=path,
        status=response.status_code
    ).inc()
    
    return response


# Error handling
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    logger.error(f"HTTP error: {exc.status_code} - {exc.detail}")
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
    """Handle general exceptions"""
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        },
    )


# Prometheus metrics endpoint
@app.get("/metrics")
async def metrics():
    """Expose Prometheus metrics"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["notifications"])
app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["webhooks"])


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Notification Integration Service",
        "version": "1.0.0",
        "status": "running",
        "channels": ["sms", "email", "webhook", "push"],
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.service_host,
        port=settings.service_port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower()
    )
