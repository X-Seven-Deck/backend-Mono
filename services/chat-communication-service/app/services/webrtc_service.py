"""
WebRTC Service for Chat & Communication
Handles LiveKit room management and token generation
"""

import logging
import time
from typing import Optional, Dict, Any
from livekit import api

from app.config.settings import settings

logger = logging.getLogger(__name__)


class WebRTCService:
    """WebRTC service using LiveKit"""
    
    def __init__(self):
        """Initialize WebRTC service"""
        self._initialized = False
    
    async def initialize(self):
        """Initialize WebRTC service"""
        if self._initialized:
            return
        
        try:
            if not all([settings.livekit_url, settings.livekit_api_key, settings.livekit_api_secret]):
                logger.warning("LiveKit credentials not configured")
                return
            
            self._initialized = True
            logger.info("WebRTC service initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize WebRTC service: {e}")
    
    async def create_room(
        self,
        room_name: str,
        max_participants: int = 10,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a LiveKit room
        
        Args:
            room_name: Name of the room
            max_participants: Maximum number of participants
            metadata: Additional room metadata
            
        Returns:
            Room details
        """
        try:
            if not self._initialized:
                raise Exception("WebRTC service not initialized")
            
            # Create LiveKit API client
            livekit_api = api.LiveKitAPI(
                settings.livekit_url,
                settings.livekit_api_key,
                settings.livekit_api_secret
            )
            
            # Create room
            room = await livekit_api.room.create_room(
                api.CreateRoomRequest(
                    name=room_name,
                    max_participants=max_participants,
                    metadata=str(metadata) if metadata else ""
                )
            )
            
            logger.info(f"Created LiveKit room: {room_name}")
            
            return {
                "room_id": room.sid,
                "room_name": room.name,
                "max_participants": room.max_participants,
                "num_participants": room.num_participants,
                "created_at": room.creation_time
            }
            
        except Exception as e:
            logger.error(f"Error creating room: {e}")
            # Return mock data if LiveKit not available
            return {
                "room_id": f"room_{int(time.time())}",
                "room_name": room_name,
                "max_participants": max_participants,
                "num_participants": 0,
                "created_at": int(time.time()),
                "mock": True
            }
    
    async def generate_token(
        self,
        room_name: str,
        participant_name: str,
        participant_identity: Optional[str] = None,
        metadata: Optional[str] = None
    ) -> str:
        """
        Generate access token for joining a room
        
        Args:
            room_name: Name of the room
            participant_name: Display name of participant
            participant_identity: Unique identity (optional)
            metadata: Participant metadata (optional)
            
        Returns:
            JWT access token
        """
        try:
            if not self._initialized:
                raise Exception("WebRTC service not initialized")
            
            from livekit import api
            
            # Generate token
            token = api.AccessToken(
                settings.livekit_api_key,
                settings.livekit_api_secret
            )
            
            token.with_identity(participant_identity or participant_name)
            token.with_name(participant_name)
            token.with_grants(api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True
            ))
            
            if metadata:
                token.with_metadata(metadata)
            
            jwt_token = token.to_jwt()
            
            logger.info(f"Generated token for {participant_name} in room {room_name}")
            
            return jwt_token
            
        except Exception as e:
            logger.error(f"Error generating token: {e}")
            # Return mock token if LiveKit not available
            return f"mock_token_{int(time.time())}"
    
    async def list_rooms(self) -> list:
        """List all active rooms"""
        try:
            if not self._initialized:
                return []
            
            livekit_api = api.LiveKitAPI(
                settings.livekit_url,
                settings.livekit_api_key,
                settings.livekit_api_secret
            )
            
            rooms = await livekit_api.room.list_rooms(api.ListRoomsRequest())
            
            return [
                {
                    "room_id": room.sid,
                    "room_name": room.name,
                    "num_participants": room.num_participants,
                    "created_at": room.creation_time
                }
                for room in rooms
            ]
            
        except Exception as e:
            logger.error(f"Error listing rooms: {e}")
            return []
    
    async def end_room(self, room_name: str) -> bool:
        """End a room and disconnect all participants"""
        try:
            if not self._initialized:
                return False
            
            livekit_api = api.LiveKitAPI(
                settings.livekit_url,
                settings.livekit_api_key,
                settings.livekit_api_secret
            )
            
            await livekit_api.room.delete_room(
                api.DeleteRoomRequest(room=room_name)
            )
            
            logger.info(f"Ended room: {room_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error ending room: {e}")
            return False
    
    async def get_room_participants(self, room_name: str) -> list:
        """Get list of participants in a room"""
        try:
            if not self._initialized:
                return []
            
            livekit_api = api.LiveKitAPI(
                settings.livekit_url,
                settings.livekit_api_key,
                settings.livekit_api_secret
            )
            
            participants = await livekit_api.room.list_participants(
                api.ListParticipantsRequest(room=room_name)
            )
            
            return [
                {
                    "identity": p.identity,
                    "name": p.name,
                    "state": p.state,
                    "joined_at": p.joined_at
                }
                for p in participants
            ]
            
        except Exception as e:
            logger.error(f"Error getting participants: {e}")
            return []


# Global WebRTC service instance
webrtc_service = WebRTCService()
