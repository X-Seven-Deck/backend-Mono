"""
X-sevenAI AI Orchestration Service

The brain of the platform - orchestrates all AI operations including LangGraph workflows,
DSPy prompts, Crew AI agents, Haystack RAG, and multi-LLM management.
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
from app.core.redis_client import redis_client
from app.core.llm_provider import llm_manager
from app.services.langgraph_orchestrator import langgraph_orchestrator

# Import routes
from app.routes import orchestration, generation, rag, health, crew

# Configure logging
setup_logger("ai-orchestration", settings.log_level)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'ai_orchestration_requests_total',
    'Total requests',
    ['method', 'endpoint', 'status']
)
REQUEST_DURATION = Histogram(
    'ai_orchestration_request_duration_seconds',
    'Request duration',
    ['method', 'endpoint']
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management for the application"""
    # Startup
    logger.info("Starting AI Orchestration Service")
    logger.info(f"Environment: {settings.environment}")
    
    # Initialize Redis
    try:
        await redis_client.connect()
        logger.info("Redis connected successfully")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
    
    # Verify LLM providers
    if llm_manager.openai_client:
        logger.info("OpenAI client ready")
    if llm_manager.groq_client:
        logger.info("Groq client ready")
    if llm_manager.anthropic_client:
        logger.info("Anthropic client ready")
    
    logger.info("AI Orchestration Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Orchestration Service")
    await redis_client.disconnect()
    logger.info("AI Orchestration Service stopped")


# Create FastAPI app
app = FastAPI(
    title="X-sevenAI AI Orchestration Service",
    description="AI brain for X-sevenAI platform with LangGraph, DSPy, Crew AI, and Haystack RAG",
    version="0.1.0",
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
app.include_router(orchestration.router, prefix="/api/v1/orchestration", tags=["orchestration"])
app.include_router(generation.router, prefix="/api/v1/generation", tags=["generation"])
app.include_router(rag.router, prefix="/api/v1/rag", tags=["rag"])
app.include_router(crew.router, prefix="/api/v1/crew", tags=["crew-ai"])


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "AI Orchestration Service",
        "version": "0.1.0",
        "status": "running",
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
