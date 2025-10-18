"""
Configuration Management
Centralized settings for POS microservice
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Service
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    POS_SERVICE_HOST: str = "0.0.0.0"
    POS_SERVICE_PORT: int = 8070
    
    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_KEY: str
    
    # Authentication
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY: int = 86400
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 1
    REDIS_PASSWORD: str = ""
    REDIS_TTL: int = 3600
    
    # Inter-Service
    DASHBOARD_SERVICE_URL: str = "http://localhost:8060"
    API_GATEWAY_URL: str = "http://localhost:8000"
    
    # CORS
    CORS_ORIGINS: str = "*"
    CORS_ALLOW_CREDENTIALS: bool = True
    
    # Tax
    DEFAULT_TAX_RATE: float = 0.10
    TAX_CALCULATION_MODE: str = "location_based"
    
    # Receipt
    RECEIPT_PREFIX: str = "RCP"
    BUSINESS_NAME: str = "Xseven Business"
    BUSINESS_ADDRESS: str = "123 Main St"
    BUSINESS_PHONE: str = "+1234567890"
    
    # Monitoring
    PROMETHEUS_ENABLED: bool = True
    PROMETHEUS_PORT: int = 9091
    
    # Feature Flags
    ENABLE_OFFLINE_MODE: bool = True
    ENABLE_PUSH_NOTIFICATIONS: bool = True
    ENABLE_RECEIPT_EMAIL: bool = True
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins"""
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    # Add the extra fields that are in .env but not in the model
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_PROJECT_ID: str = ""
    
    class Config:
        env_file = "/Users/naveen/Desktop/x7AI/services/pos-service/.env"
        case_sensitive = True
        extra = "allow"  # This will ignore extra fields in .env


# Singleton settings instance
settings = Settings()
