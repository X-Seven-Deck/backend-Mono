"""
Temporal Workflow API Routes

Endpoints for durable AI workflows with Temporal orchestration
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime

from app.services.temporal_orchestrator import (
    temporal_orchestrator,
    BusinessOnboardingInput,
    CustomerEngagementInput,
    OrderIntelligenceInput
)
from app.utils import logger

router = APIRouter()


# Request Models
class BusinessOnboardingRequest(BaseModel):
    """Business onboarding workflow request"""
    business_name: str
    business_type: str
    category: str
    location: str
    contact_info: Dict[str, str]
    owner_id: str


class CustomerEngagementRequest(BaseModel):
    """Customer engagement workflow request"""
    customer_id: str
    business_id: str
    channel: str
    message: str
    context: Dict[str, Any] = Field(default={})


class OrderIntelligenceRequest(BaseModel):
    """AI order processing workflow request"""
    order_id: str
    customer_id: str
    business_id: str
    raw_order_text: str
    channel: str


class WorkflowStatusRequest(BaseModel):
    """Workflow status query request"""
    workflow_id: str


# ==================== WORKFLOW ENDPOINTS ====================

@router.post("/business-onboarding")
async def start_business_onboarding(request: BusinessOnboardingRequest):
    """
    Start AI-powered business onboarding workflow
    
    Complete onboarding process with LangGraph conversation,
    Crew AI strategic analysis, and knowledge base setup.
    """
    try:
        logger.info(f"Starting business onboarding: {request.business_name}")
        
        input_data = BusinessOnboardingInput(
            business_name=request.business_name,
            business_type=request.business_type,
            category=request.category,
            location=request.location,
            contact_info=request.contact_info,
            owner_id=request.owner_id
        )
        
        workflow_id = await temporal_orchestrator.execute_business_onboarding(input_data)
        
        return {
            "status": "started",
            "workflow_id": workflow_id,
            "workflow_type": "business_onboarding",
            "business_name": request.business_name,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Business onboarding workflow error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/customer-engagement")
async def start_customer_engagement(request: CustomerEngagementRequest):
    """
    Start multi-channel customer engagement workflow
    
    Handles customer interactions with sentiment analysis,
    RAG context retrieval, and AI response generation.
    """
    try:
        logger.info(f"Starting customer engagement: {request.customer_id}")
        
        input_data = CustomerEngagementInput(
            customer_id=request.customer_id,
            business_id=request.business_id,
            channel=request.channel,
            message=request.message,
            context=request.context
        )
        
        workflow_id = await temporal_orchestrator.execute_customer_engagement(input_data)
        
        return {
            "status": "started",
            "workflow_id": workflow_id,
            "workflow_type": "customer_engagement",
            "customer_id": request.customer_id,
            "channel": request.channel,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Customer engagement workflow error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/order-intelligence")
async def start_order_intelligence(request: OrderIntelligenceRequest):
    """
    Start AI-powered order processing workflow
    
    Extracts structured order from natural language,
    validates with Crew AI, and processes automatically.
    """
    try:
        logger.info(f"Starting order intelligence: {request.order_id}")
        
        input_data = OrderIntelligenceInput(
            order_id=request.order_id,
            customer_id=request.customer_id,
            business_id=request.business_id,
            raw_order_text=request.raw_order_text,
            channel=request.channel
        )
        
        workflow_id = await temporal_orchestrator.execute_order_intelligence(input_data)
        
        return {
            "status": "started",
            "workflow_id": workflow_id,
            "workflow_type": "order_intelligence",
            "order_id": request.order_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Order intelligence workflow error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{workflow_id}")
async def get_workflow_status(workflow_id: str):
    """
    Get workflow execution status and result
    
    Returns current status, result (if complete), and execution metadata.
    """
    try:
        logger.info(f"Fetching workflow status: {workflow_id}")
        
        result = await temporal_orchestrator.get_workflow_result(workflow_id)
        
        return {
            "workflow_id": workflow_id,
            "status": "completed",
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Workflow status error: {e}", exc_info=True)
        # Workflow might still be running
        return {
            "workflow_id": workflow_id,
            "status": "running",
            "message": "Workflow is still executing",
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/workflows/list")
async def list_workflows():
    """
    List all available Temporal workflows
    
    Returns catalog of durable AI workflows.
    """
    return {
        "workflows": [
            {
                "name": "business_onboarding",
                "endpoint": "/api/v1/temporal/business-onboarding",
                "description": "Complete AI-powered business onboarding with conversation, analysis, and setup",
                "features": [
                    "LangGraph conversational onboarding",
                    "Crew AI strategic planning",
                    "Knowledge base initialization",
                    "AI feature configuration"
                ],
                "duration": "5-15 minutes",
                "fault_tolerant": True
            },
            {
                "name": "customer_engagement",
                "endpoint": "/api/v1/temporal/customer-engagement",
                "description": "Multi-channel customer interaction with AI assistance",
                "features": [
                    "Sentiment analysis",
                    "RAG context retrieval",
                    "AI response generation",
                    "Multi-channel support"
                ],
                "duration": "30 seconds - 2 minutes",
                "fault_tolerant": True
            },
            {
                "name": "order_intelligence",
                "endpoint": "/api/v1/temporal/order-intelligence",
                "description": "AI-powered order extraction and processing from natural language",
                "features": [
                    "Natural language order parsing",
                    "Menu matching via RAG",
                    "Crew AI validation",
                    "Automatic processing"
                ],
                "duration": "1-3 minutes",
                "fault_tolerant": True
            }
        ],
        "total_workflows": 3,
        "status_endpoint": "/api/v1/temporal/status/{workflow_id}",
        "timestamp": datetime.utcnow().isoformat()
    }
