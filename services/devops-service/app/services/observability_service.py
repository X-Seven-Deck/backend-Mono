"""Advanced Observability & Monitoring"""
import logging
from typing import Dict, List, Optional
from datetime import datetime
import httpx
from app.config import settings
from app.models.schemas import SLODefinition, SLOStatus, SLIType

logger = logging.getLogger(__name__)

class ObservabilityService:
    """Enterprise observability stack"""
    
    def __init__(self):
        self.prometheus_url = settings.PROMETHEUS_URL
        self.slos: Dict[str, SLODefinition] = {}
    
    async def query_metrics(self, query: str) -> Dict:
        """Query Prometheus metrics"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.prometheus_url}/api/v1/query",
                    params={"query": query},
                    timeout=10.0
                )
                return response.json()
        except Exception as e:
            logger.error(f"Metrics query error: {e}")
            return {}
    
    async def define_slo(self, slo: SLODefinition):
        """Define Service Level Objective"""
        key = f"{slo.service_name}:{slo.sli_type.value}"
        self.slos[key] = slo
        logger.info(f"Defined SLO for {slo.service_name}: {slo.target}%")
    
    async def check_slo_compliance(self, service_name: str, sli_type: SLIType) -> SLOStatus:
        """Check SLO compliance"""
        key = f"{service_name}:{sli_type.value}"
        slo = self.slos.get(key)
        
        if not slo:
            return SLOStatus(
                service_name=service_name,
                sli_type=sli_type,
                target=99.9,
                current_value=100.0,
                error_budget_remaining=100.0,
                is_compliant=True,
                window_start=datetime.utcnow(),
                window_end=datetime.utcnow()
            )
        
        # Simulate current value
        current_value = 99.95
        error_budget = 100 - slo.target
        error_budget_remaining = ((current_value - slo.target) / error_budget) * 100
        
        return SLOStatus(
            service_name=service_name,
            sli_type=sli_type,
            target=slo.target,
            current_value=current_value,
            error_budget_remaining=max(0, error_budget_remaining),
            is_compliant=current_value >= slo.target,
            window_start=datetime.utcnow(),
            window_end=datetime.utcnow()
        )

def get_observability_service() -> ObservabilityService:
    return ObservabilityService()
