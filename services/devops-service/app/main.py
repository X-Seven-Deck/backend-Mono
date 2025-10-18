"""DevOps Service - Phase 3 Implementation"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.config import settings
from app.models.schemas import *
from app.services.gitops_service import get_gitops_manager
from app.services.incident_management_service import get_incident_manager
from app.services.observability_service import get_observability_service
from app.services.performance_service import get_cache_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="X7AI DevOps Service",
    description="Phase 3: DevOps Excellence & Business Continuity",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GitOps Endpoints
@app.post("/api/v1/deployments/canary", response_model=DeploymentResponse)
async def deploy_canary(request: CanaryDeploymentRequest):
    """Deploy with canary strategy"""
    try:
        manager = get_gitops_manager()
        return await manager.deploy_with_canary(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/deployments/{service_name}/status")
async def get_deployment_status(service_name: str):
    """Get deployment status"""
    manager = get_gitops_manager()
    return await manager.get_deployment_status(service_name)

# Incident Management Endpoints
@app.post("/api/v1/incidents", response_model=Incident)
async def create_incident(incident: IncidentCreate):
    """Create new incident"""
    manager = get_incident_manager()
    return await manager.handle_incident(incident)

@app.put("/api/v1/incidents/{incident_id}/resolve")
async def resolve_incident(incident_id: str):
    """Resolve incident"""
    manager = get_incident_manager()
    result = await manager.resolve_incident(incident_id)
    if not result:
        raise HTTPException(status_code=404, detail="Incident not found")
    return result

# SLO Management Endpoints
@app.post("/api/v1/slo/define")
async def define_slo(slo: SLODefinition):
    """Define Service Level Objective"""
    service = get_observability_service()
    await service.define_slo(slo)
    return {"message": "SLO defined successfully"}

@app.get("/api/v1/slo/{service_name}/status", response_model=SLOStatus)
async def check_slo(service_name: str, sli_type: SLIType):
    """Check SLO compliance"""
    service = get_observability_service()
    return await service.check_slo_compliance(service_name, sli_type)

# Metrics Endpoints
@app.get("/api/v1/metrics/query")
async def query_metrics(query: str):
    """Query Prometheus metrics"""
    service = get_observability_service()
    return await service.query_metrics(query)

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.SERVICE_PORT)
