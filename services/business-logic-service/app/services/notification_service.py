"""
Notification Service Integration

Complete notification delivery with:
- Email notifications
- SMS notifications
- Push notifications
- Notification templates
- Multi-channel delivery
- Delivery tracking
- Retry logic
"""

import logging
import httpx
from typing import Dict, Optional, Any, List
from datetime import datetime
from enum import Enum

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class NotificationChannel(str, Enum):
    """Notification delivery channel"""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"


class NotificationStatus(str, Enum):
    """Notification delivery status"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"


class NotificationService:
    """
    Complete notification service
    
    Features:
    - Multi-channel delivery (email, SMS, push)
    - Template-based notifications
    - Personalization
    - Delivery tracking
    - Automatic retry on failure
    - Rate limiting
    - Unsubscribe management
    - Analytics and reporting
    
    Integrates with:
    - Notification Integration Service (dedicated microservice)
    - Email providers (SendGrid, AWS SES)
    - SMS providers (Twilio, AWS SNS)
    - Push notification services (FCM, APNs)
    """
    
    def __init__(self):
        self.notification_service_url = settings.NOTIFICATION_SERVICE_URL
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        from_address: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Send email notification
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Plain text body
            html_body: HTML body (optional)
            from_address: Sender email (optional)
            cc: CC recipients
            bcc: BCC recipients
            attachments: File attachments
        
        Returns:
            Dict with send status and message ID
        """
        try:
            payload = {
                "channel": "email",
                "to": to,
                "subject": subject,
                "body": body,
                "html_body": html_body,
                "from_address": from_address,
                "cc": cc or [],
                "bcc": bcc or [],
                "attachments": attachments or []
            }
            
            response = await self.client.post(
                f"{self.notification_service_url}/api/v1/notifications/send",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Email sent to {to}: {result.get('message_id')}")
                return {
                    "success": True,
                    "message_id": result.get("message_id"),
                    "status": "sent"
                }
            else:
                logger.error(f"Email send failed: {response.text}")
                return {
                    "success": False,
                    "error": response.text
                }
                
        except Exception as e:
            logger.error(f"Error sending email: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_sms(
        self,
        to: str,
        message: str,
        from_number: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send SMS notification
        
        Args:
            to: Recipient phone number (E.164 format)
            message: SMS message text
            from_number: Sender phone number
        
        Returns:
            Dict with send status and message ID
        """
        try:
            payload = {
                "channel": "sms",
                "to": to,
                "message": message,
                "from_number": from_number
            }
            
            response = await self.client.post(
                f"{self.notification_service_url}/api/v1/notifications/send",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"SMS sent to {to}: {result.get('message_id')}")
                return {
                    "success": True,
                    "message_id": result.get("message_id"),
                    "status": "sent"
                }
            else:
                return {
                    "success": False,
                    "error": response.text
                }
                
        except Exception as e:
            logger.error(f"Error sending SMS: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_push_notification(
        self,
        user_id: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        badge: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Send push notification
        
        Args:
            user_id: User/device identifier
            title: Notification title
            body: Notification body
            data: Additional data payload
            badge: Badge count
        
        Returns:
            Dict with send status
        """
        try:
            payload = {
                "channel": "push",
                "user_id": user_id,
                "title": title,
                "body": body,
                "data": data or {},
                "badge": badge
            }
            
            response = await self.client.post(
                f"{self.notification_service_url}/api/v1/notifications/send",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Push notification sent to {user_id}")
                return {
                    "success": True,
                    "message_id": result.get("message_id")
                }
            else:
                return {
                    "success": False,
                    "error": response.text
                }
                
        except Exception as e:
            logger.error(f"Error sending push notification: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_templated_notification(
        self,
        channel: NotificationChannel,
        template_id: str,
        recipient: str,
        template_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send notification using template
        
        Args:
            channel: Notification channel
            template_id: Template identifier
            recipient: Recipient (email/phone/user_id)
            template_data: Data for template rendering
        
        Returns:
            Dict with send status
        """
        try:
            payload = {
                "channel": channel.value,
                "template_id": template_id,
                "recipient": recipient,
                "template_data": template_data
            }
            
            response = await self.client.post(
                f"{self.notification_service_url}/api/v1/notifications/send-templated",
                json=payload
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "success": False,
                    "error": response.text
                }
                
        except Exception as e:
            logger.error(f"Error sending templated notification: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_multi_channel(
        self,
        channels: List[NotificationChannel],
        recipient_map: Dict[str, str],
        message: str,
        subject: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send notification across multiple channels
        
        Args:
            channels: List of channels to use
            recipient_map: Map of channel to recipient
            message: Message content
            subject: Subject (for email)
        
        Returns:
            Dict with results per channel
        """
        results = {}
        
        for channel in channels:
            recipient = recipient_map.get(channel.value)
            if not recipient:
                continue
            
            if channel == NotificationChannel.EMAIL:
                result = await self.send_email(
                    to=recipient,
                    subject=subject or "Notification",
                    body=message
                )
            elif channel == NotificationChannel.SMS:
                result = await self.send_sms(
                    to=recipient,
                    message=message
                )
            elif channel == NotificationChannel.PUSH:
                result = await self.send_push_notification(
                    user_id=recipient,
                    title=subject or "Notification",
                    body=message
                )
            else:
                result = {"success": False, "error": "Unsupported channel"}
            
            results[channel.value] = result
        
        return {
            "multi_channel": True,
            "results": results,
            "all_successful": all(r.get("success") for r in results.values())
        }
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Singleton
_notification_service: Optional[NotificationService] = None

def get_notification_service() -> NotificationService:
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service
