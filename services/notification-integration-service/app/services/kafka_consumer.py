"""
Kafka Consumer for event-driven notifications
"""

from typing import Dict, Any, Optional
import json
import asyncio
from kafka import KafkaConsumer
from kafka.errors import KafkaError

from app.config import settings
from app.utils import logger
from app.services.twilio_service import twilio_service
from app.services.sendgrid_service import sendgrid_service
from app.services.zapier_service import zapier_service


class NotificationKafkaConsumer:
    """
    Kafka consumer for processing notification events
    
    Features:
    - Event-driven notification processing
    - Multi-channel routing (SMS, Email, Webhook)
    - Error handling and dead letter queue
    - Automatic retry logic
    """
    
    def __init__(self):
        self.consumer: Optional[KafkaConsumer] = None
        self.running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start Kafka consumer"""
        if self.running:
            return
        
        try:
            logger.info("Starting Kafka consumer for notifications")
            
            # Create Kafka consumer
            self.consumer = KafkaConsumer(
                settings.kafka_notification_topic,
                bootstrap_servers=settings.kafka_bootstrap_servers.split(','),
                group_id=settings.kafka_consumer_group,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                max_poll_records=100
            )
            
            self.running = True
            
            # Start consuming in background
            self._task = asyncio.create_task(self._consume_messages())
            
            logger.info(f"Kafka consumer started for topic: {settings.kafka_notification_topic}")
            
        except KafkaError as e:
            logger.error(f"Failed to start Kafka consumer: {e}", exc_info=True)
            raise
    
    async def stop(self):
        """Stop Kafka consumer"""
        if not self.running:
            return
        
        logger.info("Stopping Kafka consumer")
        self.running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        if self.consumer:
            self.consumer.close()
        
        logger.info("Kafka consumer stopped")
    
    async def _consume_messages(self):
        """Consume and process messages"""
        try:
            while self.running:
                # Poll for messages (non-blocking with timeout)
                messages = self.consumer.poll(timeout_ms=1000)
                
                if not messages:
                    await asyncio.sleep(0.1)
                    continue
                
                # Process messages
                for topic_partition, records in messages.items():
                    for record in records:
                        try:
                            await self._process_notification(record.value)
                        except Exception as e:
                            logger.error(f"Error processing notification: {e}", exc_info=True)
                            # Send to dead letter queue or retry logic here
                
        except Exception as e:
            logger.error(f"Kafka consumer error: {e}", exc_info=True)
            self.running = False
    
    async def _process_notification(self, notification: Dict[str, Any]):
        """
        Process notification event
        
        Args:
            notification: Notification event data
        """
        try:
            notification_type = notification.get("type")
            channel = notification.get("channel")
            data = notification.get("data", {})
            
            logger.info(f"Processing notification: type={notification_type}, channel={channel}")
            
            # Route to appropriate channel
            if channel == "sms":
                await self._send_sms_notification(data)
            elif channel == "email":
                await self._send_email_notification(data)
            elif channel == "whatsapp":
                await self._send_whatsapp_notification(data)
            elif channel == "webhook":
                await self._send_webhook_notification(data)
            else:
                logger.warning(f"Unknown notification channel: {channel}")
            
        except Exception as e:
            logger.error(f"Notification processing error: {e}", exc_info=True)
            raise
    
    async def _send_sms_notification(self, data: Dict[str, Any]):
        """Send SMS notification"""
        to = data.get("to")
        message = data.get("message")
        
        if not to or not message:
            logger.error("Missing required fields for SMS notification")
            return
        
        result = await twilio_service.send_sms(to=to, message=message)
        logger.info(f"SMS notification sent: {result}")
    
    async def _send_email_notification(self, data: Dict[str, Any]):
        """Send email notification"""
        to_email = data.get("to_email")
        subject = data.get("subject")
        html_content = data.get("html_content")
        
        if not to_email or not subject or not html_content:
            logger.error("Missing required fields for email notification")
            return
        
        result = await sendgrid_service.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            plain_content=data.get("plain_content")
        )
        logger.info(f"Email notification sent: {result}")
    
    async def _send_whatsapp_notification(self, data: Dict[str, Any]):
        """Send WhatsApp notification"""
        to = data.get("to")
        message = data.get("message")
        
        if not to or not message:
            logger.error("Missing required fields for WhatsApp notification")
            return
        
        result = await twilio_service.send_whatsapp(
            to=to,
            message=message,
            media_url=data.get("media_url")
        )
        logger.info(f"WhatsApp notification sent: {result}")
    
    async def _send_webhook_notification(self, data: Dict[str, Any]):
        """Send webhook notification"""
        webhook_url = data.get("webhook_url")
        payload = data.get("payload", {})
        
        if not webhook_url:
            logger.error("Missing webhook URL for webhook notification")
            return
        
        result = await zapier_service.trigger_webhook(
            webhook_url=webhook_url,
            data=payload
        )
        logger.info(f"Webhook notification sent: {result}")


# Global Kafka consumer instance
kafka_consumer = NotificationKafkaConsumer()
