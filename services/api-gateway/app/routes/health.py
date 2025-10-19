"""
Health check routes for API Gateway
"""

from fastapi import APIRouter, Request
from datetime import datetime
from typing import Dict, Any

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "service": "api-gateway",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health/live")
async def liveness():
    """Kubernetes liveness probe"""
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness(request: Request):
    """
    Kubernetes readiness probe
    Checks if gateway is ready to serve traffic
    """
    # Check if service registry is initialized
    if not hasattr(request.app.state, 'service_registry'):
        return {"status": "not ready", "reason": "service registry not initialized"}
    
    # Check if health checker is running
    if hasattr(request.app.state, 'health_checker'):
        health_checker = request.app.state.health_checker
        overall_health = await health_checker.get_overall_health()
        
        # Ready if at least 50% of services are healthy
        if overall_health["healthy_services"] >= overall_health["total_services"] * 0.5:
            return {
                "status": "ready",
                "healthy_services": overall_health["healthy_services"],
                "total_services": overall_health["total_services"]
            }
        else:
            return {
                "status": "not ready",
                "reason": "insufficient healthy services",
                "healthy_services": overall_health["healthy_services"],
                "total_services": overall_health["total_services"]
            }
    
    return {"status": "ready"}


@router.get("/health/services")
async def services_health(request: Request) -> Dict[str, Any]:
    """
    Detailed health status of all backend services
    """
    if not hasattr(request.app.state, 'health_checker'):
        return {"error": "Health checker not initialized"}
    
    health_checker = request.app.state.health_checker
    overall_health = await health_checker.get_overall_health()
    
    # Get circuit breaker states
    circuit_states = {}
    if hasattr(request.app.state, 'circuit_breaker_manager'):
        circuit_breaker_manager = request.app.state.circuit_breaker_manager
        circuit_states = circuit_breaker_manager.get_all_states()
    
    return {
        "overall_health": overall_health,
        "circuit_breakers": circuit_states,
        "timestamp": datetime.utcnow().isoformat()
    }
