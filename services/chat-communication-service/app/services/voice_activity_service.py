"""
Voice Activity Detection Service
Real-time voice processing and activity detection for audio chat
"""

import logging
import asyncio
from typing import Optional, Dict, Any, Callable
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class VoiceActivityState(str, Enum):
    """Voice activity states"""
    IDLE = "idle"
    LISTENING = "listening"
    SPEAKING = "speaking"
    PROCESSING = "processing"
    RESPONDING = "responding"


class VoiceActivityService:
    """Real-time voice activity detection and management"""
    
    def __init__(self):
        """Initialize voice activity service"""
        self._active_sessions: Dict[str, Dict[str, Any]] = {}
        self._initialized = False
    
    async def initialize(self):
        """Initialize voice activity service"""
        if self._initialized:
            return
        
        try:
            self._initialized = True
            logger.info("Voice activity service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize voice activity service: {e}")
    
    async def start_voice_session(
        self,
        session_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Start a voice activity session
        
        Args:
            session_id: Unique session identifier
            config: Voice session configuration
            
        Returns:
            Session details
        """
        try:
            default_config = {
                "silence_threshold": 2.0,  # seconds
                "speech_threshold": 0.5,   # seconds
                "auto_end_silence": 5.0,   # seconds
                "max_duration": 300,       # seconds (5 minutes)
                "language": "en"
            }
            
            session_config = {**default_config, **(config or {})}
            
            self._active_sessions[session_id] = {
                "state": VoiceActivityState.IDLE,
                "config": session_config,
                "started_at": datetime.utcnow(),
                "last_activity_at": datetime.utcnow(),
                "speech_segments": [],
                "total_speech_duration": 0,
                "is_active": True
            }
            
            logger.info(f"Started voice session: {session_id}")
            
            return {
                "session_id": session_id,
                "state": VoiceActivityState.IDLE.value,
                "config": session_config
            }
            
        except Exception as e:
            logger.error(f"Error starting voice session: {e}")
            raise
    
    async def detect_speech_start(
        self,
        session_id: str,
        audio_level: float = 0.0
    ) -> Dict[str, Any]:
        """
        Detect start of speech
        
        Args:
            session_id: Session identifier
            audio_level: Current audio level (0-1)
            
        Returns:
            Detection result
        """
        try:
            if session_id not in self._active_sessions:
                raise Exception(f"Session {session_id} not found")
            
            session = self._active_sessions[session_id]
            
            # Check if audio level exceeds threshold
            if audio_level > 0.3:  # Configurable threshold
                if session["state"] == VoiceActivityState.IDLE:
                    session["state"] = VoiceActivityState.SPEAKING
                    session["current_segment_start"] = datetime.utcnow()
                    session["last_activity_at"] = datetime.utcnow()
                    
                    logger.info(f"Speech started in session {session_id}")
                    
                    return {
                        "speech_detected": True,
                        "state": VoiceActivityState.SPEAKING.value,
                        "timestamp": datetime.utcnow().isoformat()
                    }
            
            return {
                "speech_detected": False,
                "state": session["state"].value
            }
            
        except Exception as e:
            logger.error(f"Error detecting speech start: {e}")
            return {"speech_detected": False, "error": str(e)}
    
    async def detect_speech_end(
        self,
        session_id: str,
        silence_duration: float = 0.0
    ) -> Dict[str, Any]:
        """
        Detect end of speech
        
        Args:
            session_id: Session identifier
            silence_duration: Duration of silence in seconds
            
        Returns:
            Detection result
        """
        try:
            if session_id not in self._active_sessions:
                raise Exception(f"Session {session_id} not found")
            
            session = self._active_sessions[session_id]
            config = session["config"]
            
            # Check if silence exceeds threshold
            if silence_duration >= config["silence_threshold"]:
                if session["state"] == VoiceActivityState.SPEAKING:
                    # Calculate segment duration
                    segment_start = session.get("current_segment_start")
                    if segment_start:
                        segment_duration = (datetime.utcnow() - segment_start).total_seconds()
                        
                        session["speech_segments"].append({
                            "start": segment_start.isoformat(),
                            "duration": segment_duration
                        })
                        
                        session["total_speech_duration"] += segment_duration
                    
                    session["state"] = VoiceActivityState.PROCESSING
                    session["current_segment_start"] = None
                    
                    logger.info(f"Speech ended in session {session_id}")
                    
                    return {
                        "speech_ended": True,
                        "state": VoiceActivityState.PROCESSING.value,
                        "segment_duration": segment_duration if segment_start else 0,
                        "timestamp": datetime.utcnow().isoformat()
                    }
            
            return {
                "speech_ended": False,
                "state": session["state"].value
            }
            
        except Exception as e:
            logger.error(f"Error detecting speech end: {e}")
            return {"speech_ended": False, "error": str(e)}
    
    async def update_session_state(
        self,
        session_id: str,
        state: VoiceActivityState
    ) -> bool:
        """Update session state"""
        try:
            if session_id not in self._active_sessions:
                return False
            
            self._active_sessions[session_id]["state"] = state
            self._active_sessions[session_id]["last_activity_at"] = datetime.utcnow()
            
            logger.info(f"Updated session {session_id} state to {state.value}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating session state: {e}")
            return False
    
    async def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current session state"""
        try:
            if session_id not in self._active_sessions:
                return None
            
            session = self._active_sessions[session_id]
            
            return {
                "session_id": session_id,
                "state": session["state"].value,
                "started_at": session["started_at"].isoformat(),
                "last_activity_at": session["last_activity_at"].isoformat(),
                "total_speech_duration": session["total_speech_duration"],
                "speech_segments_count": len(session["speech_segments"]),
                "is_active": session["is_active"]
            }
            
        except Exception as e:
            logger.error(f"Error getting session state: {e}")
            return None
    
    async def handle_silence_timeout(
        self,
        session_id: str,
        callback: Optional[Callable] = None
    ) -> bool:
        """
        Handle silence timeout (auto-end session)
        
        Args:
            session_id: Session identifier
            callback: Optional callback function
            
        Returns:
            Success status
        """
        try:
            if session_id not in self._active_sessions:
                return False
            
            session = self._active_sessions[session_id]
            config = session["config"]
            
            # Check if silence timeout exceeded
            time_since_activity = (datetime.utcnow() - session["last_activity_at"]).total_seconds()
            
            if time_since_activity >= config["auto_end_silence"]:
                session["is_active"] = False
                session["state"] = VoiceActivityState.IDLE
                
                logger.info(f"Session {session_id} ended due to silence timeout")
                
                if callback:
                    await callback(session_id, "silence_timeout")
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error handling silence timeout: {e}")
            return False
    
    async def end_voice_session(self, session_id: str) -> Dict[str, Any]:
        """End voice session and return summary"""
        try:
            if session_id not in self._active_sessions:
                raise Exception(f"Session {session_id} not found")
            
            session = self._active_sessions[session_id]
            
            # Calculate session summary
            total_duration = (datetime.utcnow() - session["started_at"]).total_seconds()
            
            summary = {
                "session_id": session_id,
                "total_duration": total_duration,
                "total_speech_duration": session["total_speech_duration"],
                "speech_segments_count": len(session["speech_segments"]),
                "speech_ratio": session["total_speech_duration"] / total_duration if total_duration > 0 else 0,
                "ended_at": datetime.utcnow().isoformat()
            }
            
            # Remove session
            del self._active_sessions[session_id]
            
            logger.info(f"Ended voice session: {session_id}")
            
            return summary
            
        except Exception as e:
            logger.error(f"Error ending voice session: {e}")
            raise
    
    async def cleanup_inactive_sessions(self, max_age_seconds: int = 3600):
        """Cleanup inactive sessions older than max_age"""
        try:
            current_time = datetime.utcnow()
            sessions_to_remove = []
            
            for session_id, session in self._active_sessions.items():
                age = (current_time - session["started_at"]).total_seconds()
                
                if age > max_age_seconds or not session["is_active"]:
                    sessions_to_remove.append(session_id)
            
            for session_id in sessions_to_remove:
                del self._active_sessions[session_id]
                logger.info(f"Cleaned up inactive session: {session_id}")
            
            return len(sessions_to_remove)
            
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {e}")
            return 0
    
    async def get_active_sessions_count(self) -> int:
        """Get count of active sessions"""
        return len([s for s in self._active_sessions.values() if s["is_active"]])


# Global voice activity service instance
voice_activity_service = VoiceActivityService()
