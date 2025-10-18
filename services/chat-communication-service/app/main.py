"""
X-sevenAI Chat & Communication Service

Real-time chat with WebSockets, voice processing (ElevenLabs/Whisper),
and WebRTC calls via LiveKit with AI handover support.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from prometheus_client import Counter, Histogram
import uvicorn
from datetime import datetime
from typing import Dict, Set, Optional
import json
import os
import logging
import sys

from app.config.settings import settings
from app.services.voice_service import voice_service
from app.services.webrtc_service import webrtc_service
from app.services.audio_call_service import audio_call_service
from app.services.push_notification_service import push_notification_service
from app.services.widget_service import widget_service
from app.services.voice_activity_service import voice_activity_service
from app.routes import audio_calls, widget

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# Configuration
SERVICE_NAME = settings.service_name
SERVICE_PORT = settings.service_port
LOG_LEVEL = settings.log_level

# WebSocket connection manager
class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, room_id: str):
        """Connect client to room"""
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = set()
        self.active_connections[room_id].add(websocket)
        logger.info(f"Client connected to room: {room_id}")
    
    def disconnect(self, websocket: WebSocket, room_id: str):
        """Disconnect client from room"""
        if room_id in self.active_connections:
            self.active_connections[room_id].discard(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
        logger.info(f"Client disconnected from room: {room_id}")
    
    async def broadcast(self, message: dict, room_id: str):
        """Broadcast message to all clients in room"""
        if room_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[room_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting: {e}")
                    disconnected.add(connection)
            
            # Clean up disconnected clients
            for conn in disconnected:
                self.disconnect(conn, room_id)
    
    async def send_personal(self, message: dict, websocket: WebSocket):
        """Send message to specific client"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")


manager = ConnectionManager()

# Prometheus metrics
REQUEST_COUNT = Counter(
    'chat_requests_total',
    'Total requests',
    ['method', 'endpoint', 'status']
)
WEBSOCKET_CONNECTIONS = Counter(
    'chat_websocket_connections_total',
    'Total WebSocket connections'
)
MESSAGES_SENT = Counter(
    'chat_messages_sent_total',
    'Total messages sent',
    ['room_type']
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management"""
    logger.info(f"Starting {SERVICE_NAME}")
    
    # Initialize voice service
    try:
        await voice_service.initialize()
        logger.info("✓ Voice service initialized")
    except Exception as e:
        logger.warning(f"⚠ Voice service not fully available: {e}")
    
    # Initialize WebRTC service
    try:
        await webrtc_service.initialize()
        logger.info("✓ WebRTC service initialized")
    except Exception as e:
        logger.warning(f"⚠ WebRTC service not fully available: {e}")
    
    # Initialize audio call service
    try:
        await audio_call_service.initialize()
        logger.info("✓ Audio call service initialized")
    except Exception as e:
        logger.warning(f"⚠ Audio call service not available: {e}")
    
    # Initialize push notification service
    try:
        await push_notification_service.initialize()
        logger.info("✓ Push notification service initialized")
    except Exception as e:
        logger.warning(f"⚠ Push notification service not available: {e}")
    
    # Initialize widget service
    try:
        await widget_service.initialize()
        logger.info("✓ Widget service initialized")
    except Exception as e:
        logger.warning(f"⚠ Widget service not available: {e}")
    
    # Initialize voice activity service
    try:
        await voice_activity_service.initialize()
        logger.info("✓ Voice activity service initialized")
    except Exception as e:
        logger.warning(f"⚠ Voice activity service not available: {e}")
    
    logger.info(f"🚀 {SERVICE_NAME} is ready")
    
    yield
    
    logger.info(f"Shutting down {SERVICE_NAME}")


# Create FastAPI app
app = FastAPI(
    title="X-sevenAI Chat & Communication Service",
    description="""
    Enterprise-grade real-time communication service with:
    - Audio calling (WhatsApp-style)
    - Voice chat (OpenAI-style)
    - WebRTC via LiveKit
    - Push notifications
    - Widget integration
    - Voice activity detection
    """,
    version="2.0.0",
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

# Include routers
app.include_router(audio_calls.router)
app.include_router(widget.router)


# Health endpoints
@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": "2.0.0",
        "active_rooms": len(manager.active_connections),
        "active_voice_sessions": await voice_activity_service.get_active_sessions_count(),
        "services": {
            "voice": voice_service._initialized,
            "webrtc": webrtc_service._initialized,
            "audio_calls": audio_call_service._initialized,
            "push_notifications": push_notification_service._initialized,
            "widget": widget_service._initialized,
            "voice_activity": voice_activity_service._initialized
        },
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
        "version": "2.0.0",
        "description": "Enterprise-grade audio calling and voice chat service",
        "status": "running",
        "features": [
            "Audio calling (WhatsApp-style)",
            "Voice chat (OpenAI-style)",
            "WebRTC via LiveKit",
            "Push notifications",
            "Widget integration",
            "Voice activity detection",
            "Real-time WebSocket chat"
        ],
        "endpoints": {
            "audio_calls": "/api/v1/audio-calls",
            "widget": "/api/v1/widget",
            "voice": "/api/v1/voice",
            "webrtc": "/api/v1/webrtc",
            "websocket": "/ws/chat/{room_id}",
            "docs": "/docs"
        },
        "timestamp": datetime.utcnow().isoformat()
    }


# WebSocket endpoint for real-time chat
@app.websocket("/ws/chat/{room_id}")
async def websocket_chat(websocket: WebSocket, room_id: str):
    """
    WebSocket endpoint for real-time chat
    
    Supports:
    - Dedicated chat (business-specific)
    - Dashboard chat (business AI assistant)
    - Global chat (cross-business)
    """
    await manager.connect(websocket, room_id)
    WEBSOCKET_CONNECTIONS.inc()
    
    try:
        # Send welcome message
        await manager.send_personal({
            "type": "system",
            "message": f"Connected to room: {room_id}",
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Process message
            processed_message = {
                "type": "message",
                "room_id": room_id,
                "content": message_data.get("content", ""),
                "sender": message_data.get("sender", "anonymous"),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Broadcast to room
            await manager.broadcast(processed_message, room_id)
            MESSAGES_SENT.labels(room_type=room_id.split("_")[0]).inc()
            
            # TODO: Store message in database
            # TODO: Publish to Kafka for analytics
            # TODO: Trigger AI response if needed
            # For now, messages are handled in-memory via WebSocket
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
        await manager.broadcast({
            "type": "system",
            "message": "A user disconnected",
            "timestamp": datetime.utcnow().isoformat()
        }, room_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, room_id)


# Voice endpoints
@app.post("/api/v1/voice/text-to-speech")
async def text_to_speech(text: str, voice_id: Optional[str] = None):
    """
    Convert text to speech using ElevenLabs
    """
    try:
        audio_bytes = await voice_service.text_to_speech(text, voice_id)
        
        return StreamingResponse(
            iter([audio_bytes]),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=speech.mp3"
            }
        )
    except Exception as e:
        logger.error(f"Error in TTS: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/voice/speech-to-text")
async def speech_to_text(audio_file: UploadFile = File(...), language: str = "en"):
    """
    Convert speech to text using Whisper
    """
    try:
        # Read audio file
        audio_bytes = await audio_file.read()
        
        # Transcribe
        result = await voice_service.speech_to_text(audio_bytes, language)
        
        return {
            "status": "success",
            "text": result["text"],
            "language": result["language"],
            "confidence": result["confidence"]
        }
    except Exception as e:
        logger.error(f"Error in STT: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/voice/voices")
async def get_available_voices():
    """
    Get list of available ElevenLabs voices
    """
    try:
        voices = await voice_service.get_available_voices()
        
        return {
            "status": "success",
            "voices": voices,
            "count": len(voices)
        }
    except Exception as e:
        logger.error(f"Error getting voices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# LiveKit WebRTC endpoints
@app.post("/api/v1/webrtc/create-room")
async def create_webrtc_room(
    room_name: str,
    max_participants: int = 10,
    metadata: Optional[dict] = None
):
    """
    Create LiveKit room for WebRTC calls
    """
    try:
        room = await webrtc_service.create_room(
            room_name=room_name,
            max_participants=max_participants,
            metadata=metadata
        )
        
        return {
            "status": "success",
            "room": room
        }
    except Exception as e:
        logger.error(f"Error creating room: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/webrtc/join-token")
async def generate_join_token(
    room_name: str,
    participant_name: str,
    participant_identity: Optional[str] = None,
    metadata: Optional[str] = None
):
    """
    Generate token for joining LiveKit room
    """
    try:
        token = await webrtc_service.generate_token(
            room_name=room_name,
            participant_name=participant_name,
            participant_identity=participant_identity,
            metadata=metadata
        )
        
        return {
            "status": "success",
            "token": token,
            "room_name": room_name,
            "participant_name": participant_name,
            "livekit_url": settings.livekit_url
        }
    except Exception as e:
        logger.error(f"Error generating token: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/webrtc/rooms")
async def list_webrtc_rooms():
    """
    List all active WebRTC rooms
    """
    try:
        rooms = await webrtc_service.list_rooms()
        
        return {
            "status": "success",
            "rooms": rooms,
            "count": len(rooms)
        }
    except Exception as e:
        logger.error(f"Error listing rooms: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/webrtc/rooms/{room_name}")
async def end_webrtc_room(room_name: str):
    """
    End a WebRTC room
    """
    try:
        success = await webrtc_service.end_room(room_name)
        
        if not success:
            raise HTTPException(status_code=404, detail="Room not found")
        
        return {
            "status": "success",
            "message": "Room ended"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ending room: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/webrtc/rooms/{room_name}/participants")
async def get_room_participants(room_name: str):
    """
    Get participants in a WebRTC room
    """
    try:
        participants = await webrtc_service.get_room_participants(room_name)
        
        return {
            "status": "success",
            "room_name": room_name,
            "participants": participants,
            "count": len(participants)
        }
    except Exception as e:
        logger.error(f"Error getting participants: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/webrtc/ai-handover")
async def ai_handover(room_name: str, handover_to: str, reason: Optional[str] = None):
    """
    Handover WebRTC call from AI to human or vice versa
    """
    try:
        # Get current participants
        participants = await webrtc_service.get_room_participants(room_name)
        
        # TODO: Implement actual handover logic with AI agent
        # This would involve:
        # 1. Notifying the new handler
        # 2. Transferring conversation context
        # 3. Updating session metadata
        
        return {
            "status": "success",
            "room_name": room_name,
            "handover_to": handover_to,
            "reason": reason,
            "participants": len(participants),
            "message": "Handover initiated"
        }
    except Exception as e:
        logger.error(f"Error in handover: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Chat history endpoints
@app.get("/api/v1/chat/history/{room_id}")
async def get_chat_history(room_id: str, limit: int = 50):
    """Get chat history for room"""
    # TODO: Query from database
    return {
        "room_id": room_id,
        "messages": [],
        "count": 0
    }


@app.get("/api/v1/chat/rooms")
async def list_active_rooms():
    """List all active chat rooms"""
    return {
        "active_rooms": list(manager.active_connections.keys()),
        "total_connections": sum(len(conns) for conns in manager.active_connections.values())
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=SERVICE_PORT,
        reload=True,
        log_level=LOG_LEVEL.lower()
    )
