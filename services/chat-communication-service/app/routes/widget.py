"""
Widget Routes - Business voice chat widget API
"""

import logging
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel, Field

from app.services.widget_service import widget_service
from app.services.push_notification_service import push_notification_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/widget", tags=["Widget"])


class CreateWidgetRequest(BaseModel):
    """Request to create a widget"""
    business_id: UUID
    name: str
    widget_type: str = "voice_chat"
    features: Optional[dict] = None
    theme_config: Optional[dict] = None
    allowed_domains: Optional[List[str]] = None


class UpdateWidgetRequest(BaseModel):
    """Request to update widget configuration"""
    name: Optional[str] = None
    features: Optional[dict] = None
    theme_config: Optional[dict] = None
    allowed_domains: Optional[List[str]] = None
    position: Optional[str] = None
    rate_limit_per_minute: Optional[int] = None


class TrackEventRequest(BaseModel):
    """Request to track widget event"""
    event_type: str
    event_data: dict
    session_id: Optional[str] = None


class RegisterDeviceRequest(BaseModel):
    """Request to register device for push notifications"""
    device_token: str
    device_type: str
    platform: str


@router.post("/create")
async def create_widget(request: CreateWidgetRequest):
    """
    Create a new widget configuration
    
    Returns widget key and secret for authentication
    """
    try:
        widget = await widget_service.create_widget(
            business_id=request.business_id,
            name=request.name,
            widget_type=request.widget_type,
            features=request.features,
            theme_config=request.theme_config,
            allowed_domains=request.allowed_domains
        )
        
        logger.info(f"Created widget for business {request.business_id}")
        
        return {
            "status": "success",
            "widget": widget,
            "message": "Widget created successfully. Save the widget_secret securely - it won't be shown again."
        }
        
    except Exception as e:
        logger.error(f"Error creating widget: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/{widget_key}")
async def get_widget_config(
    widget_key: str,
    request: Request
):
    """
    Get widget configuration
    
    Validates domain and returns widget settings
    """
    try:
        # Get origin domain from request
        origin = request.headers.get("origin") or request.headers.get("referer")
        domain = None
        
        if origin:
            from urllib.parse import urlparse
            parsed = urlparse(origin)
            domain = parsed.netloc
        
        widget = await widget_service.get_widget_config(
            widget_key=widget_key,
            domain=domain
        )
        
        if not widget:
            raise HTTPException(status_code=404, detail="Widget not found or domain not allowed")
        
        return {
            "status": "success",
            "widget": widget
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting widget config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/authenticate")
async def authenticate_widget(
    widget_key: str = Header(..., alias="X-Widget-Key"),
    widget_secret: str = Header(..., alias="X-Widget-Secret")
):
    """
    Authenticate widget API request
    
    Returns authentication token for subsequent requests
    """
    try:
        is_valid = await widget_service.authenticate_widget_request(
            widget_key=widget_key,
            widget_secret=widget_secret
        )
        
        if not is_valid:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # In production, generate a JWT token here
        auth_token = f"wgt_token_{widget_key}"
        
        return {
            "status": "success",
            "authenticated": True,
            "token": auth_token
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error authenticating widget: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{widget_key}/track")
async def track_widget_event(
    widget_key: str,
    request: TrackEventRequest,
    user_id: Optional[str] = Header(None, alias="X-User-ID")
):
    """
    Track widget analytics event
    
    Records user interactions for analytics
    """
    try:
        # Get widget to validate and get business_id
        widget = await widget_service.get_widget_config(widget_key)
        
        if not widget:
            raise HTTPException(status_code=404, detail="Widget not found")
        
        if not widget.get("analytics_enabled"):
            return {"status": "success", "tracked": False, "reason": "analytics_disabled"}
        
        # Track event
        success = await widget_service.track_widget_event(
            widget_id=UUID(widget["id"]),
            business_id=UUID(widget["business_id"]),
            event_type=request.event_type,
            event_data=request.event_data,
            user_id=UUID(user_id) if user_id else None,
            session_id=request.session_id
        )
        
        return {
            "status": "success",
            "tracked": success
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking widget event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{widget_key}")
async def update_widget(
    widget_key: str,
    request: UpdateWidgetRequest
):
    """Update widget configuration"""
    try:
        updates = request.dict(exclude_unset=True)
        
        widget = await widget_service.update_widget_config(
            widget_key=widget_key,
            updates=updates
        )
        
        if not widget:
            raise HTTPException(status_code=404, detail="Widget not found")
        
        return {
            "status": "success",
            "widget": widget
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating widget: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{widget_key}")
async def deactivate_widget(widget_key: str):
    """Deactivate a widget"""
    try:
        success = await widget_service.deactivate_widget(widget_key)
        
        if not success:
            raise HTTPException(status_code=404, detail="Widget not found")
        
        return {
            "status": "success",
            "message": "Widget deactivated"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating widget: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/business/{business_id}/widgets")
async def list_business_widgets(business_id: UUID):
    """List all widgets for a business"""
    try:
        widgets = await widget_service.list_business_widgets(business_id)
        
        return {
            "status": "success",
            "widgets": widgets,
            "count": len(widgets)
        }
        
    except Exception as e:
        logger.error(f"Error listing widgets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/business/{business_id}/analytics")
async def get_widget_analytics(
    business_id: UUID,
    days: int = 7
):
    """Get widget analytics for a business"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        analytics = await widget_service.get_widget_analytics(
            business_id=business_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "status": "success",
            "analytics": analytics,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting widget analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/push/register")
async def register_push_token(
    request: RegisterDeviceRequest,
    user_id: str = Header(..., alias="X-User-ID")
):
    """
    Register device token for push notifications
    
    Used for incoming call alerts
    """
    try:
        success = await push_notification_service.register_device_token(
            user_id=UUID(user_id),
            device_token=request.device_token,
            device_type=request.device_type,
            platform=request.platform
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to register device token")
        
        return {
            "status": "success",
            "message": "Device token registered successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering push token: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/push/deactivate")
async def deactivate_push_token(
    device_token: str,
    user_id: str = Header(..., alias="X-User-ID")
):
    """Deactivate a device token"""
    try:
        success = await push_notification_service.deactivate_token(device_token)
        
        if not success:
            raise HTTPException(status_code=404, detail="Token not found")
        
        return {
            "status": "success",
            "message": "Device token deactivated"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating push token: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/embed-code/{widget_key}")
async def get_embed_code(widget_key: str):
    """
    Get widget embed code for website integration
    
    Returns HTML/JavaScript code to embed the widget
    """
    try:
        widget = await widget_service.get_widget_config(widget_key)
        
        if not widget:
            raise HTTPException(status_code=404, detail="Widget not found")
        
        # Generate embed code
        embed_code = f"""
<!-- X-sevenAI Voice Chat Widget -->
<script src="https://cdn.x7ai.com/widget/v1/voice-chat.js"></script>
<script>
  X7AI.init({{
    widgetKey: '{widget_key}',
    businessId: '{widget["business_id"]}',
    position: '{widget.get("position", "bottom-right")}',
    theme: {widget.get("theme_config", {})},
    features: {widget.get("features", {})}
  }});
</script>
<!-- End X-sevenAI Widget -->
"""
        
        iframe_code = f"""
<!-- X-sevenAI Voice Chat Widget (iFrame) -->
<iframe 
  src="https://widget.x7ai.com/?key={widget_key}"
  width="350" 
  height="500"
  style="border:none; position:fixed; bottom:20px; right:20px; border-radius:10px; box-shadow:0 4px 12px rgba(0,0,0,0.15);">
</iframe>
<!-- End X-sevenAI Widget -->
"""
        
        return {
            "status": "success",
            "widget_key": widget_key,
            "embed_codes": {
                "script": embed_code.strip(),
                "iframe": iframe_code.strip()
            },
            "instructions": {
                "script": "Copy and paste this code before the closing </body> tag",
                "iframe": "Copy and paste this code anywhere in your HTML"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting embed code: {e}")
        raise HTTPException(status_code=500, detail=str(e))
