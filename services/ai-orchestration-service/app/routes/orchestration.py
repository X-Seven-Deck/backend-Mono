"""
Orchestration endpoints for LangGraph workflows
"""

from fastapi import APIRouter, HTTPException
from app.models.schemas import WorkflowExecutionRequest, WorkflowExecutionResponse, Message
from app.services.langgraph_orchestrator import langgraph_orchestrator
from app.utils import logger

router = APIRouter()


@router.post("/execute", response_model=WorkflowExecutionResponse)
async def execute_workflow(request: WorkflowExecutionRequest):
    """
    Execute a LangGraph workflow
    
    Supports multiple workflow types:
    - business_onboarding: Onboard new businesses
    - customer_support: Handle customer queries
    - order_processing: Process orders
    """
    try:
        logger.info(f"Executing workflow: {request.workflow_name} for session: {request.session_id}")
        
        result = await langgraph_orchestrator.execute_workflow(
            workflow_name=request.workflow_name.value,
            initial_message=request.message,
            session_id=request.session_id,
            user_id=request.user_id,
            business_id=request.business_id
        )
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result.get("error", "Workflow execution failed"))
        
        # Convert messages to Message objects
        messages = [Message(**msg) for msg in result["messages"]]
        
        return WorkflowExecutionResponse(
            status=result["status"],
            messages=messages,
            context=result["context"],
            current_step=result["current_step"],
            session_id=request.session_id
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Workflow execution error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}")
async def get_session_state(session_id: str):
    """
    Retrieve current state of a workflow session
    """
    try:
        state = await langgraph_orchestrator.load_state_from_redis(session_id)
        
        if not state:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "session_id": session_id,
            "messages": state["messages"],
            "context": state["context"],
            "current_step": state["current_step"],
            "metadata": state.get("metadata", {})
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows")
async def list_workflows():
    """
    List available workflows
    """
    return {
        "workflows": [
            {
                "name": "business_onboarding",
                "description": "Onboard new businesses to the platform",
                "steps": ["welcome", "collect_info", "validate", "setup", "complete"]
            },
            {
                "name": "customer_support",
                "description": "Handle customer support queries",
                "steps": ["analyze", "retrieve", "generate", "validate"]
            },
            {
                "name": "order_processing",
                "description": "Process customer orders",
                "steps": ["parse", "check_inventory", "calculate", "confirm"]
            }
        ]
    }
