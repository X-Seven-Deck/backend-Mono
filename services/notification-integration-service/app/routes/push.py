"""
Push notification endpoints
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from app.services.push_notification_service import push_notification_service
from app.utils import logger

router = APIRouter()


class PushNotificationRequest(BaseModel):
    """Push notification request"""
    token: str = Field(..., description="FCM device token")
    title: str = Field(..., description="Notification title")
    body: str = Field(..., description="Notification body")
    data: Optional[Dict[str, str]] = Field(None, description="Custom data payload")
    image_url: Optional[str] = Field(None, description="Image URL")
    action_url: Optional[str] = Field(None, description="Action URL on tap")
    badge_count: Optional[int] = Field(None, description="Badge count for iOS")


class MulticastPushRequest(BaseModel):
    """Multicast push notification request"""
    tokens: List[str] = Field(..., description="List of FCM device tokens (max 500)")
    title: str = Field(..., description="Notification title")
    body: str = Field(..., description="Notification body")
    data: Optional[Dict[str, str]] = Field(None, description="Custom data payload")
    image_url: Optional[str] = Field(None, description="Image URL")


class TopicPushRequest(BaseModel):
    """Topic push notification request"""
    topic: str = Field(..., description="FCM topic name")
    title: str = Field(..., description="Notification title")
    body: str = Field(..., description="Notification body")
    data: Optional[Dict[str, str]] = Field(None, description="Custom data payload")
    image_url: Optional[str] = Field(None, description="Image URL")


class TopicSubscriptionRequest(BaseModel):
    """Topic subscription request"""
    tokens: List[str] = Field(..., description="Device tokens to subscribe")
    topic: str = Field(..., description="Topic name")


@router.post("/send")
async def send_push_notification(request: PushNotificationRequest):
    """
    Send push notification to a single device
    
    Sends push notification via Firebase Cloud Messaging
    """
    try:
        logger.info(f"Push notification request for token: {request.token[:20]}...")
        
        result = await push_notification_service.send_notification(
            token=request.token,
            title=request.title,
            body=request.body,
            data=request.data,
            image_url=request.image_url,
            action_url=request.action_url,
            badge_count=request.badge_count
        )
        
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Push notification error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/multicast")
async def send_multicast_push(request: MulticastPushRequest):
    """
    Send push notification to multiple devices
    
    Sends to up to 500 devices in a single request
    """
    try:
        if len(request.tokens) > 500:
            raise HTTPException(
                status_code=400,
                detail="Maximum 500 tokens allowed per request"
            )
        
        logger.info(f"Multicast push request for {len(request.tokens)} devices")
        
        result = await push_notification_service.send_multicast(
            tokens=request.tokens,
            title=request.title,
            body=request.body,
            data=request.data,
            image_url=request.image_url
        )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Multicast push error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/topic")
async def send_topic_push(request: TopicPushRequest):
    """
    Send push notification to a topic
    
    All devices subscribed to the topic will receive the notification
    """
    try:
        logger.info(f"Topic push request for topic: {request.topic}")
        
        result = await push_notification_service.send_to_topic(
            topic=request.topic,
            title=request.title,
            body=request.body,
            data=request.data,
            image_url=request.image_url
        )
        
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Topic push error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/topic/subscribe")
async def subscribe_to_topic(request: TopicSubscriptionRequest):
    """
    Subscribe devices to a topic
    
    Allows devices to receive topic-based notifications
    """
    try:
        logger.info(f"Subscribing {len(request.tokens)} devices to topic: {request.topic}")
        
        result = await push_notification_service.subscribe_to_topic(
            tokens=request.tokens,
            topic=request.topic
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Topic subscription error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/topic/unsubscribe")
async def unsubscribe_from_topic(request: TopicSubscriptionRequest):
    """
    Unsubscribe devices from a topic
    
    Removes devices from topic subscriptions
    """
    try:
        logger.info(f"Unsubscribing {len(request.tokens)} devices from topic: {request.topic}")
        
        result = await push_notification_service.unsubscribe_from_topic(
            tokens=request.tokens,
            topic=request.topic
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Topic unsubscription error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
