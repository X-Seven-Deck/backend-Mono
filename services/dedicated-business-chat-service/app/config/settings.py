"""
Configuration settings for Dedicated Business Chat Service
"""

import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""
    
    # Service Configuration
    service_name: str = "dedicated-business-chat-service"
    service_port: int = int(os.getenv("DEDICATED_CHAT_PORT", 8050))
    environment: str = os.getenv("ENVIRONMENT", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Supabase Configuration
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_key: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    supabase_jwt_secret: str = os.getenv("SUPABASE_JWT_SECRET", "")
    
    # OpenAI Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    openai_embedding_model: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    
    # Redis Configuration
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", 6379))
    redis_db: int = int(os.getenv("REDIS_DB", 0))
    redis_password: str = os.getenv("REDIS_PASSWORD", "")
    
    # Cache Configuration
    cache_ttl: int = int(os.getenv("CACHE_TTL", 3600))  # 1 hour
    session_cache_ttl: int = int(os.getenv("SESSION_CACHE_TTL", 7200))  # 2 hours
    
    # AI Configuration
    max_context_messages: int = int(os.getenv("MAX_CONTEXT_MESSAGES", 20))
    temperature: float = float(os.getenv("AI_TEMPERATURE", 0.7))
    max_tokens: int = int(os.getenv("MAX_TOKENS", 1000))
    
    # RAG Configuration
    rag_enabled: bool = os.getenv("RAG_ENABLED", "true").lower() == "true"
    rag_top_k: int = int(os.getenv("RAG_TOP_K", 5))
    rag_similarity_threshold: float = float(os.getenv("RAG_SIMILARITY_THRESHOLD", 0.7))
    
    # CORS Configuration
    cors_origins: List[str] = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:8000"
    ).split(",")
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]
    
    # Monitoring
    enable_metrics: bool = os.getenv("ENABLE_METRICS", "true").lower() == "true"
    sentry_dsn: str = os.getenv("SENTRY_DSN", "")
    
    # Rate Limiting
    rate_limit_enabled: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", 60))
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


settings = Settings()
