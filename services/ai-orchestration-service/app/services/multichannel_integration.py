"""
Multi-Channel Integration Service

Handles all customer entry points: WhatsApp, Instagram, QR, Voice/WebRTC, Web, API
Provides unified interface for cross-channel AI interactions.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import json
import qrcode
import io
import base64

from app.config import settings
from app.utils import logger
from app.services.langgraph_orchestrator import langgraph_orchestrator
from app.services.dspy_prompts import dspy_service


class Channel(str, Enum):
    """Supported communication channels"""
    WHATSAPP = "whatsapp"
    INSTAGRAM = "instagram"
    QR_CODE = "qr_code"
    VOICE = "voice"
    WEBRTC = "webrtc"
    WEB = "web"
    API = "api"
    FACEBOOK = "facebook"


class MessageType(str, Enum):
    """Message types"""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    LOCATION = "location"


class MultiChannelIntegration:
    """
    Unified multi-channel integration service
    
    Manages customer interactions across all entry points with consistent
    AI-powered responses regardless of channel.
    """
    
    def __init__(self):
        self._initialized = False
        self.channel_handlers = {}
    
    async def initialize(self):
        """Initialize multi-channel integration"""
        if self._initialized:
            return
        
        logger.info("Initializing Multi-Channel Integration")
        
        # Register channel handlers
        self.channel_handlers = {
            Channel.WHATSAPP: self._handle_whatsapp,
            Channel.INSTAGRAM: self._handle_instagram,
            Channel.QR_CODE: self._handle_qr,
            Channel.VOICE: self._handle_voice,
            Channel.WEBRTC: self._handle_webrtc,
            Channel.WEB: self._handle_web,
            Channel.API: self._handle_api,
            Channel.FACEBOOK: self._handle_facebook
        }
        
        self._initialized = True
        logger.info("Multi-Channel Integration initialized")
    
    async def process_message(
        self,
        channel: Channel,
        message: str,
        sender_id: str,
        business_id: str,
        message_type: MessageType = MessageType.TEXT,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process incoming message from any channel
        
        Args:
            channel: Communication channel
            message: Message content
            sender_id: Customer/sender identifier
            business_id: Business identifier
            message_type: Type of message
            metadata: Additional channel-specific metadata
        
        Returns:
            Unified response with channel-specific formatting
        """
        if not self._initialized:
            await self.initialize()
        
        logger.info(f"Processing {channel} message from {sender_id}")
        
        # Route to channel-specific handler
        handler = self.channel_handlers.get(channel)
        if not handler:
            raise ValueError(f"Unsupported channel: {channel}")
        
        return await handler(
            message=message,
            sender_id=sender_id,
            business_id=business_id,
            message_type=message_type,
            metadata=metadata or {}
        )
    
    # ==================== CHANNEL HANDLERS ====================
    
    async def _handle_whatsapp(
        self,
        message: str,
        sender_id: str,
        business_id: str,
        message_type: MessageType,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle WhatsApp messages"""
        logger.info(f"WhatsApp message from {sender_id}")
        
        # Execute LangGraph workflow for context-aware response
        session_id = f"whatsapp_{sender_id}_{business_id}"
        
        result = await langgraph_orchestrator.execute_workflow(
            workflow_name="customer_support",
            initial_message=message,
            session_id=session_id,
            user_id=sender_id,
            business_id=business_id
        )
        
        # Format response for WhatsApp
        response_text = result.get("messages", [])[-1].get("content", "") if result.get("messages") else ""
        
        return {
            "channel": "whatsapp",
            "sender_id": sender_id,
            "business_id": business_id,
            "response": {
                "type": "text",
                "content": response_text,
                "whatsapp_format": {
                    "to": sender_id,
                    "type": "text",
                    "text": {"body": response_text}
                }
            },
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _handle_instagram(
        self,
        message: str,
        sender_id: str,
        business_id: str,
        message_type: MessageType,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle Instagram direct messages"""
        logger.info(f"Instagram message from {sender_id}")
        
        # Process with DSPy for social media optimized responses
        result = await dspy_service.process_business_query(
            query=message,
            context=f"Instagram DM from customer {sender_id} to business {business_id}"
        )
        
        response_text = result.get("answer", "")
        
        # Keep responses concise for Instagram (character limit)
        if len(response_text) > 1000:
            response_text = response_text[:997] + "..."
        
        return {
            "channel": "instagram",
            "sender_id": sender_id,
            "business_id": business_id,
            "response": {
                "type": "text",
                "content": response_text,
                "instagram_format": {
                    "recipient_id": sender_id,
                    "message": {"text": response_text}
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _handle_qr(
        self,
        message: str,
        sender_id: str,
        business_id: str,
        message_type: MessageType,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle QR code scanned interactions"""
        logger.info(f"QR code interaction from {sender_id}")
        
        # Extract QR context
        table_id = metadata.get("table_id")
        qr_type = metadata.get("qr_type", "general")
        
        # Enhance context for QR-specific workflow
        enhanced_context = f"QR Code ({qr_type})"
        if table_id:
            enhanced_context += f" - Table {table_id}"
        
        session_id = f"qr_{business_id}_{table_id or sender_id}"
        
        # Execute dedicated chat workflow
        result = await langgraph_orchestrator.execute_workflow(
            workflow_name="customer_support",
            initial_message=message,
            session_id=session_id,
            user_id=sender_id,
            business_id=business_id
        )
        
        response_text = result.get("messages", [])[-1].get("content", "") if result.get("messages") else ""
        
        return {
            "channel": "qr_code",
            "sender_id": sender_id,
            "business_id": business_id,
            "qr_context": {
                "table_id": table_id,
                "qr_type": qr_type
            },
            "response": {
                "type": "text",
                "content": response_text,
                "web_format": {
                    "html": f"<div class='qr-response'>{response_text}</div>",
                    "table_id": table_id
                }
            },
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _handle_voice(
        self,
        message: str,
        sender_id: str,
        business_id: str,
        message_type: MessageType,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle voice call interactions"""
        logger.info(f"Voice interaction from {sender_id}")
        
        # Process voice input (already transcribed by Whisper)
        session_id = f"voice_{sender_id}_{business_id}"
        
        result = await langgraph_orchestrator.execute_workflow(
            workflow_name="customer_support",
            initial_message=message,
            session_id=session_id,
            user_id=sender_id,
            business_id=business_id
        )
        
        response_text = result.get("messages", [])[-1].get("content", "") if result.get("messages") else ""
        
        # Format for text-to-speech (ElevenLabs)
        return {
            "channel": "voice",
            "sender_id": sender_id,
            "business_id": business_id,
            "response": {
                "type": "voice",
                "content": response_text,
                "voice_format": {
                    "text": response_text,
                    "voice_id": metadata.get("voice_id", "default"),
                    "language": metadata.get("language", "en"),
                    "tts_provider": "elevenlabs"
                }
            },
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _handle_webrtc(
        self,
        message: str,
        sender_id: str,
        business_id: str,
        message_type: MessageType,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle WebRTC video/audio calls"""
        logger.info(f"WebRTC interaction from {sender_id}")
        
        # Similar to voice but includes video capabilities
        session_id = f"webrtc_{sender_id}_{business_id}"
        
        result = await langgraph_orchestrator.execute_workflow(
            workflow_name="customer_support",
            initial_message=message,
            session_id=session_id,
            user_id=sender_id,
            business_id=business_id
        )
        
        response_text = result.get("messages", [])[-1].get("content", "") if result.get("messages") else ""
        
        return {
            "channel": "webrtc",
            "sender_id": sender_id,
            "business_id": business_id,
            "response": {
                "type": "multimedia",
                "content": response_text,
                "webrtc_format": {
                    "text": response_text,
                    "room_id": metadata.get("room_id"),
                    "supports_video": True,
                    "supports_audio": True,
                    "tts_enabled": True
                }
            },
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _handle_web(
        self,
        message: str,
        sender_id: str,
        business_id: str,
        message_type: MessageType,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle web dashboard chat"""
        logger.info(f"Web chat from {sender_id}")
        
        session_id = f"web_{sender_id}_{business_id}"
        
        result = await langgraph_orchestrator.execute_workflow(
            workflow_name="customer_support",
            initial_message=message,
            session_id=session_id,
            user_id=sender_id,
            business_id=business_id
        )
        
        response_text = result.get("messages", [])[-1].get("content", "") if result.get("messages") else ""
        
        return {
            "channel": "web",
            "sender_id": sender_id,
            "business_id": business_id,
            "response": {
                "type": "text",
                "content": response_text,
                "web_format": {
                    "html": f"<p>{response_text}</p>",
                    "supports_markdown": True
                }
            },
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _handle_api(
        self,
        message: str,
        sender_id: str,
        business_id: str,
        message_type: MessageType,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle direct API calls"""
        logger.info(f"API request from {sender_id}")
        
        # Process with DSPy for structured responses
        result = await dspy_service.process_business_query(
            query=message,
            context=json.dumps(metadata)
        )
        
        return {
            "channel": "api",
            "sender_id": sender_id,
            "business_id": business_id,
            "response": {
                "type": "json",
                "content": result.get("answer", ""),
                "structured_data": result
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _handle_facebook(
        self,
        message: str,
        sender_id: str,
        business_id: str,
        message_type: MessageType,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle Facebook Messenger"""
        logger.info(f"Facebook message from {sender_id}")
        
        session_id = f"facebook_{sender_id}_{business_id}"
        
        result = await langgraph_orchestrator.execute_workflow(
            workflow_name="customer_support",
            initial_message=message,
            session_id=session_id,
            user_id=sender_id,
            business_id=business_id
        )
        
        response_text = result.get("messages", [])[-1].get("content", "") if result.get("messages") else ""
        
        return {
            "channel": "facebook",
            "sender_id": sender_id,
            "business_id": business_id,
            "response": {
                "type": "text",
                "content": response_text,
                "facebook_format": {
                    "recipient": {"id": sender_id},
                    "message": {"text": response_text}
                }
            },
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # ==================== QR CODE GENERATION ====================
    
    def generate_qr_code(
        self,
        business_id: str,
        qr_type: str,
        context_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate QR code for business
        
        Args:
            business_id: Business identifier
            qr_type: Type of QR (table, menu, service, event)
            context_data: Context to embed in QR
        
        Returns:
            QR code image and shareable link
        """
        logger.info(f"Generating QR code: {qr_type} for business {business_id}")
        
        # Create QR data payload
        qr_data = {
            "business_id": business_id,
            "qr_type": qr_type,
            "timestamp": datetime.utcnow().isoformat(),
            **context_data
        }
        
        # Generate shareable link
        qr_id = f"qr_{business_id}_{qr_type}_{context_data.get('table_id', 'general')}"
        shareable_link = f"https://x7ai.app/qr/{qr_id}"
        
        # Add link to payload
        qr_data["link"] = shareable_link
        
        # Generate QR code image
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(json.dumps(qr_data))
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return {
            "qr_id": qr_id,
            "business_id": business_id,
            "qr_type": qr_type,
            "shareable_link": shareable_link,
            "qr_image_base64": img_str,
            "context_data": context_data,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    # ==================== CHANNEL ANALYTICS ====================
    
    async def get_channel_analytics(
        self,
        business_id: str,
        time_period: str = "last_7_days"
    ) -> Dict[str, Any]:
        """
        Get analytics across all channels
        
        Returns engagement metrics, popular channels, response times, etc.
        """
        logger.info(f"Fetching channel analytics for {business_id}")
        
        # This would query actual metrics from database
        # For now, return structure
        return {
            "business_id": business_id,
            "time_period": time_period,
            "channels": {
                "whatsapp": {
                    "total_messages": 0,
                    "response_rate": 0.0,
                    "avg_response_time_seconds": 0,
                    "customer_satisfaction": 0.0
                },
                "instagram": {
                    "total_messages": 0,
                    "response_rate": 0.0,
                    "avg_response_time_seconds": 0,
                    "customer_satisfaction": 0.0
                },
                "qr_code": {
                    "total_scans": 0,
                    "unique_users": 0,
                    "conversion_rate": 0.0
                },
                "voice": {
                    "total_calls": 0,
                    "avg_call_duration_seconds": 0,
                    "resolution_rate": 0.0
                },
                "webrtc": {
                    "total_sessions": 0,
                    "avg_session_duration_seconds": 0,
                    "video_enabled_percentage": 0.0
                },
                "web": {
                    "total_messages": 0,
                    "response_rate": 0.0,
                    "avg_response_time_seconds": 0
                }
            },
            "overall": {
                "total_interactions": 0,
                "most_popular_channel": "whatsapp",
                "peak_hours": [],
                "customer_satisfaction_avg": 0.0
            },
            "timestamp": datetime.utcnow().isoformat()
        }


# Global multi-channel integration instance
multichannel_integration = MultiChannelIntegration()
