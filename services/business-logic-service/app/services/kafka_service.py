"""
Kafka Event Streaming Service

Complete Kafka integration for event-driven architecture with:
- Event publishing (producer)
- Event consumption (consumer)
- Event schemas and validation
- Error handling and retry logic
- Dead letter queue support
"""

import logging
import json
import asyncio
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from enum import Enum

from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from aiokafka.errors import KafkaError
from confluent_kafka import Producer, Consumer, KafkaException
from confluent_kafka.admin import AdminClient, NewTopic

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EventType(str, Enum):
    """Event types for business logic"""
    # Order events
    ORDER_CREATED = "order.created"
    ORDER_UPDATED = "order.updated"
    ORDER_CONFIRMED = "order.confirmed"
    ORDER_PREPARING = "order.preparing"
    ORDER_READY = "order.ready"
    ORDER_COMPLETED = "order.completed"
    ORDER_CANCELLED = "order.cancelled"
    
    # Reservation events
    RESERVATION_CREATED = "reservation.created"
    RESERVATION_CONFIRMED = "reservation.confirmed"
    RESERVATION_UPDATED = "reservation.updated"
    RESERVATION_CANCELLED = "reservation.cancelled"
    RESERVATION_NO_SHOW = "reservation.no_show"
    
    # Inventory events
    INVENTORY_UPDATED = "inventory.updated"
    INVENTORY_LOW_STOCK = "inventory.low_stock"
    INVENTORY_OUT_OF_STOCK = "inventory.out_of_stock"
    INVENTORY_RESTOCKED = "inventory.restocked"
    
    # Payment events
    PAYMENT_INITIATED = "payment.initiated"
    PAYMENT_AUTHORIZED = "payment.authorized"
    PAYMENT_CAPTURED = "payment.captured"
    PAYMENT_FAILED = "payment.failed"
    PAYMENT_REFUNDED = "payment.refunded"


class Event(BaseModel):
    """Base event model"""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str = "business-logic-service"
    version: str = "1.0"
    tenant_id: Optional[str] = None
    business_id: Optional[str] = None
    data: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class KafkaService:
    """
    Complete Kafka service for event streaming
    
    Features:
    - Async producer for event publishing
    - Async consumer for event processing
    - Event schema validation
    - Automatic retry with exponential backoff
    - Dead letter queue for failed events
    - Topic management
    - Consumer group coordination
    """
    
    def __init__(self):
        self.producer: Optional[AIOKafkaProducer] = None
        self.consumers: Dict[str, AIOKafkaConsumer] = {}
        self.event_handlers: Dict[EventType, List[Callable]] = {}
        self.running = False
        
        # Topic configuration
        self.topics = {
            "orders": settings.KAFKA_TOPICS_ORDERS,
            "reservations": settings.KAFKA_TOPICS_RESERVATIONS,
            "inventory": settings.KAFKA_TOPICS_INVENTORY,
            "payments": settings.KAFKA_TOPICS_PAYMENTS,
            "dlq": "business-logic-dlq"  # Dead letter queue
        }
    
    async def start(self):
        """Initialize Kafka producer and consumers"""
        try:
            # Initialize producer
            self.producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(
                    v,
                    default=self._json_serializer
                ).encode('utf-8'),
                compression_type='gzip',
                max_batch_size=16384,
                linger_ms=10,
                acks='all',  # Wait for all replicas
                retries=3
            )
            await self.producer.start()
            logger.info("✅ Kafka producer started")
            
            # Create topics if they don't exist
            await self._create_topics()
            
            self.running = True
            logger.info("✅ Kafka service started successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to start Kafka service: {e}", exc_info=True)
            raise
    
    async def stop(self):
        """Shutdown Kafka connections"""
        self.running = False
        
        if self.producer:
            await self.producer.stop()
            logger.info("Kafka producer stopped")
        
        for consumer in self.consumers.values():
            await consumer.stop()
        logger.info("All Kafka consumers stopped")
    
    async def publish_event(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        tenant_id: Optional[str] = None,
        business_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Publish event to Kafka
        
        Args:
            event_type: Type of event
            data: Event payload
            tenant_id: Tenant identifier
            business_id: Business identifier
            metadata: Additional metadata
        
        Returns:
            bool: True if published successfully
        """
        try:
            if not self.producer:
                logger.warning("Kafka producer not initialized, skipping event")
                return False
            
            # Create event
            event = Event(
                event_type=event_type,
                tenant_id=tenant_id,
                business_id=business_id,
                data=data,
                metadata=metadata or {}
            )
            
            # Determine topic
            topic = self._get_topic_for_event(event_type)
            
            # Publish to Kafka
            await self.producer.send_and_wait(
                topic,
                value=event.dict(),
                key=business_id.encode('utf-8') if business_id else None
            )
            
            logger.info(
                f"Published event {event_type.value} to topic {topic}",
                extra={
                    "event_id": event.event_id,
                    "tenant_id": tenant_id,
                    "business_id": business_id
                }
            )
            
            return True
            
        except KafkaError as e:
            logger.error(f"Kafka error publishing event: {e}", exc_info=True)
            # Send to DLQ
            await self._send_to_dlq(event_type, data, str(e))
            return False
        except Exception as e:
            logger.error(f"Error publishing event: {e}", exc_info=True)
            return False
    
    async def subscribe(
        self,
        event_types: List[EventType],
        handler: Callable,
        consumer_group: Optional[str] = None
    ):
        """
        Subscribe to event types and register handler
        
        Args:
            event_types: List of event types to subscribe to
            handler: Async function to handle events
            consumer_group: Consumer group ID
        """
        try:
            # Register handler
            for event_type in event_types:
                if event_type not in self.event_handlers:
                    self.event_handlers[event_type] = []
                self.event_handlers[event_type].append(handler)
            
            # Determine topics
            topics = list(set(
                self._get_topic_for_event(et) for et in event_types
            ))
            
            # Create consumer
            group_id = consumer_group or settings.KAFKA_CONSUMER_GROUP
            consumer = AIOKafkaConsumer(
                *topics,
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                group_id=group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                auto_commit_interval_ms=1000
            )
            
            await consumer.start()
            self.consumers[group_id] = consumer
            
            logger.info(
                f"Subscribed to events {[et.value for et in event_types]} "
                f"on topics {topics} with group {group_id}"
            )
            
            # Start consuming
            asyncio.create_task(self._consume_events(consumer))
            
        except Exception as e:
            logger.error(f"Error subscribing to events: {e}", exc_info=True)
            raise
    
    async def _consume_events(self, consumer: AIOKafkaConsumer):
        """Consume events from Kafka"""
        try:
            async for msg in consumer:
                try:
                    event_data = msg.value
                    event_type = EventType(event_data.get("event_type"))
                    
                    # Get handlers for this event type
                    handlers = self.event_handlers.get(event_type, [])
                    
                    # Execute handlers
                    for handler in handlers:
                        try:
                            await handler(event_data)
                        except Exception as e:
                            logger.error(
                                f"Error in event handler for {event_type}: {e}",
                                exc_info=True
                            )
                            # Send to DLQ
                            await self._send_to_dlq(
                                event_type,
                                event_data,
                                f"Handler error: {str(e)}"
                            )
                    
                except Exception as e:
                    logger.error(f"Error processing event: {e}", exc_info=True)
                    
        except Exception as e:
            logger.error(f"Consumer error: {e}", exc_info=True)
            if self.running:
                # Restart consumer
                logger.info("Restarting consumer...")
                await asyncio.sleep(5)
                await consumer.start()
                asyncio.create_task(self._consume_events(consumer))
    
    async def _create_topics(self):
        """Create Kafka topics if they don't exist"""
        try:
            admin_client = AdminClient({
                'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS
            })
            
            # Get existing topics
            metadata = admin_client.list_topics(timeout=10)
            existing_topics = set(metadata.topics.keys())
            
            # Create missing topics
            new_topics = []
            for topic in self.topics.values():
                if topic not in existing_topics:
                    new_topics.append(
                        NewTopic(
                            topic=topic,
                            num_partitions=3,
                            replication_factor=1
                        )
                    )
            
            if new_topics:
                fs = admin_client.create_topics(new_topics)
                for topic, f in fs.items():
                    try:
                        f.result()
                        logger.info(f"Created topic: {topic}")
                    except Exception as e:
                        logger.warning(f"Topic {topic} creation warning: {e}")
            
        except Exception as e:
            logger.warning(f"Error creating topics: {e}")
    
    def _get_topic_for_event(self, event_type: EventType) -> str:
        """Get Kafka topic for event type"""
        if "order" in event_type.value:
            return self.topics["orders"]
        elif "reservation" in event_type.value:
            return self.topics["reservations"]
        elif "inventory" in event_type.value:
            return self.topics["inventory"]
        elif "payment" in event_type.value:
            return self.topics["payments"]
        else:
            return self.topics["orders"]  # Default
    
    async def _send_to_dlq(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        error: str
    ):
        """Send failed event to dead letter queue"""
        try:
            dlq_event = {
                "original_event_type": event_type.value,
                "data": data,
                "error": error,
                "timestamp": datetime.utcnow().isoformat(),
                "retry_count": 0
            }
            
            if self.producer:
                await self.producer.send_and_wait(
                    self.topics["dlq"],
                    value=dlq_event
                )
                logger.info(f"Sent event to DLQ: {event_type.value}")
                
        except Exception as e:
            logger.error(f"Error sending to DLQ: {e}")
    
    @staticmethod
    def _json_serializer(obj):
        """JSON serializer for complex objects"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, Enum):
            return obj.value
        raise TypeError(f"Type {type(obj)} not serializable")


# Import at the end to avoid circular imports
from pydantic import BaseModel, Field
from decimal import Decimal
import uuid


# Singleton instance
_kafka_service: Optional[KafkaService] = None


def get_kafka_service() -> KafkaService:
    """Get Kafka service singleton"""
    global _kafka_service
    if _kafka_service is None:
        _kafka_service = KafkaService()
    return _kafka_service
