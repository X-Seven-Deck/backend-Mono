"""
Audio Call Routes - Enterprise-grade audio calling API
"""

import logging
from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field

from app.services.audio_call_service import audio_call_service, CallType, CallStatus
from app.services.webrtc_service import webrtc_service
from app.services.push_notification_service import push_notification_service
from app.services.voice_activity_service import voice_activity_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/audio-calls", tags=["Audio Calls"])


class InitiateCallRequest(BaseModel):
    """Request to initiate an audio call"""
    business_id: UUID
    callee_id: Optional[UUID] = None
    call_type: str = Field(default="business_support", description="Type of call")
    caller_name: Optional[str] = None


class UpdateCallStatusRequest(BaseModel):
    """Request to update call status"""
    status: str
    disconnect_reason: Optional[str] = None


class CallQualityRequest(BaseModel):
    """Request to set call quality"""
    quality_score: float = Field(ge=0, le=5, description="Quality score 0-5")


@router.post("/initiate")
async def initiate_audio_call(
    request: InitiateCallRequest,
    caller_id: Optional[str] = Header(None, alias="X-User-ID")
):
    """
    Initiate an audio call
    
    Creates LiveKit room, call session, and sends push notification
    """
    try:
        # Create LiveKit room for audio
        room_name = f"audio_call_{request.business_id}_{datetime.utcnow().timestamp()}"
        
        room = await webrtc_service.create_room(
            room_name=room_name,
            max_participants=2,
            metadata={"type": "audio_call", "business_id": str(request.business_id)}
        )
        
        # Create call session
        call_session = await audio_call_service.create_call_session(
            business_id=request.business_id,
            caller_id=UUID(caller_id) if caller_id else None,
            callee_id=request.callee_id,
            call_type=CallType(request.call_type),
            room_id=room["room_name"],
            direction="outbound"
        )
        
        # Generate tokens for both parties
        caller_token = await webrtc_service.generate_token(
            room_name=room["room_name"],
            participant_name=request.caller_name or "Caller",
            participant_identity=caller_id
        )
        
        # Send push notification to callee if specified
        if request.callee_id:
            await push_notification_service.send_call_notification(
                user_id=request.callee_id,
                call_data={
                    "call_id": call_session["call_id"],
                    "room_id": room["room_name"],
                    "caller_id": caller_id,
                    "caller_name": request.caller_name or "Someone",
                    "business_id": str(request.business_id)
                }
            )
            
            # Update status to ringing
            await audio_call_service.update_call_status(
                call_session["call_id"],
                CallStatus.RINGING
            )
        
        # Start voice activity session
        await voice_activity_service.start_voice_session(
            session_id=call_session["call_id"],
            config={"language": "en"}
        )
        
        logger.info(f"Initiated audio call: {call_session['call_id']}")
        
        return {
            "status": "success",
            "call_id": call_session["call_id"],
            "room_id": room["room_name"],
            "caller_token": caller_token,
            "livekit_url": webrtc_service._initialized and room.get("livekit_url") or None,
            "call_session": call_session
        }
        
    except Exception as e:
        logger.error(f"Error initiating call: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/join/{call_id}")
async def join_audio_call(
    call_id: str,
    participant_name: str,
    user_id: Optional[str] = Header(None, alias="X-User-ID")
):
    """
    Join an existing audio call
    
    Generates token and updates call status to connected
    """
    try:
        # Get call session
        call_session = await audio_call_service.get_call_session(call_id)
        
        if not call_session:
            raise HTTPException(status_code=404, detail="Call not found")
        
        if call_session["status"] not in ["ringing", "connected"]:
            raise HTTPException(status_code=400, detail=f"Call is {call_session['status']}")
        
        # Generate join token
        token = await webrtc_service.generate_token(
            room_name=call_session["room_id"],
            participant_name=participant_name,
            participant_identity=user_id
        )
        
        # Update call status to connected if it was ringing
        if call_session["status"] == "ringing":
            await audio_call_service.update_call_status(
                call_id,
                CallStatus.CONNECTED
            )
        
        # Log call event
        await audio_call_service.log_call_event(
            call_id=UUID(call_session["id"]),
            event_type="participant_joined",
            event_data={"participant_name": participant_name, "user_id": user_id}
        )
        
        logger.info(f"User {user_id} joined call {call_id}")
        
        return {
            "status": "success",
            "call_id": call_id,
            "token": token,
            "room_id": call_session["room_id"],
            "call_session": call_session
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error joining call: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{call_id}/status")
async def update_call_status(
    call_id: str,
    request: UpdateCallStatusRequest
):
    """Update call status"""
    try:
        call_session = await audio_call_service.update_call_status(
            call_id=call_id,
            status=CallStatus(request.status),
            disconnect_reason=request.disconnect_reason
        )
        
        # If call ended, end voice activity session
        if request.status == "ended":
            try:
                summary = await voice_activity_service.end_voice_session(call_id)
                logger.info(f"Voice session summary: {summary}")
            except:
                pass
        
        return {
            "status": "success",
            "call_session": call_session
        }
        
    except Exception as e:
        logger.error(f"Error updating call status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{call_id}/quality")
async def set_call_quality(
    call_id: str,
    request: CallQualityRequest
):
    """Set call quality score"""
    try:
        success = await audio_call_service.set_call_quality(
            call_id=call_id,
            quality_score=request.quality_score
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Call not found")
        
        return {"status": "success", "quality_score": request.quality_score}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting call quality: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{call_id}")
async def get_call_details(call_id: str):
    """Get call session details"""
    try:
        call_session = await audio_call_service.get_call_session(call_id)
        
        if not call_session:
            raise HTTPException(status_code=404, detail="Call not found")
        
        # Get voice activity state if available
        voice_state = await voice_activity_service.get_session_state(call_id)
        
        return {
            "status": "success",
            "call_session": call_session,
            "voice_activity": voice_state
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting call details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/business/{business_id}/active")
async def get_active_calls(business_id: UUID):
    """Get active calls for a business"""
    try:
        active_calls = await audio_call_service.get_active_calls(business_id)
        
        return {
            "status": "success",
            "active_calls": active_calls,
            "count": len(active_calls)
        }
        
    except Exception as e:
        logger.error(f"Error getting active calls: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}/history")
async def get_call_history(
    user_id: UUID,
    limit: int = 50
):
    """Get call history for a user"""
    try:
        history = await audio_call_service.get_call_history(user_id, limit)
        
        return {
            "status": "success",
            "call_history": history,
            "count": len(history)
        }
        
    except Exception as e:
        logger.error(f"Error getting call history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/business/{business_id}/analytics")
async def get_call_analytics(
    business_id: UUID,
    days: int = 7
):
    """Get call analytics for a business"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        analytics = await audio_call_service.get_call_analytics(
            business_id=business_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "status": "success",
            "analytics": analytics,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting call analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
