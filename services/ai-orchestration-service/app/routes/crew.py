"""
Crew AI multi-agent endpoints
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from app.services.crew_orchestrator import crew_orchestrator
from app.utils import logger

router = APIRouter()


class CustomerSupportRequest(BaseModel):
    """Customer support request"""
    customer_query: str = Field(..., description="Customer's question or issue")
    business_id: str = Field(..., description="Business identifier")
    business_name: str = Field(..., description="Business name")
    business_type: str = Field(..., description="Business type (restaurant, salon, retail, etc.)")
    additional_context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class BusinessOnboardingRequest(BaseModel):
    """Business onboarding request"""
    name: str = Field(..., description="Business name")
    business_type: str = Field(..., description="Business type")
    category: str = Field(..., description="Business category")
    location: str = Field(..., description="Business location")
    contact_info: Optional[Dict[str, str]] = Field(None, description="Contact information")
    additional_info: Optional[Dict[str, Any]] = Field(None, description="Additional information")


class OrderProcessingRequest(BaseModel):
    """Order processing request"""
    order_id: str = Field(..., description="Order identifier")
    items: list = Field(..., description="Order items")
    customer_id: str = Field(..., description="Customer identifier")
    business_id: str = Field(..., description="Business identifier")
    total_amount: float = Field(..., description="Total order amount")
    special_instructions: Optional[str] = Field(None, description="Special instructions")


class AnalyticsInsightsRequest(BaseModel):
    """Analytics insights request"""
    business_id: str = Field(..., description="Business identifier")
    metrics: Dict[str, Any] = Field(..., description="Analytics metrics")
    period: str = Field("last_30_days", description="Time period for analysis")
    include_recommendations: bool = Field(True, description="Include marketing recommendations")


@router.post("/customer-support")
async def execute_customer_support(request: CustomerSupportRequest):
    """
    Execute customer support multi-agent workflow
    
    Uses specialized agents to analyze and resolve customer queries
    """
    try:
        logger.info(f"Customer support crew request for business: {request.business_id}")
        
        business_context = {
            "business_id": request.business_id,
            "business_name": request.business_name,
            "business_type": request.business_type,
            **(request.additional_context or {})
        }
        
        result = await crew_orchestrator.execute_customer_support(
            customer_query=request.customer_query,
            business_context=business_context
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Customer support crew error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/business-onboarding")
async def execute_business_onboarding(request: BusinessOnboardingRequest):
    """
    Execute business onboarding multi-agent workflow
    
    Creates comprehensive onboarding plan with marketing and analytics setup
    """
    try:
        logger.info(f"Business onboarding crew request for: {request.name}")
        
        business_info = {
            "name": request.name,
            "business_type": request.business_type,
            "category": request.category,
            "location": request.location,
            "contact_info": request.contact_info or {},
            **(request.additional_info or {})
        }
        
        result = await crew_orchestrator.execute_business_onboarding(
            business_info=business_info
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Business onboarding crew error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/order-processing")
async def execute_order_processing(request: OrderProcessingRequest):
    """
    Execute order processing multi-agent workflow
    
    Processes orders with validation, customer communication, and quality checks
    """
    try:
        logger.info(f"Order processing crew request for order: {request.order_id}")
        
        order_data = {
            "order_id": request.order_id,
            "items": request.items,
            "customer_id": request.customer_id,
            "business_id": request.business_id,
            "total_amount": request.total_amount,
            "special_instructions": request.special_instructions
        }
        
        result = await crew_orchestrator.execute_order_processing(
            order_data=order_data
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Order processing crew error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analytics-insights")
async def execute_analytics_insights(request: AnalyticsInsightsRequest):
    """
    Execute analytics insights multi-agent workflow
    
    Analyzes business data and provides strategic insights with recommendations
    """
    try:
        logger.info(f"Analytics insights crew request for business: {request.business_id}")
        
        analytics_data = {
            "metrics": request.metrics,
            "period": request.period,
            "include_recommendations": request.include_recommendations
        }
        
        result = await crew_orchestrator.execute_analytics_insights(
            business_id=request.business_id,
            analytics_data=analytics_data
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Analytics insights crew error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents")
async def list_agents():
    """
    List available AI agents
    
    Returns information about all specialized agents
    """
    return {
        "agents": [
            {
                "name": "business_analyst",
                "role": "Business Analyst",
                "capabilities": ["business analysis", "strategic planning", "requirements gathering"]
            },
            {
                "name": "customer_service",
                "role": "Customer Service Specialist",
                "capabilities": ["customer support", "query resolution", "complaint handling"]
            },
            {
                "name": "order_manager",
                "role": "Order Management Specialist",
                "capabilities": ["order processing", "inventory management", "fulfillment"]
            },
            {
                "name": "reservation_coordinator",
                "role": "Reservation Coordinator",
                "capabilities": ["booking management", "scheduling", "capacity optimization"]
            },
            {
                "name": "marketing_strategist",
                "role": "Marketing Strategist",
                "capabilities": ["campaign planning", "customer acquisition", "engagement strategies"]
            },
            {
                "name": "data_analyst",
                "role": "Data Analyst",
                "capabilities": ["data analysis", "insights generation", "KPI tracking"]
            },
            {
                "name": "qa_specialist",
                "role": "Quality Assurance Specialist",
                "capabilities": ["quality control", "customer satisfaction", "process improvement"]
            }
        ],
        "workflows": [
            "customer_support",
            "business_onboarding",
            "order_processing",
            "analytics_insights"
        ]
    }
