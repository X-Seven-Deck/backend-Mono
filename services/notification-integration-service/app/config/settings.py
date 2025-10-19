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
    
    # Database configuration (Supabase PostgreSQL)
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/x7ai"
    )
    database_pool_size: int = 10
    database_max_overflow: int = 20
    
    # Twilio configuration
    twilio_account_sid: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    twilio_auth_token: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    twilio_phone_number: str = os.getenv("TWILIO_PHONE_NUMBER", "")
    twilio_whatsapp_number: str = os.getenv("TWILIO_WHATSAPP_NUMBER", "")
    twilio_verify_service_sid: str = os.getenv("TWILIO_VERIFY_SERVICE_SID", "")
    
    # SendGrid configuration
    sendgrid_api_key: str = os.getenv("SENDGRID_API_KEY", "")
    sendgrid_from_email: str = os.getenv("SENDGRID_FROM_EMAIL", "noreply@x7ai.com")
    sendgrid_from_name: str = os.getenv("SENDGRID_FROM_NAME", "X-sevenAI")
    
    # Firebase configuration (for push notifications)
    firebase_credentials_path: str = os.getenv(
        "FIREBASE_CREDENTIALS_PATH",
        "/app/config/firebase-credentials.json"
    )
    
    # Zapier configuration
    zapier_webhook_url: str = os.getenv("ZAPIER_WEBHOOK_URL", "")
    zapier_api_key: str = os.getenv("ZAPIER_API_KEY", "")
    
    # Kafka configuration
    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    kafka_notification_topic: str = "notifications"
    kafka_consumer_group: str = "notification-service-group"
    kafka_enable: bool = os.getenv("KAFKA_ENABLE", "true").lower() == "true"
    
    # Redis configuration (for rate limiting and caching)
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis_ttl: int = 3600
    redis_db: int = 0
    
    # Celery configuration (for scheduling)
    celery_broker_url: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    celery_result_backend: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
    
    # Rate limiting
    rate_limit_sms: int = 100  # per hour
    rate_limit_email: int = 1000  # per hour
    rate_limit_push: int = 5000  # per hour
    rate_limit_webhook: int = 500  # per hour
    rate_limit_global: str = "1000/hour"  # Global rate limit
    
    # Retry configuration
    max_retries: int = 3
    retry_delay: int = 5  # seconds
    retry_backoff_multiplier: int = 2
    
    # Template storage
    template_storage_path: str = os.getenv("TEMPLATE_STORAGE_PATH", "/app/templates")
    
    # Monitoring and observability
    sentry_dsn: str = os.getenv("SENTRY_DSN", "")
    enable_metrics: bool = True
    enable_tracing: bool = True
    
    # Security
    webhook_signature_secret: str = os.getenv("WEBHOOK_SIGNATURE_SECRET", "")
    api_key_header: str = "X-API-Key"
    
    # Feature flags
    enable_sms: bool = True
    enable_email: bool = True
    enable_push: bool = True
    enable_whatsapp: bool = True
    enable_webhook: bool = True
    enable_scheduler: bool = True
    enable_analytics: bool = True
    
    # Business logic
    max_batch_size: int = 500
    notification_ttl_days: int = 90  # Keep logs for 90 days
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
