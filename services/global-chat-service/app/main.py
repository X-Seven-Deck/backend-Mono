"""
X-sevenAI Global Chat Service

Universal AI-powered chatbot for cross-business interactions.
Uses Crew AI agents for multi-agent collaboration and DSPy for prompts.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram
import uvicorn
from datetime import datetime
from typing import Optional
import os

from app.config import settings
from app.utils import logger, setup_logger
from app.services.crew_agents import crew_service
from app.services.database_service import global_db_service

# Configure logging
setup_logger("global-chat-service", settings.log_level)

# Configuration
SERVICE_NAME = settings.service_name
SERVICE_PORT = settings.service_port
LOG_LEVEL = settings.log_level

# Prometheus metrics
REQUEST_COUNT = Counter(
    'global_chat_requests_total',
    'Total requests',
    ['method', 'endpoint', 'status']
)
CHAT_QUERIES = Counter(
    'global_chat_queries_total',
    'Total chat queries',
    ['query_type']
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management"""
    logger.info(f"Starting {SERVICE_NAME}")
    
    # Initialize database service
    try:
        await global_db_service.initialize()
        logger.info("✓ Database service initialized")
    except Exception as e:
        logger.error(f"✗ Failed to initialize database: {e}")
    
    # Initialize Crew AI agents
    try:
        await crew_service.initialize()
        logger.info("✓ Crew AI agents initialized successfully")
    except Exception as e:
        logger.error(f"✗ Failed to initialize Crew AI: {e}")
    
    yield
    
    logger.info(f"Shutting down {SERVICE_NAME}")


# Create FastAPI app
app = FastAPI(
    title="X-sevenAI Global Chat Service",
    description="Universal AI chatbot for cross-business interactions with Crew AI agents",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)


# Health endpoints
@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health/live")
async def liveness():
    """Liveness probe"""
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness():
    """Readiness probe"""
    return {"status": "ready"}


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": SERVICE_NAME,
        "version": "0.1.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }


# Global chat endpoints
@app.post("/api/v1/chat/query")
async def process_query(
    query: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    context: Optional[dict] = None
):
    """
    Process global chat query
    
    Uses Crew AI agents to:
    - Search across all businesses
    - Find availability
    - Process orders/reservations
    - Answer general queries
    """
    try:
        CHAT_QUERIES.labels(query_type="general").inc()
        
        # Generate session ID if not provided
        if not session_id:
            session_id = f"session_{int(datetime.utcnow().timestamp())}"
        
        if not user_id:
            user_id = f"user_{int(datetime.utcnow().timestamp())}"
        
        # Process query using Crew AI agents
        result = await crew_service.process_query(
            query=query,
            user_id=user_id,
            session_id=session_id,
            context=context
        )
        
        return {
            "status": "success",
            "response": result["response"],
            "session_id": session_id,
            "intent": result.get("intent"),
            "agents_used": result.get("agents_used", []),
            "suggestions": [
                "View available restaurants",
                "Make a reservation",
                "Browse menus"
            ],
            "timestamp": result["timestamp"]
        }
    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/chat/search-businesses")
async def search_businesses(
    query: str,
    category: Optional[str] = None,
    location: Optional[str] = None,
    limit: int = 10
):
    """
    Search for businesses across platform
    
    Uses semantic search and filters with database integration
    """
    try:
        CHAT_QUERIES.labels(query_type="search").inc()
        
        # Search businesses from database
        businesses = await global_db_service.search_businesses(
            query=query,
            category=category,
            location=location,
            limit=limit
        )
        
        return {
            "status": "success",
            "businesses": businesses,
            "count": len(businesses),
            "query": query,
            "filters": {
                "category": category,
                "location": location
            }
        }
    except Exception as e:
        logger.error(f"Error searching businesses: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/chat/check-availability")
async def check_availability(
    business_id: str,
    date: str,
    time: str,
    party_size: int
):
    """
    Check availability for reservation
    
    Queries business database for open slots
    """
    try:
        CHAT_QUERIES.labels(query_type="availability").inc()
        
        from uuid import UUID
        
        # Check availability from database
        availability = await global_db_service.check_availability(
            business_id=UUID(business_id),
            date=date,
            time=time,
            party_size=party_size
        )
        
        return {
            "status": "success",
            "business_id": business_id,
            "available": availability["available"],
            "availability_info": availability,
            "message": availability["message"]
        }
    except Exception as e:
        logger.error(f"Error checking availability: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/chat/create-order")
async def create_order(
    business_id: str,
    items: list,
    user_id: Optional[str] = None,
    delivery_address: Optional[str] = None
):
    """
    Create order through global chat
    
    Generates order ID and initiates processing
    """
    try:
        CHAT_QUERIES.labels(query_type="order").inc()
        
        from uuid import UUID
        
        # Calculate total (simplified)
        total = sum(item.get("price", 0) * item.get("quantity", 1) for item in items)
        
        # Create order in database
        order = await global_db_service.create_order(
            business_id=UUID(business_id),
            customer_id=UUID(user_id) if user_id else None,
            items=items,
            total_amount=total,
            metadata={"delivery_address": delivery_address}
        )
        
        return {
            "status": "success",
            "order_id": order["id"],
            "order_number": order["order_number"],
            "business_id": business_id,
            "items": items,
            "total": total,
            "estimated_time": "30-45 minutes",
            "message": "Order created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating order: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/chat/create-reservation")
async def create_reservation(
    business_id: str,
    date: str,
    time: str,
    party_size: int,
    customer_name: str,
    customer_phone: str,
    user_id: Optional[str] = None,
    special_requests: Optional[str] = None
):
    """
    Create reservation through global chat
    
    Generates reservation ID and confirms booking
    """
    try:
        CHAT_QUERIES.labels(query_type="reservation").inc()
        
        from uuid import UUID
        
        # Create reservation in database
        reservation = await global_db_service.create_reservation(
            business_id=UUID(business_id),
            customer_id=UUID(user_id) if user_id else None,
            date=date,
            time=time,
            party_size=party_size,
            customer_name=customer_name,
            customer_phone=customer_phone,
            special_requests=special_requests
        )
        
        return {
            "status": "success",
            "reservation_id": reservation["id"],
            "reservation_number": reservation["reservation_number"],
            "business_id": business_id,
            "date": date,
            "time": time,
            "party_size": party_size,
            "confirmation_code": reservation["reservation_number"],
            "message": "Reservation confirmed"
        }
    except Exception as e:
        logger.error(f"Error creating reservation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/chat/recommendations")
async def get_recommendations(
    user_id: Optional[str] = None,
    category: Optional[str] = None,
    location: Optional[str] = None,
    limit: int = 5
):
    """
    Get personalized business recommendations
    
    Uses AI to suggest businesses based on preferences and history
    """
    try:
        from uuid import UUID
        
        # Get recommendations from database
        recommendations = await global_db_service.get_business_recommendations(
            user_id=UUID(user_id) if user_id else None,
            category=category,
            limit=limit
        )
        
        return {
            "status": "success",
            "recommendations": recommendations,
            "count": len(recommendations),
            "personalized": user_id is not None
        }
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/chat/session/create")
async def create_session(
    user_id: Optional[str] = None,
    channel: str = "web",
    context: Optional[dict] = None
):
    """
    Create a new global chat session
    
    Returns session details
    """
    try:
        from uuid import UUID
        
        session = await global_db_service.create_global_session(
            user_id=UUID(user_id) if user_id else None,
            channel=channel,
            context=context
        )
        
        return {
            "status": "success",
            "session": session
        }
    except Exception as e:
        logger.error(f"Error creating session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=SERVICE_PORT,
        reload=True,
        log_level=LOG_LEVEL.lower()
    )
