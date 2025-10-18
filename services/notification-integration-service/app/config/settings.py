"""
Configuration settings for Notification Integration Service
"""

import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Service configuration
    service_name: str = "notification-integration-service"
    service_host: str = "0.0.0.0"
    service_port: int = 8006
    environment: str = os.getenv("ENVIRONMENT", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # CORS settings
    cors_origins: List[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]
    
    # Twilio configuration
    twilio_account_sid: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    twilio_auth_token: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    twilio_phone_number: str = os.getenv("TWILIO_PHONE_NUMBER", "")
    twilio_whatsapp_number: str = os.getenv("TWILIO_WHATSAPP_NUMBER", "")
    
    # SendGrid configuration
    sendgrid_api_key: str = os.getenv("SENDGRID_API_KEY", "")
    sendgrid_from_email: str = os.getenv("SENDGRID_FROM_EMAIL", "noreply@x7ai.com")
    sendgrid_from_name: str = os.getenv("SENDGRID_FROM_NAME", "X-sevenAI")
    
    # Zapier configuration
    zapier_webhook_url: str = os.getenv("ZAPIER_WEBHOOK_URL", "")
    zapier_api_key: str = os.getenv("ZAPIER_API_KEY", "")
    
    # Kafka configuration
    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    kafka_notification_topic: str = "notifications"
    kafka_consumer_group: str = "notification-service-group"
    
    # Redis configuration (for rate limiting and caching)
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis_ttl: int = 3600
    
    # Rate limiting
    rate_limit_sms: int = 100  # per hour
    rate_limit_email: int = 1000  # per hour
    rate_limit_webhook: int = 500  # per hour
    
    # Retry configuration
    max_retries: int = 3
    retry_delay: int = 5  # seconds
    
    # Template storage
    template_storage_path: str = os.getenv("TEMPLATE_STORAGE_PATH", "/app/templates")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
