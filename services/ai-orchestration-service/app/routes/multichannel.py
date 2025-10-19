"""
Multi-Channel Integration API Routes

Endpoints for all customer entry points: WhatsApp, Instagram, QR, Voice, WebRTC, Web, API
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime

from app.services.multichannel_integration import multichannel_integration, Channel, MessageType
from app.utils import logger

router = APIRouter()


# Request Models
class ChannelMessageRequest(BaseModel):
    """Unified message request for all channels"""
    channel: Channel
    message: str
    sender_id: str
    business_id: str
    message_type: MessageType = MessageType.TEXT
    metadata: Optional[Dict[str, Any]] = None


class QRCodeGenerationRequest(BaseModel):
    """QR code generation request"""
    business_id: str
    qr_type: str = Field(..., description="table, menu, service, event")
    context_data: Dict[str, Any] = Field(default={}, description="Context to embed in QR")


# ==================== UNIFIED CHANNEL ENDPOINT ====================

@router.post("/message")
async def process_channel_message(request: ChannelMessageRequest):
    """
    Unified endpoint for processing messages from any channel
    
    Handles: WhatsApp, Instagram, QR, Voice, WebRTC, Web, API, Facebook
    """
    try:
        logger.info(f"Processing {request.channel} message from {request.sender_id}")
        
        result = await multichannel_integration.process_message(
            channel=request.channel,
            message=request.message,
            sender_id=request.sender_id,
            business_id=request.business_id,
            message_type=request.message_type,
            metadata=request.metadata
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Channel message processing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== CHANNEL-SPECIFIC ENDPOINTS ====================

@router.post("/whatsapp")
async def whatsapp_message(
    message: str,
    sender_id: str,
    business_id: str,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    WhatsApp Business API endpoint
    
    Processes WhatsApp messages with AI-powered responses.
    """
    try:
        result = await multichannel_integration.process_message(
            channel=Channel.WHATSAPP,
            message=message,
            sender_id=sender_id,
            business_id=business_id,
            metadata=metadata or {}
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/instagram")
async def instagram_message(
    message: str,
    sender_id: str,
    business_id: str,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Instagram Direct Message endpoint
    
    Processes Instagram DMs with AI-powered responses.
    """
    try:
        result = await multichannel_integration.process_message(
            channel=Channel.INSTAGRAM,
            message=message,
            sender_id=sender_id,
            business_id=business_id,
            metadata=metadata or {}
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/qr-interaction")
async def qr_interaction(
    message: str,
    sender_id: str,
    business_id: str,
    table_id: Optional[str] = None,
    qr_type: str = "general",
    metadata: Optional[Dict[str, Any]] = None
):
    """
    QR Code interaction endpoint
    
    Processes messages from QR code scanned interactions.
    """
    try:
        qr_metadata = metadata or {}
        qr_metadata.update({"table_id": table_id, "qr_type": qr_type})
        
        result = await multichannel_integration.process_message(
            channel=Channel.QR_CODE,
            message=message,
            sender_id=sender_id,
            business_id=business_id,
            metadata=qr_metadata
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/voice")
async def voice_interaction(
    message: str,
    sender_id: str,
    business_id: str,
    voice_id: str = "default",
    language: str = "en",
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Voice call endpoint
    
    Processes voice interactions (transcribed by Whisper).
    Returns response for text-to-speech (ElevenLabs).
    """
    try:
        voice_metadata = metadata or {}
        voice_metadata.update({"voice_id": voice_id, "language": language})
        
        result = await multichannel_integration.process_message(
            channel=Channel.VOICE,
            message=message,
            sender_id=sender_id,
            business_id=business_id,
            metadata=voice_metadata
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webrtc")
async def webrtc_interaction(
    message: str,
    sender_id: str,
    business_id: str,
    room_id: str,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    WebRTC video/audio call endpoint
    
    Processes WebRTC call interactions with video support.
    """
    try:
        webrtc_metadata = metadata or {}
        webrtc_metadata.update({"room_id": room_id})
        
        result = await multichannel_integration.process_message(
            channel=Channel.WEBRTC,
            message=message,
            sender_id=sender_id,
            business_id=business_id,
            metadata=webrtc_metadata
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/web-chat")
async def web_chat(
    message: str,
    sender_id: str,
    business_id: str,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Web dashboard chat endpoint
    
    Processes messages from web dashboard interface.
    """
    try:
        result = await multichannel_integration.process_message(
            channel=Channel.WEB,
            message=message,
            sender_id=sender_id,
            business_id=business_id,
            metadata=metadata or {}
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/facebook")
async def facebook_message(
    message: str,
    sender_id: str,
    business_id: str,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Facebook Messenger endpoint
    
    Processes Facebook Messenger messages.
    """
    try:
        result = await multichannel_integration.process_message(
            channel=Channel.FACEBOOK,
            message=message,
            sender_id=sender_id,
            business_id=business_id,
            metadata=metadata or {}
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== QR CODE GENERATION ====================

@router.post("/qr/generate")
async def generate_qr_code(request: QRCodeGenerationRequest):
    """
    Generate QR code for business
    
    Creates shareable QR codes for tables, menus, services, or events.
    Returns QR image and shareable link.
    """
    try:
        logger.info(f"Generating QR code for business: {request.business_id}")
        
        result = multichannel_integration.generate_qr_code(
            business_id=request.business_id,
            qr_type=request.qr_type,
            context_data=request.context_data
        )
        
        return result
    
    except Exception as e:
        logger.error(f"QR code generation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ANALYTICS ====================

@router.get("/analytics/{business_id}")
async def get_channel_analytics(
    business_id: str,
    time_period: str = "last_7_days"
):
    """
    Get multi-channel analytics
    
    Returns engagement metrics, popular channels, response times, etc.
    """
    try:
        logger.info(f"Fetching channel analytics for business: {business_id}")
        
        result = await multichannel_integration.get_channel_analytics(
            business_id=business_id,
            time_period=time_period
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Channel analytics error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/channels/list")
async def list_channels():
    """
    List all supported communication channels
    
    Returns complete catalog of entry points.
    """
    return {
        "channels": [
            {
                "id": "whatsapp",
                "name": "WhatsApp Business",
                "endpoint": "/api/v1/multichannel/whatsapp",
                "supported_types": ["text", "image", "video", "audio", "document"],
                "features": ["AI responses", "Order processing", "Customer support"]
            },
            {
                "id": "instagram",
                "name": "Instagram Direct Messages",
                "endpoint": "/api/v1/multichannel/instagram",
                "supported_types": ["text", "image"],
                "features": ["AI responses", "Visual commerce", "Customer engagement"]
            },
            {
                "id": "qr_code",
                "name": "QR Code Access",
                "endpoint": "/api/v1/multichannel/qr-interaction",
                "supported_types": ["text"],
                "features": ["Contactless ordering", "Table service", "Menu access"]
            },
            {
                "id": "voice",
                "name": "Voice Calls",
                "endpoint": "/api/v1/multichannel/voice",
                "supported_types": ["audio"],
                "features": ["Voice AI", "Speech-to-text", "Text-to-speech"]
            },
            {
                "id": "webrtc",
                "name": "WebRTC Video/Audio",
                "endpoint": "/api/v1/multichannel/webrtc",
                "supported_types": ["audio", "video"],
                "features": ["Video calls", "Screen sharing", "AI assistant"]
            },
            {
                "id": "web",
                "name": "Web Dashboard",
                "endpoint": "/api/v1/multichannel/web-chat",
                "supported_types": ["text"],
                "features": ["Dashboard chat", "Real-time responses", "Business insights"]
            },
            {
                "id": "facebook",
                "name": "Facebook Messenger",
                "endpoint": "/api/v1/multichannel/facebook",
                "supported_types": ["text", "image"],
                "features": ["AI responses", "Customer engagement", "Social commerce"]
            }
        ],
        "total_channels": 7,
        "unified_endpoint": "/api/v1/multichannel/message",
        "timestamp": datetime.utcnow().isoformat()
    }
