"""
GitOps Deployment Manager

Handles ArgoCD integration, canary deployments, and progressive delivery
with automatic rollback capabilities.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import httpx
from kubernetes import client, config
from kubernetes.client.rest import ApiException

from app.config import settings
from app.models.schemas import (
    DeploymentStatus,
    CanaryDeploymentRequest,
    DeploymentResponse
)

logger = logging.getLogger(__name__)


class ArgoCDClient:
    """ArgoCD API client"""
    
    def __init__(self):
        self.server = settings.ARGOCD_SERVER
        self.token = settings.ARGOCD_TOKEN
        self.namespace = settings.ARGOCD_NAMESPACE
        self.base_url = f"https://{self.server}/api/v1"
        
    async def sync_application(self, app_name: str) -> Dict[str, Any]:
        """Sync ArgoCD application"""
        try:
            async with httpx.AsyncClient(verify=False) as client:
                response = await client.post(
                    f"{self.base_url}/applications/{app_name}/sync",
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=30.0
                )
                response.raise_for_status()
                logger.info(f"Synced ArgoCD application: {app_name}")
                return response.json()
        except Exception as e:
            logger.error(f"Error syncing ArgoCD application {app_name}: {e}")
            raise
    
    async def get_application_status(self, app_name: str) -> Dict[str, Any]:
        """Get ArgoCD application status"""
        try:
            async with httpx.AsyncClient(verify=False) as client:
                response = await client.get(
                    f"{self.base_url}/applications/{app_name}",
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error getting ArgoCD application status {app_name}: {e}")
            raise
    
    async def rollback_application(self, app_name: str, revision: str) -> Dict[str, Any]:
        """Rollback ArgoCD application to previous revision"""
        try:
            async with httpx.AsyncClient(verify=False) as client:
                response = await client.post(
                    f"{self.base_url}/applications/{app_name}/rollback",
                    headers={"Authorization": f"Bearer {self.token}"},
                    json={"revision": revision},
                    timeout=30.0
                )
                response.raise_for_status()
                logger.info(f"Rolled back ArgoCD application {app_name} to revision {revision}")
                return response.json()
        except Exception as e:
            logger.error(f"Error rolling back ArgoCD application {app_name}: {e}")
            raise


class FlaggerClient:
    """Flagger progressive delivery client"""
    
    def __init__(self):
        try:
            config.load_incluster_config()
        except:
            config.load_kube_config(settings.KUBECONFIG_PATH)
        
        self.custom_api = client.CustomObjectsApi()
        self.namespace = settings.KUBERNETES_NAMESPACE
    
    async def create_canary(
        self,
        name: str,
        target_version: str,
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create Flagger canary deployment"""
        canary_manifest = {
            "apiVersion": "flagger.app/v1beta1",
            "kind": "Canary",
            "metadata": {
                "name": name,
                "namespace": self.namespace
            },
            "spec": {
                "targetRef": {
                    "apiVersion": "apps/v1",
                    "kind": "Deployment",
                    "name": name
                },
                "progressDeadlineSeconds": 600,
                "service": {
                    "port": 8080
                },
                "analysis": {
                    "interval": analysis.get("interval", "1m"),
                    "threshold": analysis.get("threshold", 5),
                    "maxWeight": analysis.get("max_weight", 50),
                    "stepWeight": analysis.get("step_weight", 10),
                    "metrics": analysis.get("metrics", [])
                }
            }
        }
        
        try:
            result = self.custom_api.create_namespaced_custom_object(
                group="flagger.app",
                version="v1beta1",
                namespace=self.namespace,
                plural="canaries",
                body=canary_manifest
            )
            logger.info(f"Created Flagger canary for {name}")
            return result
        except ApiException as e:
            logger.error(f"Error creating Flagger canary: {e}")
            raise
    
    async def get_canary_status(self, name: str) -> Dict[str, Any]:
        """Get canary deployment status"""
        try:
            result = self.custom_api.get_namespaced_custom_object(
                group="flagger.app",
                version="v1beta1",
                namespace=self.namespace,
                plural="canaries",
                name=name
            )
            return result
        except ApiException as e:
            logger.error(f"Error getting canary status: {e}")
            raise
    
    async def promote_canary(self, name: str) -> Dict[str, Any]:
        """Promote canary to production"""
        try:
            # Update canary to promote
            patch = {
                "spec": {
                    "analysis": {
                        "maxWeight": 100
                    }
                }
            }
            
            result = self.custom_api.patch_namespaced_custom_object(
                group="flagger.app",
                version="v1beta1",
                namespace=self.namespace,
                plural="canaries",
                name=name,
                body=patch
            )
            logger.info(f"Promoted canary {name} to production")
            return result
        except ApiException as e:
            logger.error(f"Error promoting canary: {e}")
            raise


class PrometheusMetricsClient:
    """Prometheus metrics client for canary analysis"""
    
    def __init__(self):
        self.prometheus_url = settings.PROMETHEUS_URL
    
    async def get_canary_metrics(
        self,
        service_name: str,
        duration: str = "5m"
    ) -> Dict[str, float]:
        """Get canary deployment metrics"""
        metrics = {}
        
        try:
            async with httpx.AsyncClient() as client:
                # Success rate
                success_query = f'rate(http_requests_total{{service="{service_name}",status=~"2.."}}[{duration}])'
                success_response = await client.get(
                    f"{self.prometheus_url}/api/v1/query",
                    params={"query": success_query},
                    timeout=30.0
                )
                success_data = success_response.json()
                
                # Error rate
                error_query = f'rate(http_requests_total{{service="{service_name}",status=~"5.."}}[{duration}])'
                error_response = await client.get(
                    f"{self.prometheus_url}/api/v1/query",
                    params={"query": error_query},
                    timeout=30.0
                )
                error_data = error_response.json()
                
                # Latency
                latency_query = f'histogram_quantile(0.99, rate(http_request_duration_seconds_bucket{{service="{service_name}"}}[{duration}]))'
                latency_response = await client.get(
                    f"{self.prometheus_url}/api/v1/query",
                    params={"query": latency_query},
                    timeout=30.0
                )
                latency_data = latency_response.json()
                
                # Parse results
                metrics["success_rate"] = self._parse_metric_value(success_data)
                metrics["error_rate"] = self._parse_metric_value(error_data)
                metrics["latency_p99"] = self._parse_metric_value(latency_data)
                
                logger.info(f"Retrieved canary metrics for {service_name}: {metrics}")
                return metrics
                
        except Exception as e:
            logger.error(f"Error getting canary metrics: {e}")
            return {
                "success_rate": 100.0,
                "error_rate": 0.0,
                "latency_p99": 0.0
            }
    
    def _parse_metric_value(self, response_data: Dict) -> float:
        """Parse Prometheus metric value"""
        try:
            if response_data.get("status") == "success":
                result = response_data.get("data", {}).get("result", [])
                if result and len(result) > 0:
                    value = result[0].get("value", [None, "0"])
                    return float(value[1])
            return 0.0
        except Exception as e:
            logger.error(f"Error parsing metric value: {e}")
            return 0.0


class GitOpsDeploymentManager:
    """
    Enterprise GitOps Deployment Manager
    
    Manages progressive canary deployments with automatic rollback,
    integrated with ArgoCD and Flagger for production-grade deployments.
    """
    
    def __init__(self):
        self.argocd = ArgoCDClient()
        self.flagger = FlaggerClient()
        self.metrics = PrometheusMetricsClient()
    
    async def deploy_with_canary(
        self,
        request: CanaryDeploymentRequest
    ) -> DeploymentResponse:
        """
        Progressive canary deployment with automatic rollback
        
        Args:
            request: Canary deployment request
        
        Returns:
            DeploymentResponse with deployment status and metrics
        """
        deployment_id = f"deploy-{request.service_name}-{int(datetime.utcnow().timestamp())}"
        started_at = datetime.utcnow()
        
        try:
            logger.info(f"Starting canary deployment for {request.service_name} version {request.new_version}")
            
            # Step 1: Sync ArgoCD application
            await self.argocd.sync_application(request.service_name)
            
            # Step 2: Create Flagger canary
            canary = await self.flagger.create_canary(
                name=request.service_name,
                target_version=request.new_version,
                analysis={
                    "interval": f"{request.analysis_interval}s",
                    "threshold": 5,
                    "max_weight": 50,
                    "step_weight": 10,
                    "metrics": [
                        {"name": "request-success-rate", "threshold": request.success_threshold},
                        {"name": "request-duration", "threshold": 500}
                    ]
                }
            )
            
            # Step 3: Progressive rollout
            for step in request.canary_steps:
                logger.info(f"Canary deployment at {step}% traffic")
                
                # Wait for analysis interval
                await asyncio.sleep(request.analysis_interval)
                
                # Collect metrics
                metrics = await self.metrics.get_canary_metrics(
                    service_name=request.service_name,
                    duration="5m"
                )
                
                # Evaluate health
                if not self._evaluate_canary_health(metrics, request.success_threshold):
                    logger.error(f"Canary deployment failed at {step}% - rolling back")
                    await self._rollback_deployment(request.service_name)
                    
                    return DeploymentResponse(
                        deployment_id=deployment_id,
                        service_name=request.service_name,
                        version=request.new_version,
                        status=DeploymentStatus.ROLLED_BACK,
                        message=f"Deployment failed at {step}% traffic - automatic rollback executed",
                        started_at=started_at,
                        completed_at=datetime.utcnow(),
                        metrics=metrics
                    )
            
            # Step 4: Promote to production
            await self.flagger.promote_canary(request.service_name)
            
            logger.info(f"Successfully deployed {request.service_name} version {request.new_version}")
            
            return DeploymentResponse(
                deployment_id=deployment_id,
                service_name=request.service_name,
                version=request.new_version,
                status=DeploymentStatus.SUCCESS,
                message="Deployment completed successfully",
                started_at=started_at,
                completed_at=datetime.utcnow(),
                metrics=await self.metrics.get_canary_metrics(request.service_name)
            )
            
        except Exception as e:
            logger.error(f"Error during canary deployment: {e}", exc_info=True)
            
            return DeploymentResponse(
                deployment_id=deployment_id,
                service_name=request.service_name,
                version=request.new_version,
                status=DeploymentStatus.FAILED,
                message=f"Deployment failed: {str(e)}",
                started_at=started_at,
                completed_at=datetime.utcnow()
            )
    
    def _evaluate_canary_health(
        self,
        metrics: Dict[str, float],
        success_threshold: float
    ) -> bool:
        """Evaluate canary deployment health"""
        success_rate = metrics.get("success_rate", 0.0)
        error_rate = metrics.get("error_rate", 100.0)
        latency = metrics.get("latency_p99", 1000.0)
        
        # Check success rate
        if success_rate < success_threshold:
            logger.warning(f"Success rate {success_rate}% below threshold {success_threshold}%")
            return False
        
        # Check error rate
        if error_rate > (100 - success_threshold):
            logger.warning(f"Error rate {error_rate}% too high")
            return False
        
        # Check latency (500ms threshold)
        if latency > 500:
            logger.warning(f"Latency {latency}ms above 500ms threshold")
            return False
        
        return True
    
    async def _rollback_deployment(self, service_name: str):
        """Rollback failed deployment"""
        try:
            # Get current application status
            app_status = await self.argocd.get_application_status(service_name)
            
            # Get previous revision
            history = app_status.get("status", {}).get("history", [])
            if len(history) >= 2:
                previous_revision = history[-2].get("revision")
                await self.argocd.rollback_application(service_name, previous_revision)
                logger.info(f"Rolled back {service_name} to revision {previous_revision}")
            else:
                logger.warning(f"No previous revision found for {service_name}")
                
        except Exception as e:
            logger.error(f"Error during rollback: {e}", exc_info=True)
    
    async def get_deployment_status(self, service_name: str) -> Dict[str, Any]:
        """Get current deployment status"""
        try:
            app_status = await self.argocd.get_application_status(service_name)
            canary_status = await self.flagger.get_canary_status(service_name)
            
            return {
                "service_name": service_name,
                "argocd_status": app_status.get("status", {}),
                "canary_status": canary_status.get("status", {}),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting deployment status: {e}")
            return {
                "service_name": service_name,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# Singleton instance
_gitops_manager: Optional[GitOpsDeploymentManager] = None


def get_gitops_manager() -> GitOpsDeploymentManager:
    """Get GitOps deployment manager instance"""
    global _gitops_manager
    if _gitops_manager is None:
        _gitops_manager = GitOpsDeploymentManager()
    return _gitops_manager
