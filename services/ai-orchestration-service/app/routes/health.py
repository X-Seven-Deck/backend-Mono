"""
Health check endpoints for AI Orchestration Service
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
from app.models.schemas import HealthResponse
from app.core.redis_client import redis_client
from app.core.llm_provider import llm_manager
from app.utils import logger

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Comprehensive health check endpoint
    
    Checks status of all dependencies: Redis, LLM providers, etc.
    """
    dependencies = {}
    
    # Check Redis
    try:
        if redis_client._connected:
            await redis_client.client.ping()
            dependencies["redis"] = "connected"
        else:
            dependencies["redis"] = "disconnected"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        dependencies["redis"] = "error"
    
    # Check LLM providers
    dependencies["openai"] = "available" if llm_manager.openai_client else "unavailable"
    dependencies["groq"] = "available" if llm_manager.groq_client else "unavailable"
    dependencies["anthropic"] = "available" if llm_manager.anthropic_client else "unavailable"
    
    # Determine overall status
    critical_deps = ["redis"]
    status = "healthy"
    
    for dep in critical_deps:
        if dependencies.get(dep) not in ["connected", "available"]:
            status = "degraded"
            break
    
    # Check if at least one LLM provider is available
    llm_available = any([
        dependencies.get("openai") == "available",
        dependencies.get("groq") == "available",
        dependencies.get("anthropic") == "available"
    ])
    
    if not llm_available:
        status = "unhealthy"
    
    return HealthResponse(
        status=status,
        timestamp=datetime.utcnow().isoformat(),
        version="0.1.0",
        dependencies=dependencies
    )


@router.get("/health/live")
async def liveness():
    """
    Kubernetes liveness probe
    
    Returns 200 if service is alive
    """
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness():
    """
    Kubernetes readiness probe
    
    Returns 200 if service is ready to accept traffic
    """
    # Check critical dependencies
    try:
        if redis_client._connected:
            await redis_client.client.ping()
        else:
            raise HTTPException(status_code=503, detail="Redis not connected")
        
        # Check at least one LLM provider
        if not (llm_manager.openai_client or llm_manager.groq_client or llm_manager.anthropic_client):
            raise HTTPException(status_code=503, detail="No LLM providers available")
        
        return {"status": "ready"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail="Service not ready")
