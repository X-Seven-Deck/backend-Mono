"""
API Gateway Configuration Settings

Comprehensive configuration for all gateway features including service discovery,
rate limiting, circuit breaker, authentication, and more.
"""

import os
from typing import List, Dict, Any
from pydantic import Field
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """API Gateway settings with comprehensive configuration"""
    
    # Application settings
    app_name: str = "X-sevenAI API Gateway"
    environment: str = Field(default="development", env="ENVIRONMENT")
    service_host: str = Field(default="0.0.0.0", env="GATEWAY_SERVICE_HOST")
    service_port: int = Field(default=8000, env="GATEWAY_SERVICE_PORT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    api_prefix: str = "/api/v1"
    enable_docs: bool = Field(default=True, env="ENABLE_DOCS")
    
    # CORS settings
    cors_origins: List[str] = Field(
        default=["*"],
        env="CORS_ORIGINS"
    )
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]
    
    # Service URLs - Internal microservices
    auth_service_url: str = Field(
        default="http://auth-service:8010",
        env="AUTH_SERVICE_URL"
    )
    business_logic_service_url: str = Field(
        default="http://business-logic-service:8020",
        env="BUSINESS_LOGIC_SERVICE_URL"
    )
    ai_orchestration_service_url: str = Field(
        default="http://ai-orchestration-service:8030",
        env="AI_ORCHESTRATION_SERVICE_URL"
    )
    chat_communication_service_url: str = Field(
        default="http://chat-communication-service:8040",
        env="CHAT_COMMUNICATION_SERVICE_URL"
    )
    analytics_dashboard_service_url: str = Field(
        default="http://analytics-dashboard-service:8050",
        env="ANALYTICS_DASHBOARD_SERVICE_URL"
    )
    notification_integration_service_url: str = Field(
        default="http://notification-integration-service:8060",
        env="NOTIFICATION_INTEGRATION_SERVICE_URL"
    )
    global_chat_service_url: str = Field(
        default="http://global-chat-service:8070",
        env="GLOBAL_CHAT_SERVICE_URL"
    )
    dedicated_business_chat_service_url: str = Field(
        default="http://dedicated-business-chat-service:8050",
        env="DEDICATED_BUSINESS_CHAT_SERVICE_URL"
    )
    pos_service_url: str = Field(
        default="http://pos-service:8070",
        env="POS_SERVICE_URL"
    )
    template_selection_service_url: str = Field(
        default="http://template-selection-service:8090",
        env="TEMPLATE_SELECTION_SERVICE_URL"
    )
    monitoring_logging_service_url: str = Field(
        default="http://monitoring-logging-service:8080",
        env="MONITORING_LOGGING_SERVICE_URL"
    )
    devops_service_url: str = Field(
        default="http://devops-service:8100",
        env="DEVOPS_SERVICE_URL"
    )
    
    # Authentication settings
    jwt_secret: str = Field(default="your-secret-key", env="JWT_SECRET")
    jwt_algorithm: str = "HS256"
    jwt_expiry_seconds: int = Field(default=3600, env="JWT_EXPIRY")
    enable_oauth2: bool = Field(default=True, env="ENABLE_OAUTH2")
    enable_api_key_auth: bool = Field(default=True, env="ENABLE_API_KEY_AUTH")
    
    # Supabase settings
    supabase_url: str = Field(default="", env="SUPABASE_URL")
    supabase_anon_key: str = Field(default="", env="SUPABASE_ANON_KEY")
    supabase_service_key: str = Field(default="", env="SUPABASE_SERVICE_ROLE_KEY")
    
    # Redis settings for rate limiting and caching
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_password: str = Field(default="", env="REDIS_PASSWORD")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_ssl: bool = Field(default=False, env="REDIS_SSL")
    
    # Rate limiting settings
    enable_rate_limiting: bool = Field(default=True, env="ENABLE_RATE_LIMITING")
    default_rate_limit: int = Field(default=100, env="DEFAULT_RATE_LIMIT")  # requests per minute
    rate_limit_window: int = Field(default=60, env="RATE_LIMIT_WINDOW")  # seconds
    
    # Tier-based rate limits
    rate_limit_guest: int = Field(default=20, env="RATE_LIMIT_GUEST")
    rate_limit_basic: int = Field(default=100, env="RATE_LIMIT_BASIC")
    rate_limit_premium: int = Field(default=500, env="RATE_LIMIT_PREMIUM")
    rate_limit_enterprise: int = Field(default=2000, env="RATE_LIMIT_ENTERPRISE")
    
    # Circuit breaker settings
    enable_circuit_breaker: bool = Field(default=True, env="ENABLE_CIRCUIT_BREAKER")
    circuit_breaker_failure_threshold: int = Field(default=5, env="CB_FAILURE_THRESHOLD")
    circuit_breaker_timeout: int = Field(default=60, env="CB_TIMEOUT")  # seconds
    circuit_breaker_recovery_timeout: int = Field(default=30, env="CB_RECOVERY_TIMEOUT")
    
    # Health check settings
    health_check_interval: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")  # seconds
    health_check_timeout: int = Field(default=5, env="HEALTH_CHECK_TIMEOUT")
    health_check_enabled: bool = Field(default=True, env="HEALTH_CHECK_ENABLED")
    
    # Request timeout settings
    default_request_timeout: int = Field(default=30, env="DEFAULT_REQUEST_TIMEOUT")  # seconds
    ai_request_timeout: int = Field(default=60, env="AI_REQUEST_TIMEOUT")
    analytics_request_timeout: int = Field(default=45, env="ANALYTICS_REQUEST_TIMEOUT")
    
    # Retry settings
    enable_retries: bool = Field(default=True, env="ENABLE_RETRIES")
    max_retries: int = Field(default=3, env="MAX_RETRIES")
    retry_backoff_factor: float = Field(default=2.0, env="RETRY_BACKOFF_FACTOR")
    
    # Security settings
    enable_security_headers: bool = Field(default=True, env="ENABLE_SECURITY_HEADERS")
    enable_request_validation: bool = Field(default=True, env="ENABLE_REQUEST_VALIDATION")
    enable_response_validation: bool = Field(default=False, env="ENABLE_RESPONSE_VALIDATION")
    max_request_size: int = Field(default=10485760, env="MAX_REQUEST_SIZE")  # 10MB
    enable_ip_whitelist: bool = Field(default=False, env="ENABLE_IP_WHITELIST")
    ip_whitelist: List[str] = Field(default=[], env="IP_WHITELIST")
    
    # Multi-tenancy settings
    enable_multi_tenancy: bool = Field(default=True, env="ENABLE_MULTI_TENANCY")
    tenant_header_name: str = "X-Tenant-ID"
    require_tenant_id: bool = Field(default=False, env="REQUIRE_TENANT_ID")
    
    # Monitoring and metrics
    enable_prometheus: bool = Field(default=True, env="ENABLE_PROMETHEUS")
    enable_distributed_tracing: bool = Field(default=True, env="ENABLE_DISTRIBUTED_TRACING")
    enable_request_logging: bool = Field(default=True, env="ENABLE_REQUEST_LOGGING")
    log_request_body: bool = Field(default=False, env="LOG_REQUEST_BODY")
    log_response_body: bool = Field(default=False, env="LOG_RESPONSE_BODY")
    
    # WebSocket settings
    enable_websocket_proxy: bool = Field(default=True, env="ENABLE_WEBSOCKET_PROXY")
    websocket_ping_interval: int = Field(default=20, env="WS_PING_INTERVAL")
    websocket_ping_timeout: int = Field(default=60, env="WS_PING_TIMEOUT")
    
    # API Versioning
    enable_api_versioning: bool = Field(default=True, env="ENABLE_API_VERSIONING")
    api_versions: List[str] = Field(default=["v1"], env="API_VERSIONS")
    default_api_version: str = "v1"
    
    # Entry points configuration
    enable_qr_entry: bool = Field(default=True, env="ENABLE_QR_ENTRY")
    enable_whatsapp_entry: bool = Field(default=True, env="ENABLE_WHATSAPP_ENTRY")
    enable_social_entry: bool = Field(default=True, env="ENABLE_SOCIAL_ENTRY")
    enable_voice_entry: bool = Field(default=True, env="ENABLE_VOICE_ENTRY")
    enable_web_entry: bool = Field(default=True, env="ENABLE_WEB_ENTRY")
    enable_api_entry: bool = Field(default=True, env="ENABLE_API_ENTRY")
    
    # Caching settings
    enable_response_cache: bool = Field(default=True, env="ENABLE_RESPONSE_CACHE")
    cache_ttl: int = Field(default=300, env="CACHE_TTL")  # seconds
    cache_max_size: int = Field(default=1000, env="CACHE_MAX_SIZE")
    
    # Load balancing
    enable_load_balancing: bool = Field(default=False, env="ENABLE_LOAD_BALANCING")
    load_balance_algorithm: str = Field(default="round_robin", env="LOAD_BALANCE_ALGORITHM")
    
    # Service discovery
    enable_service_discovery: bool = Field(default=False, env="ENABLE_SERVICE_DISCOVERY")
    service_discovery_type: str = Field(default="static", env="SERVICE_DISCOVERY_TYPE")  # static, consul, kubernetes
    
    # Request transformation
    enable_request_transformation: bool = Field(default=True, env="ENABLE_REQUEST_TRANSFORMATION")
    enable_response_transformation: bool = Field(default=True, env="ENABLE_RESPONSE_TRANSFORMATION")
    
    # Admin API
    enable_admin_api: bool = Field(default=True, env="ENABLE_ADMIN_API")
    admin_api_key: str = Field(default="admin-secret-key", env="ADMIN_API_KEY")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        env_file_encoding = "utf-8"
    
    def get_service_url(self, service_name: str) -> str:
        """Get service URL by service name"""
        service_url_map = {
            "auth-service": self.auth_service_url,
            "business-logic-service": self.business_logic_service_url,
            "ai-orchestration-service": self.ai_orchestration_service_url,
            "chat-communication-service": self.chat_communication_service_url,
            "analytics-dashboard-service": self.analytics_dashboard_service_url,
            "notification-integration-service": self.notification_integration_service_url,
            "global-chat-service": self.global_chat_service_url,
            "dedicated-business-chat-service": self.dedicated_business_chat_service_url,
            "pos-service": self.pos_service_url,
            "template-selection-service": self.template_selection_service_url,
            "monitoring-logging-service": self.monitoring_logging_service_url,
            "devops-service": self.devops_service_url,
        }
        return service_url_map.get(service_name, "")
    
    def get_rate_limit_for_tier(self, tier: str) -> int:
        """Get rate limit based on subscription tier"""
        tier_limits = {
            "guest": self.rate_limit_guest,
            "basic": self.rate_limit_basic,
            "premium": self.rate_limit_premium,
            "enterprise": self.rate_limit_enterprise,
        }
        return tier_limits.get(tier.lower(), self.default_rate_limit)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
