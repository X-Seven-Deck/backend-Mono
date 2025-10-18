"""
Twilio Service for SMS and WhatsApp notifications
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from app.config import settings
from app.utils import logger


class TwilioService:
    """
    Enterprise-grade Twilio service for SMS and WhatsApp
    
    Features:
    - SMS delivery with delivery tracking
    - WhatsApp Business API integration
    - Bulk messaging support
    - Rate limiting and retry logic
    - Delivery status webhooks
    """
    
    def __init__(self):
        self.client: Optional[Client] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize Twilio client"""
        if self._initialized:
            return
        
        try:
            if not settings.twilio_account_sid or not settings.twilio_auth_token:
                logger.warning("Twilio credentials not configured")
                return
            
            self.client = Client(
                settings.twilio_account_sid,
                settings.twilio_auth_token
            )
            
            # Verify credentials
            account = self.client.api.accounts(settings.twilio_account_sid).fetch()
            logger.info(f"Twilio initialized for account: {account.friendly_name}")
            
            self._initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize Twilio: {e}", exc_info=True)
            raise
    
    async def send_sms(
        self,
        to: str,
        message: str,
        from_number: Optional[str] = None,
        status_callback: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send SMS message
        
        Args:
            to: Recipient phone number (E.164 format)
            message: Message content
            from_number: Sender phone number (defaults to configured number)
            status_callback: URL for delivery status webhook
        
        Returns:
            Dictionary with message SID and status
        """
        if not self._initialized:
            await self.initialize()
        
        if not self.client:
            raise RuntimeError("Twilio client not initialized")
        
        try:
            logger.info(f"Sending SMS to {to}")
            
            message_params = {
                "body": message,
                "from_": from_number or settings.twilio_phone_number,
                "to": to
            }
            
            if status_callback:
                message_params["status_callback"] = status_callback
            
            # Send message
            twilio_message = self.client.messages.create(**message_params)
            
            logger.info(f"SMS sent successfully. SID: {twilio_message.sid}")
            
            return {
                "status": "success",
                "message_sid": twilio_message.sid,
                "to": to,
                "status_code": twilio_message.status,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except TwilioRestException as e:
            logger.error(f"Twilio SMS error: {e.msg}", exc_info=True)
            return {
                "status": "error",
                "error": e.msg,
                "error_code": e.code,
                "to": to,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"SMS sending error: {e}", exc_info=True)
            raise
    
    async def send_whatsapp(
        self,
        to: str,
        message: str,
        media_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send WhatsApp message
        
        Args:
            to: Recipient phone number (E.164 format)
            message: Message content
            media_url: Optional media URL (image, video, document)
        
        Returns:
            Dictionary with message SID and status
        """
        if not self._initialized:
            await self.initialize()
        
        if not self.client:
            raise RuntimeError("Twilio client not initialized")
        
        try:
            logger.info(f"Sending WhatsApp message to {to}")
            
            # Format WhatsApp numbers
            whatsapp_to = f"whatsapp:{to}"
            whatsapp_from = f"whatsapp:{settings.twilio_whatsapp_number}"
            
            message_params = {
                "body": message,
                "from_": whatsapp_from,
                "to": whatsapp_to
            }
            
            if media_url:
                message_params["media_url"] = [media_url]
            
            # Send message
            twilio_message = self.client.messages.create(**message_params)
            
            logger.info(f"WhatsApp message sent successfully. SID: {twilio_message.sid}")
            
            return {
                "status": "success",
                "message_sid": twilio_message.sid,
                "to": to,
                "channel": "whatsapp",
                "status_code": twilio_message.status,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except TwilioRestException as e:
            logger.error(f"Twilio WhatsApp error: {e.msg}", exc_info=True)
            return {
                "status": "error",
                "error": e.msg,
                "error_code": e.code,
                "to": to,
                "channel": "whatsapp",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"WhatsApp sending error: {e}", exc_info=True)
            raise
    
    async def send_bulk_sms(
        self,
        recipients: List[str],
        message: str,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Send bulk SMS messages
        
        Args:
            recipients: List of recipient phone numbers
            message: Message content
            batch_size: Number of messages to send concurrently
        
        Returns:
            Dictionary with success/failure counts
        """
        if not self._initialized:
            await self.initialize()
        
        logger.info(f"Sending bulk SMS to {len(recipients)} recipients")
        
        results = {
            "total": len(recipients),
            "success": 0,
            "failed": 0,
            "details": []
        }
        
        # Process in batches
        for i in range(0, len(recipients), batch_size):
            batch = recipients[i:i + batch_size]
            
            # Send messages concurrently
            tasks = [
                self.send_sms(to=recipient, message=message)
                for recipient in batch
            ]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    results["failed"] += 1
                    results["details"].append({"error": str(result)})
                elif result.get("status") == "success":
                    results["success"] += 1
                    results["details"].append(result)
                else:
                    results["failed"] += 1
                    results["details"].append(result)
            
            # Rate limiting delay
            if i + batch_size < len(recipients):
                await asyncio.sleep(1)
        
        logger.info(f"Bulk SMS complete: {results['success']} success, {results['failed']} failed")
        
        return results
    
    async def get_message_status(self, message_sid: str) -> Dict[str, Any]:
        """
        Get delivery status of a message
        
        Args:
            message_sid: Twilio message SID
        
        Returns:
            Dictionary with message status
        """
        if not self._initialized:
            await self.initialize()
        
        if not self.client:
            raise RuntimeError("Twilio client not initialized")
        
        try:
            message = self.client.messages(message_sid).fetch()
            
            return {
                "message_sid": message.sid,
                "status": message.status,
                "to": message.to,
                "from": message.from_,
                "date_sent": message.date_sent.isoformat() if message.date_sent else None,
                "error_code": message.error_code,
                "error_message": message.error_message
            }
            
        except TwilioRestException as e:
            logger.error(f"Error fetching message status: {e.msg}")
            raise


# Global Twilio service instance
twilio_service = TwilioService()
