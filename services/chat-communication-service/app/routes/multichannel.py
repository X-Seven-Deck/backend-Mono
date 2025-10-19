"""
Multichannel Integration Routes

WhatsApp, Instagram, and QR Code integrations.
"""

import logging
from fastapi import APIRouter, HTTPException, Request, Response, Query
from typing import Optional

from app.models.chat_models import (
    WhatsAppTextMessage,
    WhatsAppTemplateMessage,
    WhatsAppMediaMessage,
    WhatsAppInteractiveMessage,
    WhatsAppWebhookPayload,
    InstagramTextMessage,
    InstagramMediaMessage,
    InstagramQuickReplies,
    InstagramWebhookPayload,
    GenerateQRCodeRequest,
    GenerateTableQRRequest,
    GenerateProductQRRequest,
    GenerateServiceQRRequest,
    QRCodeResponse,
    QRCodeAnalytics,
    SuccessResponse
)

from app.services.whatsapp_service import get_whatsapp_service
from app.services.instagram_service import get_instagram_service
from app.services.qrcode_service import get_qrcode_service
from app.services.database_service import db_service
from app.services.ai_service import ai_service
from app.services.event_publisher import event_publisher

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["multichannel"])

# ============================================================================
# WHATSAPP ENDPOINTS
# ============================================================================

@router.post("/whatsapp/send-message")
async def send_whatsapp_message(request: WhatsAppTextMessage):
    """
    Send text message via WhatsApp Business API.
    
    Automatically creates/updates chat session.
    """
    try:
        whatsapp_service = get_whatsapp_service()
        
        # Send message
        result = await whatsapp_service.send_text_message(
            to=request.to,
            message=request.message,
            context_message_id=request.context_message_id
        )
        
        if result["success"]:
            # Create or get session for this WhatsApp conversation
            # Session ID format: whatsapp_{business_id}_{phone_number}
            session_id = f"whatsapp_{request.business_id}_{request.to}"
            
            session = await db_service.get_chat_session(session_id)
            
            if not session:
                session = await db_service.create_chat_session(
                    session_type="dedicated",
                    business_id=request.business_id,
                    channel="whatsapp",
                    context={"phone_number": request.to}
                )
            
            # Store message
            await db_service.add_message(
                session_id=session["session_id"],
                role="assistant",
                content=request.message,
                message_type="text",
                metadata={"whatsapp_message_id": result["message_id"]}
            )
            
            logger.info(f"WhatsApp message sent to {request.to}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/whatsapp/send-template")
async def send_whatsapp_template(request: WhatsAppTemplateMessage):
    """Send pre-approved WhatsApp template message"""
    try:
        whatsapp_service = get_whatsapp_service()
        
        result = await whatsapp_service.send_template_message(
            to=request.to,
            template_name=request.template_name,
            language_code=request.language_code,
            parameters=request.parameters
        )
        
        if result["success"]:
            logger.info(f"WhatsApp template '{request.template_name}' sent to {request.to}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error sending WhatsApp template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/whatsapp/send-media")
async def send_whatsapp_media(request: WhatsAppMediaMessage):
    """Send media message via WhatsApp"""
    try:
        whatsapp_service = get_whatsapp_service()
        
        result = await whatsapp_service.send_media_message(
            to=request.to,
            media_type=request.media_type,
            media_url=request.media_url,
            caption=request.caption
        )
        
        if result["success"]:
            logger.info(f"WhatsApp {request.media_type} sent to {request.to}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error sending WhatsApp media: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/whatsapp/send-interactive")
async def send_whatsapp_interactive(request: WhatsAppInteractiveMessage):
    """Send interactive message with buttons"""
    try:
        whatsapp_service = get_whatsapp_service()
        
        result = await whatsapp_service.send_interactive_message(
            to=request.to,
            body_text=request.body_text,
            buttons=request.buttons
        )
        
        if result["success"]:
            logger.info(f"WhatsApp interactive message sent to {request.to}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error sending WhatsApp interactive message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/whatsapp/webhook")
async def verify_whatsapp_webhook(
    request: Request,
    mode: str = Query(None, alias="hub.mode"),
    challenge: str = Query(None, alias="hub.challenge"),
    verify_token: str = Query(None, alias="hub.verify_token")
):
    """
    WhatsApp webhook verification endpoint.
    
    Facebook/WhatsApp will call this to verify webhook.
    """
    import os
    
    expected_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "x7ai_secure_token")
    
    if mode == "subscribe" and verify_token == expected_token:
        logger.info("WhatsApp webhook verified successfully")
        return Response(content=challenge, media_type="text/plain")
    else:
        logger.warning(f"WhatsApp webhook verification failed: {verify_token}")
        raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/whatsapp/webhook")
async def whatsapp_webhook(payload: dict):
    """
    WhatsApp webhook handler for incoming messages.
    
    Processes:
    - Incoming messages
    - Delivery receipts
    - Read receipts
    """
    try:
        whatsapp_service = get_whatsapp_service()
        
        # Process webhook
        event = await whatsapp_service.process_webhook(payload)
        
        if event["type"] == "message":
            # Create/get session
            business_id = "default"  # Would be determined from phone_number_id
            session_id = f"whatsapp_{business_id}_{event['from']}"
            
            session = await db_service.get_chat_session(session_id)
            
            if not session:
                session = await db_service.create_chat_session(
                    session_type="dedicated",
                    business_id=business_id,
                    channel="whatsapp",
                    context={"phone_number": event['from']}
                )
            
            # Store user message
            user_message = await db_service.add_message(
                session_id=session["session_id"],
                role="user",
                content=event.get("text", ""),
                message_type="text",
                metadata={"whatsapp_message_id": event["message_id"]}
            )
            
            # Process with AI
            conversation_history = await db_service.get_session_messages(
                session["session_id"],
                limit=10
            )
            
            ai_result = await ai_service.process_message_with_ai(
                message=event.get("text", ""),
                business_id=business_id,
                conversation_history=[
                    {"role": msg["role"], "content": msg["content"]}
                    for msg in conversation_history[:-1]
                ]
            )
            
            # Send AI response via WhatsApp
            if ai_result.get("response"):
                await whatsapp_service.send_text_message(
                    to=event['from'],
                    message=ai_result["response"],
                    context_message_id=event["message_id"]
                )
                
                # Store AI response
                await db_service.add_message(
                    session_id=session["session_id"],
                    role="assistant",
                    content=ai_result["response"],
                    message_type="text",
                    ai_generated=True,
                    ai_model=ai_result["ai_metadata"].get("model"),
                    intent=ai_result["intent"]["intent"]
                )
            
            # Mark as read
            await whatsapp_service.mark_message_read(event["message_id"])
            
            logger.info(f"Processed WhatsApp message from {event['from']}")
        
        return {"status": "processed"}
        
    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {e}")
        return {"status": "error", "error": str(e)}


# ============================================================================
# INSTAGRAM ENDPOINTS
# ============================================================================

@router.post("/instagram/send-message")
async def send_instagram_message(request: InstagramTextMessage):
    """Send text message via Instagram Messaging API"""
    try:
        instagram_service = get_instagram_service()
        
        result = await instagram_service.send_message(
            recipient_id=request.recipient_id,
            message_text=request.message_text,
            message_type=request.message_type
        )
        
        if result["success"]:
            # Create or get session
            session_id = f"instagram_{request.business_id}_{request.recipient_id}"
            
            session = await db_service.get_chat_session(session_id)
            
            if not session:
                session = await db_service.create_chat_session(
                    session_type="dedicated",
                    business_id=request.business_id,
                    channel="instagram",
                    context={"recipient_id": request.recipient_id}
                )
            
            # Store message
            await db_service.add_message(
                session_id=session["session_id"],
                role="assistant",
                content=request.message_text,
                message_type="text",
                metadata={"instagram_message_id": result["message_id"]}
            )
            
            logger.info(f"Instagram message sent to {request.recipient_id}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error sending Instagram message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/instagram/send-media")
async def send_instagram_media(request: InstagramMediaMessage):
    """Send media message via Instagram"""
    try:
        instagram_service = get_instagram_service()
        
        result = await instagram_service.send_media_message(
            recipient_id=request.recipient_id,
            media_url=request.media_url,
            media_type=request.media_type
        )
        
        if result["success"]:
            logger.info(f"Instagram {request.media_type} sent to {request.recipient_id}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error sending Instagram media: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/instagram/send-quick-replies")
async def send_instagram_quick_replies(request: InstagramQuickReplies):
    """Send message with quick reply buttons"""
    try:
        instagram_service = get_instagram_service()
        
        result = await instagram_service.send_quick_replies(
            recipient_id=request.recipient_id,
            message_text=request.message_text,
            quick_replies=request.quick_replies
        )
        
        if result["success"]:
            logger.info(f"Instagram quick replies sent to {request.recipient_id}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error sending Instagram quick replies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/instagram/webhook")
async def verify_instagram_webhook(
    request: Request,
    mode: str = Query(None, alias="hub.mode"),
    challenge: str = Query(None, alias="hub.challenge"),
    verify_token: str = Query(None, alias="hub.verify_token")
):
    """Instagram webhook verification"""
    import os
    
    expected_token = os.getenv("INSTAGRAM_VERIFY_TOKEN", "x7ai_secure_token")
    
    if mode == "subscribe" and verify_token == expected_token:
        logger.info("Instagram webhook verified successfully")
        return Response(content=challenge, media_type="text/plain")
    else:
        logger.warning(f"Instagram webhook verification failed")
        raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/instagram/webhook")
async def instagram_webhook(payload: dict):
    """
    Instagram webhook handler for incoming messages.
    """
    try:
        instagram_service = get_instagram_service()
        
        # Process webhook
        event = await instagram_service.process_webhook(payload)
        
        if event["type"] == "message":
            # Similar processing as WhatsApp
            business_id = "default"
            session_id = f"instagram_{business_id}_{event['sender_id']}"
            
            session = await db_service.get_chat_session(session_id)
            
            if not session:
                session = await db_service.create_chat_session(
                    session_type="dedicated",
                    business_id=business_id,
                    channel="instagram",
                    context={"sender_id": event['sender_id']}
                )
            
            # Store and process message with AI
            await db_service.add_message(
                session_id=session["session_id"],
                role="user",
                content=event.get("text", ""),
                message_type="text"
            )
            
            # Get conversation history
            conversation_history = await db_service.get_session_messages(
                session["session_id"],
                limit=10
            )
            
            # Process with AI
            ai_result = await ai_service.process_message_with_ai(
                message=event.get("text", ""),
                business_id=business_id,
                conversation_history=[
                    {"role": msg["role"], "content": msg["content"]}
                    for msg in conversation_history[:-1]
                ]
            )
            
            # Send AI response
            if ai_result.get("response"):
                await instagram_service.send_message(
                    recipient_id=event['sender_id'],
                    message_text=ai_result["response"]
                )
                
                # Store AI response
                await db_service.add_message(
                    session_id=session["session_id"],
                    role="assistant",
                    content=ai_result["response"],
                    ai_generated=True,
                    ai_model=ai_result["ai_metadata"].get("model")
                )
            
            logger.info(f"Processed Instagram message from {event['sender_id']}")
        
        return {"status": "processed"}
        
    except Exception as e:
        logger.error(f"Error processing Instagram webhook: {e}")
        return {"status": "error", "error": str(e)}


# ============================================================================
# QR CODE ENDPOINTS
# ============================================================================

@router.post("/qrcode/generate", response_model=QRCodeResponse)
async def generate_qr_code(request: GenerateQRCodeRequest):
    """
    Generate dynamic QR code with embedded context.
    
    Supports multiple context types:
    - table: Restaurant table ordering
    - product: Product inquiry/purchase
    - service: Service booking
    - general: General business contact
    """
    try:
        qrcode_service = get_qrcode_service()
        
        result = qrcode_service.generate_qr_code(
            business_id=request.business_id,
            context_type=request.context_type,
            context_data=request.context_data,
            expires_in_hours=request.expires_in_hours
        )
        
        logger.info(f"Generated QR code {result['qr_id']} for business {request.business_id}")
        
        return QRCodeResponse(**result)
        
    except Exception as e:
        logger.error(f"Error generating QR code: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/qrcode/table", response_model=QRCodeResponse)
async def generate_table_qr(request: GenerateTableQRRequest):
    """Generate QR code for restaurant table"""
    try:
        qrcode_service = get_qrcode_service()
        
        result = qrcode_service.generate_table_qr(
            business_id=request.business_id,
            table_number=request.table_number,
            table_name=request.table_name,
            section=request.section
        )
        
        logger.info(f"Generated table QR code for table {request.table_number}")
        
        return QRCodeResponse(**result)
        
    except Exception as e:
        logger.error(f"Error generating table QR code: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/qrcode/product", response_model=QRCodeResponse)
async def generate_product_qr(request: GenerateProductQRRequest):
    """Generate QR code for product inquiry"""
    try:
        qrcode_service = get_qrcode_service()
        
        result = qrcode_service.generate_product_qr(
            business_id=request.business_id,
            product_id=request.product_id,
            product_name=request.product_name,
            product_image=request.product_image
        )
        
        logger.info(f"Generated product QR code for {request.product_name}")
        
        return QRCodeResponse(**result)
        
    except Exception as e:
        logger.error(f"Error generating product QR code: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/qrcode/service", response_model=QRCodeResponse)
async def generate_service_qr(request: GenerateServiceQRRequest):
    """Generate QR code for service booking"""
    try:
        qrcode_service = get_qrcode_service()
        
        result = qrcode_service.generate_service_qr(
            business_id=request.business_id,
            service_id=request.service_id,
            service_name=request.service_name,
            service_type=request.service_type
        )
        
        logger.info(f"Generated service QR code for {request.service_name}")
        
        return QRCodeResponse(**result)
        
    except Exception as e:
        logger.error(f"Error generating service QR code: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/qrcode/{qr_id}/scan")
async def track_qr_scan(qr_id: str, metadata: Optional[dict] = None):
    """
    Track QR code scan.
    
    Called when QR code is scanned to record analytics.
    """
    try:
        qrcode_service = get_qrcode_service()
        
        success = await qrcode_service.track_scan(qr_id, metadata)
        
        if not success:
            raise HTTPException(status_code=404, detail="QR code not found or expired")
        
        # Get context for chat initialization
        context = qrcode_service.get_qr_context(qr_id)
        
        return {
            "success": True,
            "qr_id": qr_id,
            "context": context
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking QR scan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/qrcode/{qr_id}/analytics", response_model=QRCodeAnalytics)
async def get_qr_analytics(qr_id: str):
    """Get analytics for QR code"""
    try:
        qrcode_service = get_qrcode_service()
        
        analytics = qrcode_service.get_qr_analytics(qr_id)
        
        if not analytics:
            raise HTTPException(status_code=404, detail="QR code not found")
        
        return QRCodeAnalytics(**analytics)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting QR analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/qrcode/{qr_id}")
async def deactivate_qr_code(qr_id: str):
    """Deactivate QR code"""
    try:
        qrcode_service = get_qrcode_service()
        
        success = qrcode_service.deactivate_qr(qr_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="QR code not found")
        
        return SuccessResponse(
            success=True,
            message="QR code deactivated successfully",
            data={"qr_id": qr_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating QR code: {e}")
        raise HTTPException(status_code=500, detail=str(e))

