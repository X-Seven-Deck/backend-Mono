"""
Chat routes for Dedicated Business Chat Service
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.responses import JSONResponse

from app.models.schemas import (
    ChatSessionCreate,
    ChatSessionResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    ChatHistoryResponse,
    BusinessContextResponse,
    HandoverRequest,
    FeedbackRequest,
    ChatSuggestions
)
from app.services.database import db_service
from app.services.ai_service import ai_service
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["Dedicated Business Chat"])


async def verify_business_access(
    business_id: UUID,
    authorization: Optional[str] = Header(None)
) -> bool:
    """Verify user has access to business"""
    # TODO: Implement proper JWT verification
    # For now, allow all requests
    return True


@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    request: ChatSessionCreate,
    authorized: bool = Depends(verify_business_access)
):
    """
    Create a new dedicated chat session for a business
    
    This creates a business-specific chat session with full context awareness.
    """
    try:
        # Create session in database
        session = await db_service.create_session(
            business_id=request.business_id,
            user_id=request.user_id,
            channel=request.channel,
            context=request.context
        )
        
        # Cache session
        await cache_service.cache_session(session["session_id"], session)
        
        # If initial message provided, process it
        if request.initial_message:
            await process_message_internal(
                session["session_id"],
                request.initial_message,
                request.business_id,
                request.user_id
            )
        
        logger.info(f"Created chat session: {session['session_id']}")
        
        return session
        
    except Exception as e:
        logger.error(f"Error creating chat session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(session_id: str):
    """Get chat session details"""
    try:
        # Try cache first
        session = await cache_service.get_cached_session(session_id)
        
        if not session:
            # Get from database
            session = await db_service.get_session(session_id)
            
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            
            # Cache it
            await cache_service.cache_session(session_id, session)
        
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/messages", response_model=ChatMessageResponse)
async def send_message(
    session_id: str,
    request: ChatMessageRequest
):
    """
    Send a message in a chat session
    
    This processes the user message and generates an AI response with business context.
    """
    try:
        # Get session
        session = await db_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session["status"] != "active":
            raise HTTPException(status_code=400, detail="Session is not active")
        
        # Rate limiting
        rate_limited = await cache_service.set_rate_limit(
            f"session:{session_id}",
            limit=30,
            window=60
        )
        
        if not rate_limited:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        # Process message
        response = await process_message_internal(
            session_id,
            request.content,
            UUID(session["business_id"]),
            UUID(session["user_id"]) if session.get("user_id") else None,
            request.metadata
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_message_internal(
    session_id: str,
    content: str,
    business_id: UUID,
    user_id: Optional[UUID] = None,
    metadata: Optional[dict] = None
) -> dict:
    """Internal function to process a message"""
    
    # Save user message
    user_message = await db_service.create_message(
        session_id=session_id,
        role="user",
        content=content,
        sender_id=user_id,
        metadata=metadata
    )
    
    # Generate AI response
    response_text, ai_metadata = await ai_service.generate_response(
        session_id=session_id,
        user_message=content,
        business_id=business_id,
        user_id=user_id
    )
    
    # Save AI response
    ai_message = await db_service.create_message(
        session_id=session_id,
        role="assistant",
        content=response_text,
        ai_generated=True,
        ai_model=ai_metadata.get("model"),
        intent=ai_metadata.get("intent"),
        entities=ai_metadata.get("entities"),
        actions=ai_metadata.get("actions"),
        processing_time=ai_metadata.get("processing_time"),
        metadata=ai_metadata
    )
    
    # Update session with latest intent and sentiment
    await db_service.update_session(
        session_id,
        {
            "intent": ai_metadata.get("intent"),
            "sentiment": ai_metadata.get("sentiment")
        }
    )
    
    # Cache the message
    await cache_service.append_message(session_id, ai_message)
    
    return ai_message


@router.get("/sessions/{session_id}/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    session_id: str,
    limit: int = 50,
    offset: int = 0
):
    """Get chat history for a session"""
    try:
        # Try cache first
        messages = await cache_service.get_cached_messages(session_id)
        
        if not messages:
            # Get from database
            messages = await db_service.get_session_messages(
                session_id,
                limit=limit,
                offset=offset
            )
            
            # Cache it
            if messages:
                await cache_service.cache_messages(session_id, messages)
        
        # Get session
        session = await db_service.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "session": session,
            "messages": messages,
            "total_messages": session.get("message_count", 0),
            "has_more": len(messages) >= limit
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/close")
async def close_chat_session(session_id: str):
    """Close a chat session"""
    try:
        success = await db_service.close_session(session_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Invalidate cache
        await cache_service.invalidate_session(session_id)
        
        return {"status": "success", "message": "Session closed"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error closing session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/business/{business_id}/context", response_model=BusinessContextResponse)
async def get_business_context(business_id: UUID):
    """Get business context information"""
    try:
        # Try cache first
        context = await cache_service.get_cached_business_context(str(business_id))
        
        if not context:
            # Get from database
            context = await db_service.get_business_context(business_id)
            
            if not context:
                raise HTTPException(status_code=404, detail="Business not found")
            
            # Cache it
            await cache_service.cache_business_context(str(business_id), context)
        
        business = context.get("business", {})
        category = business.get("business_categories", {})
        
        return {
            "business_id": business_id,
            "business_name": business.get("name", ""),
            "business_type": business.get("business_id", ""),
            "category": category.get("name", "") if category else "",
            "features": [],  # TODO: Implement feature detection
            "knowledge_base_count": context.get("knowledge_base_count", 0),
            "active_templates": context.get("template_count", 0)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting business context: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/business/{business_id}/sessions")
async def get_business_sessions(
    business_id: UUID,
    status: Optional[str] = None,
    limit: int = 50
):
    """Get all chat sessions for a business"""
    try:
        sessions = await db_service.get_business_sessions(
            business_id,
            status=status,
            limit=limit
        )
        
        return {
            "business_id": business_id,
            "sessions": sessions,
            "count": len(sessions)
        }
        
    except Exception as e:
        logger.error(f"Error getting business sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/handover")
async def handover_to_agent(
    session_id: str,
    request: HandoverRequest
):
    """Handover chat session to human agent"""
    try:
        updates = {
            "status": "transferred",
            "assigned_agent_id": str(request.agent_id) if request.agent_id else None,
            "handover_reason": request.reason
        }
        
        result = await db_service.update_session(session_id, updates)
        
        if not result:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Create system message about handover
        await db_service.create_message(
            session_id=session_id,
            role="system",
            content=f"Chat transferred to human agent. Reason: {request.reason}",
            metadata={"handover": True, "notes": request.notes}
        )
        
        return {"status": "success", "message": "Session transferred to agent"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling handover: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/messages/{message_id}/feedback")
async def submit_message_feedback(
    message_id: UUID,
    request: FeedbackRequest
):
    """Submit feedback for a message"""
    try:
        success = await db_service.update_message_feedback(
            message_id,
            request.rating,
            request.comment
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Message not found")
        
        return {"status": "success", "message": "Feedback submitted"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/suggestions", response_model=ChatSuggestions)
async def get_chat_suggestions(session_id: str):
    """Get contextual suggestions for the chat"""
    try:
        session = await db_service.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        business_id = UUID(session["business_id"])
        
        suggestions = await ai_service.generate_suggestions(session_id, business_id)
        
        return {
            "quick_replies": [
                {"text": suggestion, "action": None, "metadata": None}
                for suggestion in suggestions
            ],
            "suggested_actions": [],
            "context_hints": []
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
