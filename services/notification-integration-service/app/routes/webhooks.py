"""
Webhook endpoints for receiving callbacks
"""

from fastapi import APIRouter, Request, HTTPException
from app.utils import logger

router = APIRouter()


@router.post("/twilio/status")
async def twilio_status_callback(request: Request):
    """
    Twilio delivery status webhook
    
    Receives delivery status updates from Twilio
    """
    try:
        form_data = await request.form()
        
        message_sid = form_data.get("MessageSid")
        message_status = form_data.get("MessageStatus")
        error_code = form_data.get("ErrorCode")
        
        logger.info(f"Twilio status update: SID={message_sid}, Status={message_status}, Error={error_code}")
        
        # Here you would typically:
        # 1. Update database with delivery status
        # 2. Trigger analytics events
        # 3. Send notifications to business owners
        # 4. Update metrics
        
        return {
            "status": "received",
            "message_sid": message_sid,
            "message_status": message_status
        }
    
    except Exception as e:
        logger.error(f"Twilio webhook error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sendgrid/events")
async def sendgrid_event_webhook(request: Request):
    """
    SendGrid event webhook
    
    Receives email events (delivered, opened, clicked, etc.)
    """
    try:
        events = await request.json()
        
        logger.info(f"SendGrid events received: {len(events)} events")
        
        for event in events:
            event_type = event.get("event")
            email = event.get("email")
            timestamp = event.get("timestamp")
            
            logger.info(f"Email event: {event_type} for {email} at {timestamp}")
            
            # Process events:
            # 1. Update delivery analytics
            # 2. Track engagement metrics
            # 3. Handle bounces and spam reports
        
        return {"status": "received", "count": len(events)}
    
    except Exception as e:
        logger.error(f"SendGrid webhook error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/zapier/callback")
async def zapier_callback(request: Request):
    """
    Zapier callback webhook
    
    Receives responses from Zapier integrations
    """
    try:
        data = await request.json()
        
        logger.info(f"Zapier callback received: {data}")
        
        # Process Zapier callback
        # 1. Update integration status
        # 2. Trigger follow-up actions
        # 3. Log integration events
        
        return {"status": "received", "data": data}
    
    except Exception as e:
        logger.error(f"Zapier callback error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
