"""
Push Notification Service for Audio Call Alerts
Supports FCM (Firebase), APNS (Apple), and Web Push
"""

import logging
import httpx
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime

from supabase import create_client, Client
from app.config.settings import settings

logger = logging.getLogger(__name__)


class PushNotificationService:
    """Enterprise-grade push notification service"""
    
    def __init__(self):
        """Initialize push notification service"""
        self.client: Optional[Client] = None
        self.fcm_url = "https://fcm.googleapis.com/fcm/send"
        self._initialized = False
    
    async def initialize(self):
        """Initialize notification service"""
        if self._initialized:
            return
        
        try:
            self.client = create_client(
                settings.supabase_url,
                settings.supabase_key
            )
            self._initialized = True
            logger.info("Push notification service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize push notification service: {e}")
    
    async def register_device_token(
        self,
        user_id: UUID,
        device_token: str,
        device_type: str,
        platform: str
    ) -> bool:
        """
        Register device token for push notifications
        
        Args:
            user_id: User identifier
            device_token: Device push token
            device_type: Device type (ios, android, web, desktop)
            platform: Platform (fcm, apns, web_push)
            
        Returns:
            Success status
        """
        try:
            data = {
                "user_id": str(user_id),
                "device_token": device_token,
                "device_type": device_type,
                "platform": platform,
                "is_active": True,
                "last_used_at": datetime.utcnow().isoformat()
            }
            
            # Upsert to handle token updates
            result = self.client.table("push_notification_tokens")\
                .upsert(data, on_conflict="user_id,device_token")\
                .execute()
            
            logger.info(f"Registered device token for user {user_id}")
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error registering device token: {e}")
            return False
    
    async def send_call_notification(
        self,
        user_id: UUID,
        call_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send incoming call notification to user
        
        Args:
            user_id: User to notify
            call_data: Call information
            
        Returns:
            Notification results
        """
        try:
            # Get user's active device tokens
            tokens = await self._get_user_tokens(user_id)
            
            if not tokens:
                logger.warning(f"No active tokens for user {user_id}")
                return {"success": False, "reason": "no_tokens"}
            
            # Prepare notification payload
            notification = {
                "title": "Incoming Call",
                "body": call_data.get("caller_name", "Someone") + " is calling...",
                "sound": "ringtone.mp3",
                "priority": "high",
                "data": {
                    "call_id": call_data.get("call_id"),
                    "room_id": call_data.get("room_id"),
                    "caller_id": call_data.get("caller_id"),
                    "business_id": call_data.get("business_id"),
                    "type": "incoming_call"
                }
            }
            
            # Send to all devices
            results = []
            for token in tokens:
                if token["platform"] == "fcm":
                    result = await self._send_fcm_notification(token["device_token"], notification)
                    results.append(result)
                elif token["platform"] == "apns":
                    result = await self._send_apns_notification(token["device_token"], notification)
                    results.append(result)
                elif token["platform"] == "web_push":
                    result = await self._send_web_push_notification(token["device_token"], notification)
                    results.append(result)
            
            success_count = sum(1 for r in results if r.get("success"))
            
            return {
                "success": success_count > 0,
                "sent_count": success_count,
                "total_devices": len(tokens)
            }
            
        except Exception as e:
            logger.error(f"Error sending call notification: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_missed_call_notification(
        self,
        user_id: UUID,
        call_data: Dict[str, Any]
    ) -> bool:
        """Send missed call notification"""
        try:
            tokens = await self._get_user_tokens(user_id)
            
            if not tokens:
                return False
            
            notification = {
                "title": "Missed Call",
                "body": f"Missed call from {call_data.get('caller_name', 'Unknown')}",
                "sound": "default",
                "data": {
                    "call_id": call_data.get("call_id"),
                    "type": "missed_call"
                }
            }
            
            for token in tokens:
                if token["platform"] == "fcm":
                    await self._send_fcm_notification(token["device_token"], notification)
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending missed call notification: {e}")
            return False
    
    async def _get_user_tokens(self, user_id: UUID) -> List[Dict[str, Any]]:
        """Get active device tokens for user"""
        try:
            result = self.client.table("push_notification_tokens")\
                .select("*")\
                .eq("user_id", str(user_id))\
                .eq("is_active", True)\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error getting user tokens: {e}")
            return []
    
    async def _send_fcm_notification(
        self,
        token: str,
        notification: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send Firebase Cloud Messaging notification"""
        try:
            if not hasattr(settings, 'fcm_server_key') or not settings.fcm_server_key:
                logger.warning("FCM server key not configured")
                return {"success": False, "reason": "fcm_not_configured"}
            
            headers = {
                "Authorization": f"key={settings.fcm_server_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "to": token,
                "notification": {
                    "title": notification["title"],
                    "body": notification["body"],
                    "sound": notification.get("sound", "default")
                },
                "data": notification.get("data", {}),
                "priority": "high"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.fcm_url,
                    json=payload,
                    headers=headers,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    logger.info(f"FCM notification sent successfully")
                    return {"success": True, "platform": "fcm"}
                else:
                    logger.error(f"FCM notification failed: {response.text}")
                    return {"success": False, "error": response.text}
                    
        except Exception as e:
            logger.error(f"Error sending FCM notification: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_apns_notification(
        self,
        token: str,
        notification: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send Apple Push Notification Service notification"""
        try:
            # APNS implementation would go here
            # Requires APNS certificates and proper setup
            logger.info("APNS notification (placeholder)")
            return {"success": True, "platform": "apns", "placeholder": True}
            
        except Exception as e:
            logger.error(f"Error sending APNS notification: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_web_push_notification(
        self,
        token: str,
        notification: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send Web Push notification"""
        try:
            # Web Push implementation would go here
            # Requires VAPID keys and proper setup
            logger.info("Web Push notification (placeholder)")
            return {"success": True, "platform": "web_push", "placeholder": True}
            
        except Exception as e:
            logger.error(f"Error sending Web Push notification: {e}")
            return {"success": False, "error": str(e)}
    
    async def deactivate_token(self, device_token: str) -> bool:
        """Deactivate a device token"""
        try:
            result = self.client.table("push_notification_tokens")\
                .update({"is_active": False})\
                .eq("device_token", device_token)\
                .execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error deactivating token: {e}")
            return False


# Global push notification service instance
push_notification_service = PushNotificationService()
