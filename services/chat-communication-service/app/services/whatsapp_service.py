"""
WhatsApp Business API Integration

Enterprise WhatsApp messaging with template management and automation.
"""

import os
from typing import Dict, List, Optional, Any
import logging
import httpx
from datetime import datetime

logger = logging.getLogger(__name__)


class WhatsAppService:
    """
    WhatsApp Business API Integration
    
    Features:
    - Send/receive messages
    - Template management
    - Media support (images, documents, videos)
    - Conversation threading
    - Delivery status tracking
    - Automated responses
    """
    
    def __init__(self):
        self.api_url = os.getenv(
            "WHATSAPP_API_URL",
            "https://graph.facebook.com/v18.0"
        )
        self.phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        self.access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
        
        self._client = httpx.AsyncClient(
            base_url=self.api_url,
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            },
            timeout=30.0
        )
    
    async def send_text_message(
        self,
        to: str,
        message: str,
        context_message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send text message to WhatsApp number.
        
        Args:
            to: Recipient phone number (with country code)
            message: Text message content
            context_message_id: Optional message ID to reply to
        """
        try:
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to,
                "type": "text",
                "text": {
                    "preview_url": True,
                    "body": message
                }
            }
            
            # Add context for threading
            if context_message_id:
                payload["context"] = {
                    "message_id": context_message_id
                }
            
            response = await self._client.post(
                f"/{self.phone_number_id}/messages",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                message_id = data.get("messages", [{}])[0].get("id")
                
                logger.info(f"WhatsApp message sent to {to}, ID: {message_id}")
                
                return {
                    "success": True,
                    "message_id": message_id,
                    "to": to
                }
            else:
                logger.error(f"WhatsApp send failed: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": response.text
                }
                
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_template_message(
        self,
        to: str,
        template_name: str,
        language_code: str = "en",
        parameters: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Send pre-approved template message.
        
        Templates must be approved by WhatsApp before use.
        """
        try:
            components = []
            
            if parameters:
                components.append({
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": param}
                        for param in parameters
                    ]
                })
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {
                        "code": language_code
                    },
                    "components": components
                }
            }
            
            response = await self._client.post(
                f"/{self.phone_number_id}/messages",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                message_id = data.get("messages", [{}])[0].get("id")
                
                logger.info(f"WhatsApp template sent to {to}, template: {template_name}")
                
                return {
                    "success": True,
                    "message_id": message_id,
                    "template": template_name
                }
            else:
                logger.error(f"Template send failed: {response.status_code}")
                return {
                    "success": False,
                    "error": response.text
                }
                
        except Exception as e:
            logger.error(f"Error sending template: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_media_message(
        self,
        to: str,
        media_type: str,  # image, document, video, audio
        media_url: str,
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send media message (image, document, video, audio).
        """
        try:
            media_payload = {
                "link": media_url
            }
            
            if caption and media_type in ["image", "video"]:
                media_payload["caption"] = caption
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": media_type,
                media_type: media_payload
            }
            
            response = await self._client.post(
                f"/{self.phone_number_id}/messages",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                message_id = data.get("messages", [{}])[0].get("id")
                
                logger.info(f"WhatsApp {media_type} sent to {to}")
                
                return {
                    "success": True,
                    "message_id": message_id,
                    "media_type": media_type
                }
            else:
                logger.error(f"Media send failed: {response.status_code}")
                return {
                    "success": False,
                    "error": response.text
                }
                
        except Exception as e:
            logger.error(f"Error sending media: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_interactive_message(
        self,
        to: str,
        body_text: str,
        buttons: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Send interactive message with buttons.
        
        Args:
            buttons: List of {"id": "btn_1", "title": "Button Text"}
        """
        try:
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "interactive",
                "interactive": {
                    "type": "button",
                    "body": {
                        "text": body_text
                    },
                    "action": {
                        "buttons": [
                            {
                                "type": "reply",
                                "reply": {
                                    "id": btn["id"],
                                    "title": btn["title"]
                                }
                            }
                            for btn in buttons[:3]  # Max 3 buttons
                        ]
                    }
                }
            }
            
            response = await self._client.post(
                f"/{self.phone_number_id}/messages",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                message_id = data.get("messages", [{}])[0].get("id")
                
                logger.info(f"Interactive message sent to {to}")
                
                return {
                    "success": True,
                    "message_id": message_id
                }
            else:
                logger.error(f"Interactive message failed: {response.status_code}")
                return {
                    "success": False,
                    "error": response.text
                }
                
        except Exception as e:
            logger.error(f"Error sending interactive message: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def mark_message_read(self, message_id: str) -> bool:
        """Mark message as read"""
        try:
            payload = {
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": message_id
            }
            
            response = await self._client.post(
                f"/{self.phone_number_id}/messages",
                json=payload
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error marking message read: {e}")
            return False
    
    async def get_media_url(self, media_id: str) -> Optional[str]:
        """Get downloadable URL for media"""
        try:
            response = await self._client.get(f"/{media_id}")
            
            if response.status_code == 200:
                data = response.json()
                return data.get("url")
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting media URL: {e}")
            return None
    
    async def process_webhook(self, webhook_data: Dict) -> Dict[str, Any]:
        """
        Process incoming WhatsApp webhook.
        
        Handles:
        - Incoming messages
        - Delivery status
        - Read receipts
        """
        try:
            entry = webhook_data.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})
            
            # Process messages
            messages = value.get("messages", [])
            if messages:
                message = messages[0]
                
                return {
                    "type": "message",
                    "from": message.get("from"),
                    "message_id": message.get("id"),
                    "timestamp": message.get("timestamp"),
                    "message_type": message.get("type"),
                    "text": message.get("text", {}).get("body"),
                    "context": message.get("context")
                }
            
            # Process status updates
            statuses = value.get("statuses", [])
            if statuses:
                status = statuses[0]
                
                return {
                    "type": "status",
                    "message_id": status.get("id"),
                    "status": status.get("status"),  # sent, delivered, read, failed
                    "timestamp": status.get("timestamp")
                }
            
            return {"type": "unknown"}
            
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return {"type": "error", "error": str(e)}
    
    async def close(self):
        """Close HTTP client"""
        await self._client.aclose()


# Singleton instance
_whatsapp_service = None

def get_whatsapp_service() -> WhatsAppService:
    """Get singleton instance of WhatsAppService"""
    global _whatsapp_service
    if _whatsapp_service is None:
        _whatsapp_service = WhatsAppService()
    return _whatsapp_service
