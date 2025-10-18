"""
Instagram Messaging API Integration

Direct messaging and engagement through Instagram.
"""

import os
from typing import Dict, List, Optional, Any
import logging
import httpx

logger = logging.getLogger(__name__)


class InstagramService:
    """
    Instagram Messaging API Integration
    
    Features:
    - Send/receive direct messages
    - Story mentions and replies
    - Comment management
    - Media sharing
    - Quick replies and ice breakers
    """
    
    def __init__(self):
        self.api_url = os.getenv(
            "INSTAGRAM_API_URL",
            "https://graph.facebook.com/v18.0"
        )
        self.instagram_account_id = os.getenv("INSTAGRAM_ACCOUNT_ID")
        self.access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
        
        self._client = httpx.AsyncClient(
            base_url=self.api_url,
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            },
            timeout=30.0
        )
    
    async def send_message(
        self,
        recipient_id: str,
        message_text: str,
        message_type: str = "RESPONSE"  # RESPONSE, UPDATE, MESSAGE_TAG
    ) -> Dict[str, Any]:
        """
        Send direct message to Instagram user.
        
        Args:
            recipient_id: Instagram user ID (IGSID)
            message_text: Message content
            message_type: RESPONSE (24h window), UPDATE, or MESSAGE_TAG
        """
        try:
            payload = {
                "recipient": {
                    "id": recipient_id
                },
                "message": {
                    "text": message_text
                },
                "messaging_type": message_type
            }
            
            response = await self._client.post(
                f"/{self.instagram_account_id}/messages",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                message_id = data.get("message_id")
                
                logger.info(f"Instagram message sent to {recipient_id}, ID: {message_id}")
                
                return {
                    "success": True,
                    "message_id": message_id,
                    "recipient_id": recipient_id
                }
            else:
                logger.error(f"Instagram send failed: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": response.text
                }
                
        except Exception as e:
            logger.error(f"Error sending Instagram message: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_media_message(
        self,
        recipient_id: str,
        media_url: str,
        media_type: str = "image"  # image, video
    ) -> Dict[str, Any]:
        """
        Send media message (image or video).
        """
        try:
            attachment_payload = {
                "type": media_type,
                "payload": {
                    "url": media_url,
                    "is_reusable": True
                }
            }
            
            payload = {
                "recipient": {
                    "id": recipient_id
                },
                "message": {
                    "attachment": attachment_payload
                }
            }
            
            response = await self._client.post(
                f"/{self.instagram_account_id}/messages",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                message_id = data.get("message_id")
                
                logger.info(f"Instagram {media_type} sent to {recipient_id}")
                
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
    
    async def send_quick_replies(
        self,
        recipient_id: str,
        message_text: str,
        quick_replies: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Send message with quick reply buttons.
        
        Args:
            quick_replies: List of {"content_type": "text", "title": "Option", "payload": "value"}
        """
        try:
            payload = {
                "recipient": {
                    "id": recipient_id
                },
                "message": {
                    "text": message_text,
                    "quick_replies": quick_replies[:13]  # Max 13 quick replies
                }
            }
            
            response = await self._client.post(
                f"/{self.instagram_account_id}/messages",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                
                logger.info(f"Quick replies sent to {recipient_id}")
                
                return {
                    "success": True,
                    "message_id": data.get("message_id")
                }
            else:
                logger.error(f"Quick replies failed: {response.status_code}")
                return {
                    "success": False,
                    "error": response.text
                }
                
        except Exception as e:
            logger.error(f"Error sending quick replies: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_generic_template(
        self,
        recipient_id: str,
        elements: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Send carousel/generic template with multiple cards.
        
        Args:
            elements: List of card elements with title, subtitle, image_url, buttons
        """
        try:
            payload = {
                "recipient": {
                    "id": recipient_id
                },
                "message": {
                    "attachment": {
                        "type": "template",
                        "payload": {
                            "template_type": "generic",
                            "elements": elements[:10]  # Max 10 elements
                        }
                    }
                }
            }
            
            response = await self._client.post(
                f"/{self.instagram_account_id}/messages",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                
                logger.info(f"Generic template sent to {recipient_id}")
                
                return {
                    "success": True,
                    "message_id": data.get("message_id")
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
    
    async def reply_to_story(
        self,
        recipient_id: str,
        story_id: str,
        message_text: str
    ) -> Dict[str, Any]:
        """
        Reply to user's story.
        """
        try:
            payload = {
                "recipient": {
                    "id": recipient_id
                },
                "message": {
                    "text": message_text,
                    "attachment": {
                        "type": "story_mention",
                        "payload": {
                            "id": story_id
                        }
                    }
                }
            }
            
            response = await self._client.post(
                f"/{self.instagram_account_id}/messages",
                json=payload
            )
            
            if response.status_code == 200:
                logger.info(f"Story reply sent to {recipient_id}")
                return {
                    "success": True,
                    "message_id": response.json().get("message_id")
                }
            else:
                return {
                    "success": False,
                    "error": response.text
                }
                
        except Exception as e:
            logger.error(f"Error replying to story: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """
        Get Instagram user profile information.
        """
        try:
            response = await self._client.get(
                f"/{user_id}",
                params={
                    "fields": "name,username,profile_pic"
                }
            )
            
            if response.status_code == 200:
                return response.json()
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return None
    
    async def process_webhook(self, webhook_data: Dict) -> Dict[str, Any]:
        """
        Process incoming Instagram webhook.
        
        Handles:
        - Direct messages
        - Story mentions
        - Story replies
        - Message reactions
        """
        try:
            entry = webhook_data.get("entry", [{}])[0]
            messaging = entry.get("messaging", [{}])[0]
            
            sender_id = messaging.get("sender", {}).get("id")
            recipient_id = messaging.get("recipient", {}).get("id")
            timestamp = messaging.get("timestamp")
            
            # Process message
            if "message" in messaging:
                message = messaging["message"]
                
                result = {
                    "type": "message",
                    "sender_id": sender_id,
                    "recipient_id": recipient_id,
                    "message_id": message.get("mid"),
                    "timestamp": timestamp
                }
                
                # Text message
                if "text" in message:
                    result["text"] = message["text"]
                
                # Media attachment
                if "attachments" in message:
                    result["attachments"] = message["attachments"]
                
                # Quick reply
                if "quick_reply" in message:
                    result["quick_reply"] = message["quick_reply"]
                
                # Story mention
                if "story_mention" in message:
                    result["story_mention"] = message["story_mention"]
                
                return result
            
            # Process reaction
            if "reaction" in messaging:
                reaction = messaging["reaction"]
                
                return {
                    "type": "reaction",
                    "sender_id": sender_id,
                    "mid": reaction.get("mid"),
                    "reaction": reaction.get("reaction"),
                    "emoji": reaction.get("emoji"),
                    "action": reaction.get("action"),  # react or unreact
                    "timestamp": timestamp
                }
            
            return {"type": "unknown"}
            
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return {"type": "error", "error": str(e)}
    
    async def set_ice_breakers(self, ice_breakers: List[Dict[str, str]]) -> bool:
        """
        Set ice breaker questions for new conversations.
        
        Args:
            ice_breakers: List of {"question": "...", "payload": "..."}
        """
        try:
            payload = {
                "ice_breakers": ice_breakers[:4]  # Max 4 ice breakers
            }
            
            response = await self._client.post(
                f"/{self.instagram_account_id}/messenger_profile",
                json=payload
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error setting ice breakers: {e}")
            return False
    
    async def close(self):
        """Close HTTP client"""
        await self._client.aclose()


# Singleton instance
_instagram_service = None

def get_instagram_service() -> InstagramService:
    """Get singleton instance of InstagramService"""
    global _instagram_service
    if _instagram_service is None:
        _instagram_service = InstagramService()
    return _instagram_service
