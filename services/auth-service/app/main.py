"""
X-sevenAI Auth Service

This service handles user authentication, registration, and profile management.
It integrates with Supabase for authentication and database operations.
"""

import logging
import os
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from dotenv import load_dotenv

# Load environment variables from the project root .env file
project_root = os.path.join(os.path.dirname(__file__), "../../")
env_file = os.path.join(project_root, ".env")

if os.path.exists(env_file):
    load_dotenv(env_file)
else:
    # Fallback to current directory
    load_dotenv()

# Import routes
from app.routes.auth import router as auth
from app.routes.users import router as users
from app.routes.business import router as business

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.getLevelName(os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("auth-service")

# Create FastAPI app
app = FastAPI(
    title="X-sevenAI Auth Service",
    description="Authentication and user management service for X-sevenAI platform",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Error handling
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Include routers
app.include_router(auth, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users, prefix="/api/v1/users", tags=["users"])
app.include_router(business, prefix="/api/v1/business", tags=["business"])

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Auth Service starting up")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Auth Service shutting down")

if __name__ == "__main__":
    host = os.getenv("AUTH_SERVICE_HOST", "0.0.0.0")
    port = int(os.getenv("AUTH_SERVICE_PORT", 8010))
    uvicorn.run("app.main:app", host=host, port=port)
