"""
Business Logic Service Configuration

Centralized configuration management with environment variables.
"""

from pydantic import BaseSettings, Field
from typing import Optional, List
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Service Information
    SERVICE_NAME: str = "business-logic-service"
    SERVICE_VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # Server Configuration
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8020, env="BUSINESS_LOGIC_PORT")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Database - Supabase
    SUPABASE_URL: str = Field(..., env="SUPABASE_URL")
    SUPABASE_ANON_KEY: str = Field(..., env="SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_ROLE_KEY: str = Field(..., env="SUPABASE_SERVICE_ROLE_KEY")
    DATABASE_POOL_SIZE: int = Field(default=20, env="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(default=10, env="DATABASE_MAX_OVERFLOW")
    
    # Redis Configuration
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")
    REDIS_PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    REDIS_POOL_SIZE: int = Field(default=10, env="REDIS_POOL_SIZE")
    REDIS_TTL: int = Field(default=3600, env="REDIS_TTL")  # 1 hour default
    
    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS: str = Field(
        default="localhost:9092",
        env="KAFKA_BOOTSTRAP_SERVERS"
    )
    KAFKA_CONSUMER_GROUP: str = Field(
        default="business-logic-service",
        env="KAFKA_CONSUMER_GROUP"
    )
    KAFKA_TOPICS_ORDERS: str = Field(default="orders", env="KAFKA_TOPIC_ORDERS")
    KAFKA_TOPICS_RESERVATIONS: str = Field(
        default="reservations",
        env="KAFKA_TOPIC_RESERVATIONS"
    )
    KAFKA_TOPICS_INVENTORY: str = Field(
        default="inventory",
        env="KAFKA_TOPIC_INVENTORY"
    )
    KAFKA_TOPICS_PAYMENTS: str = Field(
        default="payments",
        env="KAFKA_TOPIC_PAYMENTS"
    )
    
    # Temporal Configuration
    TEMPORAL_HOST: str = Field(default="localhost", env="TEMPORAL_HOST")
    TEMPORAL_PORT: int = Field(default=7233, env="TEMPORAL_PORT")
    TEMPORAL_NAMESPACE: str = Field(default="default", env="TEMPORAL_NAMESPACE")
    TEMPORAL_TASK_QUEUE: str = Field(
        default="business-logic-queue",
        env="TEMPORAL_TASK_QUEUE"
    )
    
    # External Service URLs
    AI_ORCHESTRATION_URL: str = Field(
        default="http://localhost:8010",
        env="AI_ORCHESTRATION_URL"
    )
    TEMPLATE_SELECTION_URL: str = Field(
        default="http://localhost:8090",
        env="TEMPLATE_SELECTION_URL"
    )
    ANALYTICS_DASHBOARD_URL: str = Field(
        default="http://localhost:8030",
        env="ANALYTICS_DASHBOARD_URL"
    )
    NOTIFICATION_SERVICE_URL: str = Field(
        default="http://localhost:8050",
        env="NOTIFICATION_SERVICE_URL"
    )
    
    # Payment Processors
    STRIPE_API_KEY: Optional[str] = Field(default=None, env="STRIPE_API_KEY")
    STRIPE_WEBHOOK_SECRET: Optional[str] = Field(
        default=None,
        env="STRIPE_WEBHOOK_SECRET"
    )
    SQUARE_ACCESS_TOKEN: Optional[str] = Field(default=None, env="SQUARE_ACCESS_TOKEN")
    SQUARE_LOCATION_ID: Optional[str] = Field(default=None, env="SQUARE_LOCATION_ID")
    
    # HashiCorp Vault
    VAULT_ADDR: Optional[str] = Field(default=None, env="VAULT_ADDR")
    VAULT_TOKEN: Optional[str] = Field(default=None, env="VAULT_TOKEN")
    VAULT_NAMESPACE: Optional[str] = Field(default=None, env="VAULT_NAMESPACE")
    VAULT_MOUNT_POINT: str = Field(default="secret", env="VAULT_MOUNT_POINT")
    
    # Security
    JWT_SECRET_KEY: str = Field(..., env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    JWT_EXPIRATION_MINUTES: int = Field(default=60, env="JWT_EXPIRATION_MINUTES")
    ALLOWED_ORIGINS: List[str] = Field(
        default=["*"],
        env="ALLOWED_ORIGINS"
    )
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=100, env="RATE_LIMIT_PER_MINUTE")
    RATE_LIMIT_BURST: int = Field(default=20, env="RATE_LIMIT_BURST")
    
    # Monitoring
    PROMETHEUS_ENABLED: bool = Field(default=True, env="PROMETHEUS_ENABLED")
    SENTRY_DSN: Optional[str] = Field(default=None, env="SENTRY_DSN")
    SENTRY_ENVIRONMENT: Optional[str] = Field(default=None, env="SENTRY_ENVIRONMENT")
    SENTRY_TRACES_SAMPLE_RATE: float = Field(
        default=1.0,
        env="SENTRY_TRACES_SAMPLE_RATE"
    )
    
    # OpenTelemetry
    OTEL_ENABLED: bool = Field(default=True, env="OTEL_ENABLED")
    OTEL_EXPORTER_OTLP_ENDPOINT: Optional[str] = Field(
        default=None,
        env="OTEL_EXPORTER_OTLP_ENDPOINT"
    )
    OTEL_SERVICE_NAME: str = Field(
        default="business-logic-service",
        env="OTEL_SERVICE_NAME"
    )
    
    # Business Logic Settings
    DEFAULT_TAX_RATE: float = Field(default=0.10, env="DEFAULT_TAX_RATE")
    DEFAULT_RESERVATION_DURATION: int = Field(
        default=90,
        env="DEFAULT_RESERVATION_DURATION"
    )  # minutes
    INVENTORY_LOW_STOCK_THRESHOLD: float = Field(
        default=0.2,
        env="INVENTORY_LOW_STOCK_THRESHOLD"
    )  # 20%
    ORDER_PREP_TIME_BUFFER: int = Field(
        default=15,
        env="ORDER_PREP_TIME_BUFFER"
    )  # minutes
    
    # Feature Flags
    ENABLE_AI_FEATURES: bool = Field(default=True, env="ENABLE_AI_FEATURES")
    ENABLE_TEMPORAL_WORKFLOWS: bool = Field(
        default=True,
        env="ENABLE_TEMPORAL_WORKFLOWS"
    )
    ENABLE_KAFKA_EVENTS: bool = Field(default=True, env="ENABLE_KAFKA_EVENTS")
    ENABLE_CACHING: bool = Field(default=True, env="ENABLE_CACHING")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    @property
    def redis_url(self) -> str:
        """Get Redis URL"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    @property
    def temporal_url(self) -> str:
        """Get Temporal server URL"""
        return f"{self.TEMPORAL_HOST}:{self.TEMPORAL_PORT}"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.ENVIRONMENT.lower() == "development"


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get settings singleton"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


# Convenience function to reload settings
def reload_settings() -> Settings:
    """Reload settings from environment"""
    global _settings
    _settings = Settings()
    return _settings
