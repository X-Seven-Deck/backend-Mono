"""
Audio Call Service for Enterprise-Grade Voice Communication
Handles audio call sessions, state management, and call lifecycle
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum

from supabase import create_client, Client
from app.config.settings import settings

logger = logging.getLogger(__name__)


class CallStatus(str, Enum):
    """Call status enumeration"""
    INITIATING = "initiating"
    RINGING = "ringing"
    CONNECTED = "connected"
    ON_HOLD = "on_hold"
    ENDED = "ended"
    FAILED = "failed"
    MISSED = "missed"


class CallType(str, Enum):
    """Call type enumeration"""
    BUSINESS_SUPPORT = "business_support"
    AI_ASSISTANT = "ai_assistant"
    AGENT_CALL = "agent_call"
    CUSTOMER_CALL = "customer_call"


class AudioCallService:
    """Enterprise-grade audio call management service"""
    
    def __init__(self):
        """Initialize audio call service"""
        self.client: Optional[Client] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize Supabase client"""
        if self._initialized:
            return
        
        try:
            self.client = create_client(
                settings.supabase_url,
                settings.supabase_key
            )
            self._initialized = True
            logger.info("Audio call service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize audio call service: {e}")
            raise
    
    async def create_call_session(
        self,
        business_id: UUID,
        caller_id: Optional[UUID],
        callee_id: Optional[UUID],
        call_type: CallType,
        room_id: str,
        direction: str = "outbound",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new audio call session
        
        Args:
            business_id: Business identifier
            caller_id: Caller user ID
            callee_id: Callee user ID
            call_type: Type of call
            room_id: LiveKit room ID
            direction: Call direction (inbound/outbound)
            metadata: Additional call metadata
            
        Returns:
            Call session details
        """
        try:
            call_id = f"call_{uuid4().hex[:16]}"
            
            data = {
                "call_id": call_id,
                "room_id": room_id,
                "business_id": str(business_id),
                "caller_id": str(caller_id) if caller_id else None,
                "callee_id": str(callee_id) if callee_id else None,
                "call_type": call_type.value,
                "status": CallStatus.INITIATING.value,
                "direction": direction,
                "metadata": metadata or {}
            }
            
            result = self.client.table("audio_call_sessions").insert(data).execute()
            
            if result.data:
                logger.info(f"Created audio call session: {call_id}")
                return result.data[0]
            else:
                raise Exception("Failed to create call session")
                
        except Exception as e:
            logger.error(f"Error creating call session: {e}")
            raise
    
    async def update_call_status(
        self,
        call_id: str,
        status: CallStatus,
        disconnect_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update call status
        
        Args:
            call_id: Call identifier
            status: New call status
            disconnect_reason: Reason for disconnection (if applicable)
            
        Returns:
            Updated call session
        """
        try:
            updates = {"status": status.value}
            
            if status == CallStatus.CONNECTED:
                updates["connected_at"] = datetime.utcnow().isoformat()
            elif status == CallStatus.ENDED:
                updates["ended_at"] = datetime.utcnow().isoformat()
                if disconnect_reason:
                    updates["disconnect_reason"] = disconnect_reason
            
            result = self.client.table("audio_call_sessions")\
                .update(updates)\
                .eq("call_id", call_id)\
                .execute()
            
            if result.data:
                logger.info(f"Updated call {call_id} status to {status.value}")
                return result.data[0]
            else:
                raise Exception(f"Call {call_id} not found")
                
        except Exception as e:
            logger.error(f"Error updating call status: {e}")
            raise
    
    async def get_call_session(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Get call session by ID"""
        try:
            result = self.client.table("audio_call_sessions")\
                .select("*")\
                .eq("call_id", call_id)\
                .single()\
                .execute()
            
            return result.data if result.data else None
            
        except Exception as e:
            logger.error(f"Error getting call session: {e}")
            return None
    
    async def get_active_calls(
        self,
        business_id: UUID
    ) -> List[Dict[str, Any]]:
        """Get all active calls for a business"""
        try:
            result = self.client.table("audio_call_sessions")\
                .select("*")\
                .eq("business_id", str(business_id))\
                .in_("status", [CallStatus.RINGING.value, CallStatus.CONNECTED.value, CallStatus.ON_HOLD.value])\
                .order("created_at", desc=True)\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error getting active calls: {e}")
            return []
    
    async def log_call_event(
        self,
        call_id: UUID,
        event_type: str,
        event_data: Dict[str, Any],
        user_id: Optional[UUID] = None
    ) -> bool:
        """Log a call event for analytics and debugging"""
        try:
            data = {
                "call_id": str(call_id),
                "event_type": event_type,
                "event_data": event_data,
                "user_id": str(user_id) if user_id else None
            }
            
            result = self.client.table("call_events").insert(data).execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error logging call event: {e}")
            return False
    
    async def set_call_quality(
        self,
        call_id: str,
        quality_score: float
    ) -> bool:
        """Set call quality score (0-5)"""
        try:
            result = self.client.table("audio_call_sessions")\
                .update({"quality_score": quality_score})\
                .eq("call_id", call_id)\
                .execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error setting call quality: {e}")
            return False
    
    async def enable_recording(
        self,
        call_id: str,
        recording_url: Optional[str] = None
    ) -> bool:
        """Enable call recording"""
        try:
            updates = {"recording_enabled": True}
            if recording_url:
                updates["recording_url"] = recording_url
            
            result = self.client.table("audio_call_sessions")\
                .update(updates)\
                .eq("call_id", call_id)\
                .execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error enabling recording: {e}")
            return False
    
    async def get_call_history(
        self,
        user_id: UUID,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get call history for a user"""
        try:
            result = self.client.table("audio_call_sessions")\
                .select("*")\
                .or_(f"caller_id.eq.{user_id},callee_id.eq.{user_id}")\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error getting call history: {e}")
            return []
    
    async def get_call_analytics(
        self,
        business_id: UUID,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get call analytics for a business"""
        try:
            result = self.client.table("audio_call_sessions")\
                .select("*")\
                .eq("business_id", str(business_id))\
                .gte("created_at", start_date.isoformat())\
                .lte("created_at", end_date.isoformat())\
                .execute()
            
            calls = result.data if result.data else []
            
            analytics = {
                "total_calls": len(calls),
                "completed_calls": len([c for c in calls if c["status"] == CallStatus.ENDED.value]),
                "missed_calls": len([c for c in calls if c["status"] == CallStatus.MISSED.value]),
                "failed_calls": len([c for c in calls if c["status"] == CallStatus.FAILED.value]),
                "avg_duration": sum([c.get("duration_seconds", 0) for c in calls]) / len(calls) if calls else 0,
                "avg_quality": sum([c.get("quality_score", 0) for c in calls if c.get("quality_score")]) / len([c for c in calls if c.get("quality_score")]) if calls else 0,
                "call_types": {}
            }
            
            # Count by call type
            for call in calls:
                call_type = call.get("call_type", "unknown")
                analytics["call_types"][call_type] = analytics["call_types"].get(call_type, 0) + 1
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting call analytics: {e}")
            return {}


# Global audio call service instance
audio_call_service = AudioCallService()
