"""
Push Notification Service using Firebase Cloud Messaging (FCM)

Enterprise-grade push notification service supporting:
- iOS and Android devices
- Web push notifications
- Topic-based messaging
- Device group messaging
- Scheduled notifications
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
import firebase_admin
from firebase_admin import credentials, messaging
from firebase_admin.exceptions import FirebaseError

from app.config import settings
from app.utils import logger


class PushNotificationService:
    """
    Firebase Cloud Messaging service for push notifications
    
    Features:
    - Multi-platform push (iOS, Android, Web)
    - Rich notifications with images and actions
    - Topic subscriptions
    - Device group targeting
    - Delivery tracking
    - Batch messaging
    """
    
    def __init__(self):
        self.app: Optional[firebase_admin.App] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize Firebase Admin SDK"""
        if self._initialized:
            return
        
        try:
            if not settings.firebase_credentials_path:
                logger.warning("Firebase credentials not configured")
                return
            
            # Initialize Firebase
            cred = credentials.Certificate(settings.firebase_credentials_path)
            self.app = firebase_admin.initialize_app(cred)
            
            logger.info("Firebase Cloud Messaging initialized successfully")
            self._initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}", exc_info=True)
            raise
    
    async def send_notification(
        self,
        token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
        image_url: Optional[str] = None,
        action_url: Optional[str] = None,
        badge_count: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Send push notification to a single device
        
        Args:
            token: FCM device token
            title: Notification title
            body: Notification body
            data: Custom data payload
            image_url: Optional image URL
            action_url: URL to open on tap
            badge_count: Badge count for iOS
        
        Returns:
            Dictionary with send status and message ID
        """
        if not self._initialized:
            await self.initialize()
        
        if not self.app:
            raise RuntimeError("Firebase not initialized")
        
        try:
            logger.info(f"Sending push notification to device: {token[:20]}...")
            
            # Build notification
            notification = messaging.Notification(
                title=title,
                body=body,
                image=image_url
            )
            
            # Build Android config
            android_config = messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    icon='stock_ticker_update',
                    color='#4CAF50',
                    sound='default',
                    click_action=action_url
                )
            )
            
            # Build iOS config
            apns_config = messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        badge=badge_count,
                        sound='default',
                        content_available=True
                    )
                )
            )
            
            # Build message
            message = messaging.Message(
                notification=notification,
                data=data or {},
                token=token,
                android=android_config,
                apns=apns_config
            )
            
            # Send message
            response = messaging.send(message)
            
            logger.info(f"Push notification sent successfully. Message ID: {response}")
            
            return {
                "status": "success",
                "message_id": response,
                "token": token[:20] + "...",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except FirebaseError as e:
            logger.error(f"Firebase push notification error: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "error_code": e.code if hasattr(e, 'code') else None,
                "token": token[:20] + "...",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Push notification error: {e}", exc_info=True)
            raise
    
    async def send_multicast(
        self,
        tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
        image_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send push notification to multiple devices
        
        Args:
            tokens: List of FCM device tokens (max 500)
            title: Notification title
            body: Notification body
            data: Custom data payload
            image_url: Optional image URL
        
        Returns:
            Dictionary with success/failure counts
        """
        if not self._initialized:
            await self.initialize()
        
        if not self.app:
            raise RuntimeError("Firebase not initialized")
        
        try:
            logger.info(f"Sending multicast push to {len(tokens)} devices")
            
            # Build notification
            notification = messaging.Notification(
                title=title,
                body=body,
                image=image_url
            )
            
            # Build multicast message
            message = messaging.MulticastMessage(
                notification=notification,
                data=data or {},
                tokens=tokens
            )
            
            # Send multicast
            batch_response = messaging.send_multicast(message)
            
            logger.info(
                f"Multicast sent: {batch_response.success_count} success, "
                f"{batch_response.failure_count} failed"
            )
            
            # Collect failed tokens
            failed_tokens = []
            if batch_response.failure_count > 0:
                for idx, response in enumerate(batch_response.responses):
                    if not response.success:
                        failed_tokens.append({
                            "token": tokens[idx][:20] + "...",
                            "error": str(response.exception)
                        })
            
            return {
                "status": "success",
                "total": len(tokens),
                "success_count": batch_response.success_count,
                "failure_count": batch_response.failure_count,
                "failed_tokens": failed_tokens,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except FirebaseError as e:
            logger.error(f"Firebase multicast error: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Multicast error: {e}", exc_info=True)
            raise
    
    async def send_to_topic(
        self,
        topic: str,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
        image_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send push notification to a topic
        
        Args:
            topic: FCM topic name
            title: Notification title
            body: Notification body
            data: Custom data payload
            image_url: Optional image URL
        
        Returns:
            Dictionary with send status
        """
        if not self._initialized:
            await self.initialize()
        
        if not self.app:
            raise RuntimeError("Firebase not initialized")
        
        try:
            logger.info(f"Sending push notification to topic: {topic}")
            
            # Build notification
            notification = messaging.Notification(
                title=title,
                body=body,
                image=image_url
            )
            
            # Build message
            message = messaging.Message(
                notification=notification,
                data=data or {},
                topic=topic
            )
            
            # Send to topic
            response = messaging.send(message)
            
            logger.info(f"Topic notification sent. Message ID: {response}")
            
            return {
                "status": "success",
                "message_id": response,
                "topic": topic,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except FirebaseError as e:
            logger.error(f"Firebase topic notification error: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "topic": topic,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Topic notification error: {e}", exc_info=True)
            raise
    
    async def subscribe_to_topic(
        self,
        tokens: List[str],
        topic: str
    ) -> Dict[str, Any]:
        """
        Subscribe devices to a topic
        
        Args:
            tokens: List of FCM device tokens
            topic: Topic name
        
        Returns:
            Dictionary with subscription results
        """
        if not self._initialized:
            await self.initialize()
        
        if not self.app:
            raise RuntimeError("Firebase not initialized")
        
        try:
            logger.info(f"Subscribing {len(tokens)} devices to topic: {topic}")
            
            response = messaging.subscribe_to_topic(tokens, topic)
            
            logger.info(
                f"Topic subscription: {response.success_count} success, "
                f"{response.failure_count} failed"
            )
            
            return {
                "status": "success",
                "topic": topic,
                "success_count": response.success_count,
                "failure_count": response.failure_count,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except FirebaseError as e:
            logger.error(f"Topic subscription error: {e}", exc_info=True)
            raise
    
    async def unsubscribe_from_topic(
        self,
        tokens: List[str],
        topic: str
    ) -> Dict[str, Any]:
        """
        Unsubscribe devices from a topic
        
        Args:
            tokens: List of FCM device tokens
            topic: Topic name
        
        Returns:
            Dictionary with unsubscription results
        """
        if not self._initialized:
            await self.initialize()
        
        if not self.app:
            raise RuntimeError("Firebase not initialized")
        
        try:
            logger.info(f"Unsubscribing {len(tokens)} devices from topic: {topic}")
            
            response = messaging.unsubscribe_from_topic(tokens, topic)
            
            logger.info(
                f"Topic unsubscription: {response.success_count} success, "
                f"{response.failure_count} failed"
            )
            
            return {
                "status": "success",
                "topic": topic,
                "success_count": response.success_count,
                "failure_count": response.failure_count,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except FirebaseError as e:
            logger.error(f"Topic unsubscription error: {e}", exc_info=True)
            raise


# Global push notification service instance
push_notification_service = PushNotificationService()
