"""
Notification endpoints
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models.schemas import (
    SMSNotificationRequest,
    WhatsAppNotificationRequest,
    EmailNotificationRequest,
    TemplateEmailRequest,
    WebhookNotificationRequest,
    BulkSMSRequest,
    BulkEmailRequest,
    NotificationResponse,
    BulkNotificationResponse
)
from app.services.twilio_service import twilio_service
from app.services.sendgrid_service import sendgrid_service
from app.services.zapier_service import zapier_service
from app.utils import logger

router = APIRouter()


@router.post("/sms", response_model=NotificationResponse)
async def send_sms(request: SMSNotificationRequest):
    """
    Send SMS notification
    
    Sends SMS via Twilio with delivery tracking
    """
    try:
        logger.info(f"SMS notification request for {request.to}")
        
        result = await twilio_service.send_sms(
            to=request.to,
            message=request.message,
            from_number=request.from_number,
            status_callback=request.status_callback
        )
        
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        return NotificationResponse(
            status="success",
            message_id=result.get("message_sid"),
            timestamp=result.get("timestamp"),
            details=result
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SMS notification error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/whatsapp", response_model=NotificationResponse)
async def send_whatsapp(request: WhatsAppNotificationRequest):
    """
    Send WhatsApp notification
    
    Sends WhatsApp message via Twilio Business API
    """
    try:
        logger.info(f"WhatsApp notification request for {request.to}")
        
        result = await twilio_service.send_whatsapp(
            to=request.to,
            message=request.message,
            media_url=request.media_url
        )
        
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        return NotificationResponse(
            status="success",
            message_id=result.get("message_sid"),
            timestamp=result.get("timestamp"),
            details=result
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"WhatsApp notification error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/email", response_model=NotificationResponse)
async def send_email(request: EmailNotificationRequest):
    """
    Send email notification
    
    Sends email via SendGrid with optional attachments
    """
    try:
        logger.info(f"Email notification request for {request.to_email}")
        
        result = await sendgrid_service.send_email(
            to_email=request.to_email,
            subject=request.subject,
            html_content=request.html_content,
            plain_content=request.plain_content,
            from_email=request.from_email,
            from_name=request.from_name,
            attachments=request.attachments
        )
        
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        return NotificationResponse(
            status="success",
            message_id=result.get("message_id"),
            timestamp=result.get("timestamp"),
            details=result
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email notification error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/email/template", response_model=NotificationResponse)
async def send_template_email(request: TemplateEmailRequest):
    """
    Send template-based email
    
    Sends email using SendGrid dynamic templates
    """
    try:
        logger.info(f"Template email request for {request.to_email}")
        
        result = await sendgrid_service.send_template_email(
            to_email=request.to_email,
            template_id=request.template_id,
            dynamic_data=request.dynamic_data,
            from_email=request.from_email,
            from_name=request.from_name
        )
        
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        return NotificationResponse(
            status="success",
            message_id=result.get("message_id"),
            timestamp=result.get("timestamp"),
            details=result
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Template email error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook", response_model=NotificationResponse)
async def send_webhook(request: WebhookNotificationRequest):
    """
    Send webhook notification
    
    Triggers Zapier webhook with custom data
    """
    try:
        logger.info(f"Webhook notification request for {request.webhook_url}")
        
        result = await zapier_service.trigger_webhook(
            webhook_url=request.webhook_url,
            data=request.data
        )
        
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        return NotificationResponse(
            status="success",
            timestamp=result.get("timestamp"),
            details=result
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook notification error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk/sms", response_model=BulkNotificationResponse)
async def send_bulk_sms(request: BulkSMSRequest, background_tasks: BackgroundTasks):
    """
    Send bulk SMS notifications
    
    Sends SMS to multiple recipients with batch processing
    """
    try:
        logger.info(f"Bulk SMS request for {len(request.recipients)} recipients")
        
        result = await twilio_service.send_bulk_sms(
            recipients=request.recipients,
            message=request.message,
            batch_size=request.batch_size
        )
        
        return BulkNotificationResponse(
            total=result["total"],
            success=result["success"],
            failed=result["failed"],
            details=result["details"]
        )
    
    except Exception as e:
        logger.error(f"Bulk SMS error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk/email", response_model=BulkNotificationResponse)
async def send_bulk_email(request: BulkEmailRequest, background_tasks: BackgroundTasks):
    """
    Send bulk email notifications
    
    Sends emails to multiple recipients with batch processing
    """
    try:
        logger.info(f"Bulk email request for {len(request.recipients)} recipients")
        
        result = await sendgrid_service.send_bulk_email(
            recipients=request.recipients,
            subject=request.subject,
            html_content=request.html_content,
            batch_size=request.batch_size
        )
        
        return BulkNotificationResponse(
            total=result["total"],
            success=result["success"],
            failed=result["failed"],
            details=result["details"]
        )
    
    except Exception as e:
        logger.error(f"Bulk email error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{message_sid}")
async def get_message_status(message_sid: str):
    """
    Get delivery status of a message
    
    Retrieves status from Twilio for SMS/WhatsApp messages
    """
    try:
        status = await twilio_service.get_message_status(message_sid)
        return status
    
    except Exception as e:
        logger.error(f"Status retrieval error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
