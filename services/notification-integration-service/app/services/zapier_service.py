"""
Zapier Service for webhook integrations
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import httpx
import asyncio

from app.config import settings
from app.utils import logger


class ZapierService:
    """
    Enterprise-grade Zapier webhook service
    
    Features:
    - Webhook triggers for Zapier integrations
    - Custom event routing
    - Retry logic with exponential backoff
    - Batch webhook delivery
    """
    
    def __init__(self):
        self.client: Optional[httpx.AsyncClient] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize Zapier service"""
        if self._initialized:
            return
        
        try:
            self.client = httpx.AsyncClient(
                timeout=30.0,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "X-sevenAI-Notification-Service/1.0"
                }
            )
            
            logger.info("Zapier service initialized successfully")
            self._initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize Zapier service: {e}", exc_info=True)
            raise
    
    async def trigger_webhook(
        self,
        webhook_url: str,
        data: Dict[str, Any],
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Trigger Zapier webhook
        
        Args:
            webhook_url: Zapier webhook URL
            data: Payload data
            retry_count: Current retry attempt
        
        Returns:
            Dictionary with trigger status
        """
        if not self._initialized:
            await self.initialize()
        
        if not self.client:
            raise RuntimeError("Zapier client not initialized")
        
        try:
            logger.info(f"Triggering Zapier webhook: {webhook_url[:50]}...")
            
            response = await self.client.post(webhook_url, json=data)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Webhook triggered successfully. Status: {response.status_code}")
                
                return {
                    "status": "success",
                    "webhook_url": webhook_url,
                    "status_code": response.status_code,
                    "response": response.text,
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                logger.warning(f"Webhook returned non-success status: {response.status_code}")
                
                # Retry logic
                if retry_count < settings.max_retries:
                    delay = settings.retry_delay * (2 ** retry_count)  # Exponential backoff
                    logger.info(f"Retrying webhook in {delay} seconds...")
                    await asyncio.sleep(delay)
                    return await self.trigger_webhook(webhook_url, data, retry_count + 1)
                
                return {
                    "status": "error",
                    "webhook_url": webhook_url,
                    "status_code": response.status_code,
                    "error": response.text,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
        except httpx.RequestError as e:
            logger.error(f"Webhook request error: {e}", exc_info=True)
            
            # Retry on network errors
            if retry_count < settings.max_retries:
                delay = settings.retry_delay * (2 ** retry_count)
                logger.info(f"Retrying webhook in {delay} seconds...")
                await asyncio.sleep(delay)
                return await self.trigger_webhook(webhook_url, data, retry_count + 1)
            
            return {
                "status": "error",
                "webhook_url": webhook_url,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Webhook trigger error: {e}", exc_info=True)
            raise
    
    async def trigger_event(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        use_default_webhook: bool = True
    ) -> Dict[str, Any]:
        """
        Trigger custom event to Zapier
        
        Args:
            event_type: Type of event (e.g., 'order_created', 'reservation_confirmed')
            event_data: Event payload
            use_default_webhook: Use configured default webhook URL
        
        Returns:
            Dictionary with trigger status
        """
        webhook_url = settings.zapier_webhook_url if use_default_webhook else event_data.get("webhook_url")
        
        if not webhook_url:
            raise ValueError("No webhook URL provided")
        
        payload = {
            "event_type": event_type,
            "event_data": event_data,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "x7ai-notification-service"
        }
        
        return await self.trigger_webhook(webhook_url, payload)
    
    async def trigger_bulk_webhooks(
        self,
        webhooks: List[Dict[str, Any]],
        batch_size: int = 50
    ) -> Dict[str, Any]:
        """
        Trigger multiple webhooks in parallel
        
        Args:
            webhooks: List of webhook configurations with 'url' and 'data'
            batch_size: Number of webhooks to trigger concurrently
        
        Returns:
            Dictionary with success/failure counts
        """
        if not self._initialized:
            await self.initialize()
        
        logger.info(f"Triggering {len(webhooks)} webhooks in batches")
        
        results = {
            "total": len(webhooks),
            "success": 0,
            "failed": 0,
            "details": []
        }
        
        # Process in batches
        for i in range(0, len(webhooks), batch_size):
            batch = webhooks[i:i + batch_size]
            
            # Trigger webhooks concurrently
            tasks = [
                self.trigger_webhook(
                    webhook_url=webhook.get("url"),
                    data=webhook.get("data", {})
                )
                for webhook in batch
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
            if i + batch_size < len(webhooks):
                await asyncio.sleep(0.5)
        
        logger.info(f"Bulk webhooks complete: {results['success']} success, {results['failed']} failed")
        
        return results
    
    async def close(self):
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()
            logger.info("Zapier client closed")


# Global Zapier service instance
zapier_service = ZapierService()
