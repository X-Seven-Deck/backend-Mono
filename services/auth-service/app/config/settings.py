"""
Configuration settings for the Auth Service.
"""

from pydantic import Field, ConfigDict
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

# Load environment variables from the project root .env file
project_root = os.path.join(os.path.dirname(__file__), "../../../../../")
env_file = os.path.join(project_root, ".env")

if os.path.exists(env_file):
    load_dotenv(env_file)
else:
    # Fallback to current directory
    load_dotenv()

class Settings(BaseSettings):
    """
    Application settings.
    """
    # Service settings
    SERVICE_NAME: str = "auth-service"
    VERSION: str = "0.1.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # Server settings
    HOST: str = Field(default="0.0.0.0", env="AUTH_SERVICE_HOST")
    PORT: int = Field(default=8010, env="AUTH_SERVICE_PORT")
    
    # Supabase settings
    SUPABASE_URL: str = Field(..., env="SUPABASE_URL")
    SUPABASE_ANON_KEY: str = Field(..., env="SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_ROLE_KEY: str = Field(..., env="SUPABASE_SERVICE_ROLE_KEY")
    
    # JWT settings
    JWT_SECRET: str = Field(..., env="JWT_SECRET")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY: int = Field(default=86400, env="JWT_EXPIRY")  # 24 hours in seconds
    
    # CORS settings
    CORS_ORIGINS: list = ["*"]
    
    model_config = ConfigDict(extra='ignore')

# Create settings instance
settings = Settings()
