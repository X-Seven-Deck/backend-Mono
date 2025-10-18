"""
AI Orchestration Service Configuration

Manages all configuration settings for the AI orchestration service including
LLM providers, Redis, Supabase, and service-specific parameters.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List
import os


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Service Configuration
    service_name: str = "ai-orchestration-service"
    service_host: str = "0.0.0.0"
    service_port: int = 8020
    environment: str = "development"
    log_level: str = "INFO"
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o"
    openai_temperature: float = 0.7
    openai_max_tokens: int = 2000
    
    # Groq Configuration
    groq_api_key: Optional[str] = None
    groq_model: str = "llama-3.1-70b-versatile"
    
    # Anthropic Configuration
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    
    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    redis_ttl: int = 3600  # 1 hour default
    
    # Supabase Configuration
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None
    supabase_service_key: Optional[str] = None
    
    # Pinecone Configuration (for vector search)
    pinecone_api_key: Optional[str] = None
    pinecone_environment: str = "gcp-starter"
    pinecone_index_name: str = "x7ai-knowledge"
    
    # Temporal Configuration
    temporal_host: str = "localhost"
    temporal_port: int = 7233
    temporal_namespace: str = "default"
    
    # LangGraph Configuration
    langgraph_max_iterations: int = 10
    langgraph_recursion_limit: int = 25
    
    # DSPy Configuration
    dspy_cache_enabled: bool = True
    dspy_optimization_metric: str = "accuracy"
    
    # Crew AI Configuration
    crewai_max_agents: int = 5
    crewai_verbose: bool = True
    
    # RAG Configuration
    rag_chunk_size: int = 1000
    rag_chunk_overlap: int = 200
    rag_top_k: int = 5
    rag_similarity_threshold: float = 0.7
    
    # Monitoring
    prometheus_enabled: bool = True
    prometheus_port: int = 9090
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds
    
    # CORS
    cors_origins: List[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]


# Global settings instance
settings = Settings()
