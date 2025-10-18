"""
DevOps Service Configuration
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings"""
    
    # Service Configuration
    SERVICE_NAME: str = "devops-service"
    SERVICE_PORT: int = 8100
    ENVIRONMENT: str = "development"
    
    # Kubernetes Configuration
    KUBECONFIG_PATH: str = "/path/to/kubeconfig"
    KUBERNETES_NAMESPACE: str = "x7ai-production"
    
    # ArgoCD Configuration
    ARGOCD_SERVER: str = "argocd.x7ai.com"
    ARGOCD_TOKEN: str = ""
    ARGOCD_NAMESPACE: str = "argocd"
    
    # Prometheus Configuration
    PROMETHEUS_URL: str = "http://prometheus:9090"
    PROMETHEUS_PUSHGATEWAY_URL: str = "http://pushgateway:9091"
    
    # Grafana Configuration
    GRAFANA_URL: str = "http://grafana:3000"
    GRAFANA_API_KEY: str = ""
    
    # Jaeger Configuration
    JAEGER_AGENT_HOST: str = "jaeger"
    JAEGER_AGENT_PORT: int = 6831
    
    # PagerDuty Configuration
    PAGERDUTY_API_KEY: str = ""
    PAGERDUTY_INTEGRATION_KEY: str = ""
    
    # Slack Configuration
    SLACK_WEBHOOK_URL: str = ""
    SLACK_BOT_TOKEN: str = ""
    
    # Chaos Engineering
    CHAOS_MESH_NAMESPACE: str = "chaos-testing"
    CHAOS_EXPERIMENTS_ENABLED: bool = False
    
    # Redis Configuration
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 5
    
    # Multi-Region Configuration
    PRIMARY_REGION: str = "us-east-1"
    SECONDARY_REGIONS: str = "us-west-1,eu-west-1"
    ENABLE_MULTI_REGION: bool = False
    
    # SLO Configuration
    DEFAULT_AVAILABILITY_SLO: float = 99.9
    DEFAULT_LATENCY_SLO_MS: int = 500
    DEFAULT_ERROR_RATE_SLO: float = 1.0
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @property
    def secondary_regions_list(self) -> List[str]:
        """Get secondary regions as list"""
        return [r.strip() for r in self.SECONDARY_REGIONS.split(',') if r.strip()]
    
    @property
    def all_regions(self) -> List[str]:
        """Get all regions including primary"""
        return [self.PRIMARY_REGION] + self.secondary_regions_list


settings = Settings()
