"""
Kafka Event Publisher for Chat Communication

Publishes events for analytics, monitoring, and cross-service communication.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError

logger = logging.getLogger(__name__)


class EventPublisher:
    """
    Kafka Event Publisher
    
    Features:
    - Message events
    - Session events
    - User activity events
    - Analytics events
    - System events
    """
    
    def __init__(self):
        self._initialized = False
        self.producer: Optional[AIOKafkaProducer] = None
        
        # Configuration
        self.bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        
        # Topic names
        self.topics = {
            "messages": os.getenv("KAFKA_TOPIC_MESSAGES", "chat-messages"),
            "sessions": os.getenv("KAFKA_TOPIC_SESSIONS", "chat-sessions"),
            "activity": os.getenv("KAFKA_TOPIC_ACTIVITY", "user-activity"),
            "analytics": os.getenv("KAFKA_TOPIC_ANALYTICS", "chat-analytics"),
            "system": os.getenv("KAFKA_TOPIC_SYSTEM", "system-events")
        }
    
    async def initialize(self):
        """Initialize Kafka producer"""
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                compression_type='gzip',
                acks='all',  # Wait for all replicas
                retries=3
            )
            
            await self.producer.start()
            
            self._initialized = True
            logger.info("Event publisher initialized successfully")
            
        except Exception as e:
            logger.warning(f"Failed to initialize event publisher: {e}")
            # Don't raise - service can work without Kafka
    
    # ============================================================================
    # MESSAGE EVENTS
    # ============================================================================
    
    async def publish_message_sent(
        self,
        session_id: str,
        message_id: str,
        business_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Publish message sent event"""
        try:
            event = {
                "event_type": "message_sent",
                "session_id": session_id,
                "message_id": message_id,
                "business_id": business_id,
                "role": role,
                "content_length": len(content),
                "metadata": metadata or {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return await self._publish(self.topics["messages"], event, session_id)
            
        except Exception as e:
            logger.error(f"Error publishing message sent event: {e}")
            return False
    
    async def publish_message_received(
        self,
        session_id: str,
        message_id: str,
        business_id: str,
        user_id: str,
        channel: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Publish message received event"""
        try:
            event = {
                "event_type": "message_received",
                "session_id": session_id,
                "message_id": message_id,
                "business_id": business_id,
                "user_id": user_id,
                "channel": channel,
                "metadata": metadata or {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return await self._publish(self.topics["messages"], event, session_id)
            
        except Exception as e:
            logger.error(f"Error publishing message received event: {e}")
            return False
    
    async def publish_ai_response_generated(
        self,
        session_id: str,
        message_id: str,
        business_id: str,
        model: str,
        tokens_used: int,
        processing_time: float,
        intent: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Publish AI response generated event"""
        try:
            event = {
                "event_type": "ai_response_generated",
                "session_id": session_id,
                "message_id": message_id,
                "business_id": business_id,
                "model": model,
                "tokens_used": tokens_used,
                "processing_time_ms": processing_time * 1000,
                "intent": intent,
                "metadata": metadata or {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return await self._publish(self.topics["messages"], event, session_id)
            
        except Exception as e:
            logger.error(f"Error publishing AI response event: {e}")
            return False
    
    # ============================================================================
    # SESSION EVENTS
    # ============================================================================
    
    async def publish_session_created(
        self,
        session_id: str,
        session_type: str,
        business_id: str,
        user_id: Optional[str] = None,
        channel: str = "web",
        metadata: Optional[Dict] = None
    ) -> bool:
        """Publish session created event"""
        try:
            event = {
                "event_type": "session_created",
                "session_id": session_id,
                "session_type": session_type,
                "business_id": business_id,
                "user_id": user_id,
                "channel": channel,
                "metadata": metadata or {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return await self._publish(self.topics["sessions"], event, session_id)
            
        except Exception as e:
            logger.error(f"Error publishing session created event: {e}")
            return False
    
    async def publish_session_closed(
        self,
        session_id: str,
        business_id: str,
        duration_seconds: float,
        message_count: int,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Publish session closed event"""
        try:
            event = {
                "event_type": "session_closed",
                "session_id": session_id,
                "business_id": business_id,
                "duration_seconds": duration_seconds,
                "message_count": message_count,
                "metadata": metadata or {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return await self._publish(self.topics["sessions"], event, session_id)
            
        except Exception as e:
            logger.error(f"Error publishing session closed event: {e}")
            return False
    
    async def publish_agent_handover(
        self,
        session_id: str,
        business_id: str,
        from_agent: str,  # 'ai' or agent_id
        to_agent: str,  # 'ai' or agent_id
        reason: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Publish agent handover event"""
        try:
            event = {
                "event_type": "agent_handover",
                "session_id": session_id,
                "business_id": business_id,
                "from_agent": from_agent,
                "to_agent": to_agent,
                "reason": reason,
                "metadata": metadata or {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return await self._publish(self.topics["sessions"], event, session_id)
            
        except Exception as e:
            logger.error(f"Error publishing handover event: {e}")
            return False
    
    # ============================================================================
    # USER ACTIVITY EVENTS
    # ============================================================================
    
    async def publish_user_joined(
        self,
        session_id: str,
        user_id: str,
        business_id: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Publish user joined event"""
        try:
            event = {
                "event_type": "user_joined",
                "session_id": session_id,
                "user_id": user_id,
                "business_id": business_id,
                "metadata": metadata or {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return await self._publish(self.topics["activity"], event, user_id)
            
        except Exception as e:
            logger.error(f"Error publishing user joined event: {e}")
            return False
    
    async def publish_user_left(
        self,
        session_id: str,
        user_id: str,
        business_id: str,
        duration_seconds: float,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Publish user left event"""
        try:
            event = {
                "event_type": "user_left",
                "session_id": session_id,
                "user_id": user_id,
                "business_id": business_id,
                "duration_seconds": duration_seconds,
                "metadata": metadata or {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return await self._publish(self.topics["activity"], event, user_id)
            
        except Exception as e:
            logger.error(f"Error publishing user left event: {e}")
            return False
    
    async def publish_user_typing(
        self,
        session_id: str,
        user_id: str,
        business_id: str,
        is_typing: bool
    ) -> bool:
        """Publish user typing indicator event"""
        try:
            event = {
                "event_type": "user_typing",
                "session_id": session_id,
                "user_id": user_id,
                "business_id": business_id,
                "is_typing": is_typing,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return await self._publish(self.topics["activity"], event, user_id)
            
        except Exception as e:
            logger.error(f"Error publishing typing event: {e}")
            return False
    
    # ============================================================================
    # ANALYTICS EVENTS
    # ============================================================================
    
    async def publish_analytics_event(
        self,
        business_id: str,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> bool:
        """Publish analytics event"""
        try:
            event = {
                "event_type": event_type,
                "business_id": business_id,
                "event_data": event_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return await self._publish(self.topics["analytics"], event, business_id)
            
        except Exception as e:
            logger.error(f"Error publishing analytics event: {e}")
            return False
    
    async def publish_intent_classified(
        self,
        business_id: str,
        session_id: str,
        intent: str,
        confidence: float,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Publish intent classification event"""
        try:
            event = {
                "event_type": "intent_classified",
                "business_id": business_id,
                "session_id": session_id,
                "intent": intent,
                "confidence": confidence,
                "metadata": metadata or {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return await self._publish(self.topics["analytics"], event, business_id)
            
        except Exception as e:
            logger.error(f"Error publishing intent event: {e}")
            return False
    
    async def publish_sentiment_analyzed(
        self,
        business_id: str,
        session_id: str,
        sentiment: str,
        score: float,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Publish sentiment analysis event"""
        try:
            event = {
                "event_type": "sentiment_analyzed",
                "business_id": business_id,
                "session_id": session_id,
                "sentiment": sentiment,
                "score": score,
                "metadata": metadata or {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return await self._publish(self.topics["analytics"], event, business_id)
            
        except Exception as e:
            logger.error(f"Error publishing sentiment event: {e}")
            return False
    
    # ============================================================================
    # SYSTEM EVENTS
    # ============================================================================
    
    async def publish_system_event(
        self,
        event_type: str,
        severity: str,  # info, warning, error, critical
        message: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Publish system event"""
        try:
            event = {
                "event_type": event_type,
                "severity": severity,
                "message": message,
                "service": "chat-communication-service",
                "metadata": metadata or {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return await self._publish(self.topics["system"], event)
            
        except Exception as e:
            logger.error(f"Error publishing system event: {e}")
            return False
    
    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    
    async def _publish(
        self,
        topic: str,
        event: Dict[str, Any],
        key: Optional[str] = None
    ) -> bool:
        """Publish event to Kafka topic"""
        if not self._initialized or not self.producer:
            logger.warning("Event publisher not initialized, skipping event")
            return False
        
        try:
            # Convert key to bytes if provided
            key_bytes = key.encode('utf-8') if key else None
            
            # Send to Kafka
            await self.producer.send(
                topic,
                value=event,
                key=key_bytes
            )
            
            return True
            
        except KafkaError as e:
            logger.error(f"Kafka error publishing event: {e}")
            return False
        except Exception as e:
            logger.error(f"Error publishing event: {e}")
            return False
    
    async def flush(self):
        """Flush pending messages"""
        if self.producer:
            await self.producer.flush()
    
    async def close(self):
        """Close Kafka producer"""
        if self.producer:
            await self.producer.stop()
            logger.info("Event publisher closed")


# Singleton instance
event_publisher = EventPublisher()

