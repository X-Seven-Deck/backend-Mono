"""
Chat Routes - Comprehensive API Endpoints

Enterprise-grade chat API supporting all session types.
"""

import logging
import time
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime

from app.models.chat_models import (
    CreateSessionRequest,
    SessionResponse,
    UpdateSessionRequest,
    SendMessageRequest,
    MessageResponse,
    ChatResponse,
    MessagesListResponse,
    SessionSummary,
    SuccessResponse,
    ErrorResponse
)

from app.services.database_service import db_service
from app.services.ai_service import ai_service
from app.services.cache_service import cache_service
from app.services.event_publisher import event_publisher

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

@router.post("/sessions", response_model=SessionResponse)
async def create_chat_session(request: CreateSessionRequest):
    """
    Create a new chat session.
    
    Supports three types of sessions:
    - **dedicated**: Business-specific chat (requires business_id)
    - **dashboard**: Business AI assistant (requires business_id)
    - **global**: Cross-business chat
    
    For QR code initiated chats, provide qr_code_id in metadata.
    """
    try:
        # Create session in database
        session = await db_service.create_chat_session(
            session_type=request.session_type.value,
            business_id=request.business_id,
            user_id=request.user_id,
            channel=request.channel.value,
            context=request.context,
            metadata=request.metadata
        )
        
        # Cache session
        await cache_service.cache_session(
            session["session_id"],
            session
        )
        
        # Publish event
        await event_publisher.publish_session_created(
            session_id=session["session_id"],
            session_type=request.session_type.value,
            business_id=request.business_id or "",
            user_id=request.user_id,
            channel=request.channel.value,
            metadata=request.metadata
        )
        
        logger.info(f"Created chat session: {session['session_id']}")
        
        return SessionResponse(**session)
        
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_chat_session(session_id: str):
    """
    Get chat session by ID.
    
    First checks cache, then falls back to database.
    """
    try:
        # Try cache first
        session = await cache_service.get_cached_session(session_id)
        
        if not session:
            # Fall back to database
            session = await db_service.get_chat_session(session_id)
            
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            
            # Cache for future requests
            await cache_service.cache_session(session_id, session)
        
        return SessionResponse(**session)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/sessions/{session_id}", response_model=SessionResponse)
async def update_chat_session(session_id: str, request: UpdateSessionRequest):
    """
    Update chat session.
    
    Can update status, context, metadata, assigned agent, etc.
    """
    try:
        # Prepare updates
        updates = {}
        if request.status:
            updates["status"] = request.status.value
        if request.context:
            updates["context"] = request.context
        if request.metadata:
            updates["metadata"] = request.metadata
        if request.assigned_agent_id:
            updates["assigned_agent_id"] = request.assigned_agent_id
        if request.intent:
            updates["intent"] = request.intent.value
        if request.sentiment:
            updates["sentiment"] = request.sentiment.value
        
        # Update in database
        session = await db_service.update_chat_session(session_id, updates)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Invalidate cache
        await cache_service.invalidate_session(session_id)
        
        logger.info(f"Updated session: {session_id}")
        
        return SessionResponse(**session)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/close", response_model=SuccessResponse)
async def close_chat_session(session_id: str, reason: Optional[str] = None):
    """
    Close chat session.
    
    Marks session as closed and triggers analytics.
    """
    try:
        success = await db_service.close_chat_session(session_id, reason)
        
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get session for analytics
        session = await db_service.get_chat_session(session_id)
        
        if session:
            # Calculate duration
            created_at = datetime.fromisoformat(session["created_at"])
            duration = (datetime.utcnow() - created_at).total_seconds()
            
            # Publish event
            await event_publisher.publish_session_closed(
                session_id=session_id,
                business_id=session.get("business_id", ""),
                duration_seconds=duration,
                message_count=session.get("message_count", 0)
            )
        
        # Invalidate cache
        await cache_service.invalidate_session(session_id)
        
        logger.info(f"Closed session: {session_id}")
        
        return SuccessResponse(
            success=True,
            message="Session closed successfully",
            data={"session_id": session_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error closing session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/summary", response_model=SessionSummary)
async def get_session_summary(session_id: str):
    """
    Get comprehensive session summary.
    
    Includes session info and recent messages.
    """
    try:
        # Get session
        session = await db_service.get_chat_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get recent messages
        messages = await db_service.get_session_messages(session_id, limit=10)
        
        return SessionSummary(
            session_id=session["session_id"],
            session_type=session["session_type"],
            status=session["status"],
            message_count=session.get("message_count", 0),
            created_at=session["created_at"],
            last_message_at=session.get("last_message_at"),
            intent=session.get("intent"),
            sentiment=session.get("sentiment"),
            recent_messages=[
                {
                    "role": msg["role"],
                    "content": msg["content"],
                    "created_at": msg["created_at"]
                }
                for msg in messages
            ]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MESSAGE HANDLING
# ============================================================================

@router.post("/messages", response_model=ChatResponse)
async def send_message(request: SendMessageRequest):
    """
    Send message in chat session.
    
    Handles:
    - User message storage
    - AI processing (intent, entities, sentiment)
    - AI response generation
    - Event publishing
    - Caching
    
    Returns both user message and AI response.
    """
    start_time = time.time()
    
    try:
        # Get session
        session = await db_service.get_chat_session(request.session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Store user message
        user_message = await db_service.add_message(
            session_id=request.session_id,
            role=request.role.value,
            content=request.content,
            sender_id=request.sender_id,
            sender_name=request.sender_name,
            message_type=request.message_type.value,
            metadata=request.metadata
        )
        
        # Cache message
        await cache_service.add_message_to_cache(
            request.session_id,
            user_message
        )
        
        # Publish event
        await event_publisher.publish_message_received(
            session_id=request.session_id,
            message_id=user_message["id"],
            business_id=session.get("business_id", ""),
            user_id=request.sender_id or "",
            channel=session.get("channel", "web")
        )
        
        # Process with AI if requested
        ai_response_msg = None
        ai_result = None
        
        if request.process_with_ai:
            # Get conversation history
            messages = await db_service.get_session_messages(
                request.session_id,
                limit=10
            )
            
            conversation_history = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in messages[:-1]  # Exclude current message
            ]
            
            # Process with AI
            ai_result = await ai_service.process_message_with_ai(
                message=request.content,
                business_id=session.get("business_id", ""),
                conversation_history=conversation_history,
                session_context=session.get("context", {})
            )
            
            # Store AI response
            if ai_result.get("response"):
                ai_response_msg = await db_service.add_message(
                    session_id=request.session_id,
                    role="assistant",
                    content=ai_result["response"],
                    message_type="text",
                    ai_generated=True,
                    ai_model=ai_result["ai_metadata"].get("model"),
                    intent=ai_result["intent"]["intent"],
                    entities=ai_result["entities"],
                    actions=ai_result["ai_metadata"].get("suggested_actions", []),
                    metadata=ai_result["ai_metadata"]
                )
                
                # Cache AI response
                await cache_service.add_message_to_cache(
                    request.session_id,
                    ai_response_msg
                )
                
                # Publish AI event
                await event_publisher.publish_ai_response_generated(
                    session_id=request.session_id,
                    message_id=ai_response_msg["id"],
                    business_id=session.get("business_id", ""),
                    model=ai_result["ai_metadata"].get("model", ""),
                    tokens_used=ai_result["ai_metadata"].get("tokens_used", 0),
                    processing_time=(time.time() - start_time),
                    intent=ai_result["intent"]["intent"]
                )
                
                # Update session with intent and sentiment
                await db_service.update_chat_session(
                    request.session_id,
                    {
                        "intent": ai_result["intent"]["intent"],
                        "sentiment": ai_result["sentiment"]["sentiment"]
                    }
                )
            
            # Publish analytics events
            if ai_result.get("intent"):
                await event_publisher.publish_intent_classified(
                    business_id=session.get("business_id", ""),
                    session_id=request.session_id,
                    intent=ai_result["intent"]["intent"],
                    confidence=ai_result["intent"]["confidence"]
                )
            
            if ai_result.get("sentiment"):
                await event_publisher.publish_sentiment_analyzed(
                    business_id=session.get("business_id", ""),
                    session_id=request.session_id,
                    sentiment=ai_result["sentiment"]["sentiment"],
                    score=ai_result["sentiment"]["score"]
                )
        
        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        
        return ChatResponse(
            user_message=MessageResponse(**user_message),
            ai_response=MessageResponse(**ai_response_msg) if ai_response_msg else None,
            processing_time_ms=processing_time,
            intent=ai_result["intent"]["intent"] if ai_result else None,
            entities=ai_result["entities"] if ai_result else {},
            sentiment=ai_result["sentiment"]["sentiment"] if ai_result else None,
            suggested_actions=ai_result["ai_metadata"].get("suggested_actions", []) if ai_result else []
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/messages", response_model=MessagesListResponse)
async def get_session_messages(
    session_id: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    include_deleted: bool = False
):
    """
    Get messages for a session.
    
    Supports pagination with limit/offset.
    By default, excludes deleted messages.
    """
    try:
        # Try cache first for recent messages
        if offset == 0 and limit <= 50:
            cached_messages = await cache_service.get_cached_messages(
                session_id,
                limit=limit
            )
            
            if cached_messages:
                return MessagesListResponse(
                    messages=[MessageResponse(**msg) for msg in cached_messages],
                    total=len(cached_messages),
                    session_id=session_id,
                    has_more=len(cached_messages) >= limit
                )
        
        # Get from database
        messages = await db_service.get_session_messages(
            session_id=session_id,
            limit=limit,
            offset=offset,
            include_deleted=include_deleted
        )
        
        return MessagesListResponse(
            messages=[MessageResponse(**msg) for msg in messages],
            total=len(messages),
            session_id=session_id,
            has_more=len(messages) >= limit
        )
        
    except Exception as e:
        logger.error(f"Error getting messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/messages/{message_id}", response_model=SuccessResponse)
async def delete_message(message_id: str, hard_delete: bool = False):
    """
    Delete message.
    
    - **soft delete** (default): Marks message as deleted
    - **hard delete**: Permanently removes message
    """
    try:
        success = await db_service.delete_message(message_id, hard_delete)
        
        if not success:
            raise HTTPException(status_code=404, detail="Message not found")
        
        logger.info(f"Deleted message: {message_id} (hard={hard_delete})")
        
        return SuccessResponse(
            success=True,
            message="Message deleted successfully",
            data={"message_id": message_id, "hard_delete": hard_delete}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# BUSINESS SESSIONS
# ============================================================================

@router.get("/business/{business_id}/sessions")
async def get_business_sessions(
    business_id: str,
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Get all sessions for a business.
    
    Can filter by status (active, closed, etc.)
    """
    try:
        if status == "active":
            sessions = await db_service.get_active_sessions_for_business(
                business_id,
                limit=limit
            )
        else:
            # Get all sessions (would need additional query implementation)
            sessions = await db_service.get_active_sessions_for_business(
                business_id,
                limit=limit
            )
        
        return {
            "business_id": business_id,
            "sessions": [SessionResponse(**session) for session in sessions],
            "total": len(sessions)
        }
        
    except Exception as e:
        logger.error(f"Error getting business sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# TYPING INDICATORS
# ============================================================================

@router.post("/sessions/{session_id}/typing")
async def set_typing_indicator(
    session_id: str,
    user_id: str,
    is_typing: bool = True
):
    """
    Set typing indicator for user in session.
    
    Indicators automatically expire after 10 seconds.
    """
    try:
        success = await cache_service.set_typing_indicator(
            session_id,
            user_id,
            is_typing
        )
        
        if success:
            # Publish event for real-time updates
            await event_publisher.publish_user_typing(
                session_id=session_id,
                user_id=user_id,
                business_id="",  # Would be fetched from session
                is_typing=is_typing
            )
        
        return {
            "success": True,
            "session_id": session_id,
            "user_id": user_id,
            "is_typing": is_typing
        }
        
    except Exception as e:
        logger.error(f"Error setting typing indicator: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/typing")
async def get_typing_users(session_id: str):
    """
    Get list of users currently typing in session.
    """
    try:
        typing_users = await cache_service.get_typing_users(session_id)
        
        return {
            "session_id": session_id,
            "typing_users": typing_users,
            "count": len(typing_users)
        }
        
    except Exception as e:
        logger.error(f"Error getting typing users: {e}")
        raise HTTPException(status_code=500, detail=str(e))

