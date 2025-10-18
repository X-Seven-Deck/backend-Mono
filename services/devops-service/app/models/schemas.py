"""
DevOps Service Data Models
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class DeploymentStatus(str, Enum):
    """Deployment status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class IncidentSeverity(str, Enum):
    """Incident severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(str, Enum):
    """Incident status"""
    OPEN = "open"
    INVESTIGATING = "investigating"
    IDENTIFIED = "identified"
    MONITORING = "monitoring"
    RESOLVED = "resolved"


class ChaosExperimentType(str, Enum):
    """Types of chaos experiments"""
    POD_FAILURE = "pod_failure"
    NETWORK_LATENCY = "network_latency"
    CPU_STRESS = "cpu_stress"
    MEMORY_STRESS = "memory_stress"
    DATABASE_FAILURE = "database_failure"
    NETWORK_PARTITION = "network_partition"


class SLIType(str, Enum):
    """Service Level Indicator types"""
    AVAILABILITY = "availability"
    LATENCY = "latency"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"


# Deployment Models
class CanaryDeploymentRequest(BaseModel):
    """Request to deploy with canary strategy"""
    service_name: str = Field(..., description="Name of the service to deploy")
    new_version: str = Field(..., description="New version to deploy")
    canary_steps: List[int] = Field(default=[10, 25, 50, 75, 100], description="Traffic percentage steps")
    analysis_interval: int = Field(default=300, description="Analysis interval in seconds")
    success_threshold: float = Field(default=99.0, description="Success rate threshold")


class DeploymentResponse(BaseModel):
    """Deployment response"""
    deployment_id: str
    service_name: str
    version: str
    status: DeploymentStatus
    message: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    metrics: Optional[Dict[str, Any]] = None


# Incident Management Models
class IncidentCreate(BaseModel):
    """Create incident request"""
    title: str = Field(..., description="Incident title")
    description: str = Field(..., description="Incident description")
    severity: IncidentSeverity = Field(..., description="Incident severity")
    service: str = Field(..., description="Affected service")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class Incident(BaseModel):
    """Incident model"""
    incident_id: str
    title: str
    description: str
    severity: IncidentSeverity
    status: IncidentStatus
    service: str
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    war_room_url: Optional[str] = None
    pagerduty_incident_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PostMortem(BaseModel):
    """Post-mortem report"""
    incident_id: str
    title: str
    timeline: List[Dict[str, Any]]
    root_cause: str
    impact: Dict[str, Any]
    action_items: List[Dict[str, Any]]
    created_at: datetime


# Chaos Engineering Models
class ChaosExperimentRequest(BaseModel):
    """Chaos experiment request"""
    experiment_type: ChaosExperimentType
    target_service: str
    duration: int = Field(default=300, description="Experiment duration in seconds")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Experiment-specific parameters")


class ChaosExperimentResult(BaseModel):
    """Chaos experiment result"""
    experiment_id: str
    experiment_type: ChaosExperimentType
    target_service: str
    resilience_score: float
    started_at: datetime
    completed_at: datetime
    metrics: Dict[str, Any]
    observations: List[str]
    recommendations: List[str]


# SLO Models
class SLODefinition(BaseModel):
    """Service Level Objective definition"""
    service_name: str
    sli_type: SLIType
    target: float = Field(..., description="Target percentage (e.g., 99.9 for 99.9%)")
    window_days: int = Field(default=30, description="Rolling window in days")


class SLOStatus(BaseModel):
    """Current SLO status"""
    service_name: str
    sli_type: SLIType
    target: float
    current_value: float
    error_budget_remaining: float
    is_compliant: bool
    window_start: datetime
    window_end: datetime


# Observability Models
class MetricQuery(BaseModel):
    """Prometheus metric query"""
    query: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    step: Optional[str] = Field(default="1m", description="Query resolution step")


class MetricResult(BaseModel):
    """Metric query result"""
    metric_name: str
    values: List[Dict[str, Any]]
    labels: Dict[str, str]


class AlertRule(BaseModel):
    """Prometheus alert rule"""
    alert_name: str
    expr: str
    duration: str = Field(default="5m", description="Alert duration")
    severity: str = Field(default="warning", description="Alert severity")
    annotations: Dict[str, str]
    labels: Dict[str, str]


# Performance Optimization Models
class CacheConfiguration(BaseModel):
    """Multi-layer cache configuration"""
    l1_ttl: int = Field(default=300, description="L1 cache TTL in seconds")
    l2_ttl: int = Field(default=3600, description="L2 cache TTL in seconds")
    l3_ttl: int = Field(default=86400, description="L3 cache TTL in seconds")
    enabled_layers: List[str] = Field(default=["l1", "l2"], description="Enabled cache layers")


class AutoScalingConfig(BaseModel):
    """Auto-scaling configuration"""
    service_name: str
    min_replicas: int = Field(default=2, description="Minimum replicas")
    max_replicas: int = Field(default=10, description="Maximum replicas")
    target_cpu_utilization: int = Field(default=70, description="Target CPU utilization percentage")
    target_memory_utilization: int = Field(default=80, description="Target memory utilization percentage")
    scale_up_cooldown: int = Field(default=300, description="Scale up cooldown in seconds")
    scale_down_cooldown: int = Field(default=600, description="Scale down cooldown in seconds")


# Health Check Models
class HealthCheck(BaseModel):
    """Service health check"""
    service: str
    status: str
    version: str
    timestamp: datetime
    checks: Dict[str, bool]
    metrics: Optional[Dict[str, Any]] = None


class SystemHealth(BaseModel):
    """Overall system health"""
    status: str
    services: List[HealthCheck]
    timestamp: datetime
    regions: List[str]
    overall_availability: float
