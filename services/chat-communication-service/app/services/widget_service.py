"""
Widget Service for Business Voice Chat Integration
Manages widget configurations, authentication, and analytics
"""

import logging
import secrets
import hashlib
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime

from supabase import create_client, Client
from app.config.settings import settings

logger = logging.getLogger(__name__)


class WidgetService:
    """Enterprise-grade widget management service"""
    
    def __init__(self):
        """Initialize widget service"""
        self.client: Optional[Client] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize widget service"""
        if self._initialized:
            return
        
        try:
            self.client = create_client(
                settings.supabase_url,
                settings.supabase_key
            )
            self._initialized = True
            logger.info("Widget service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize widget service: {e}")
    
    async def create_widget(
        self,
        business_id: UUID,
        name: str,
        widget_type: str = "voice_chat",
        features: Optional[Dict[str, bool]] = None,
        theme_config: Optional[Dict[str, Any]] = None,
        allowed_domains: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new widget configuration
        
        Args:
            business_id: Business identifier
            name: Widget name
            widget_type: Type of widget
            features: Enabled features
            theme_config: Theme configuration
            allowed_domains: Allowed domains for CORS
            
        Returns:
            Widget configuration with API keys
        """
        try:
            # Generate secure widget credentials
            widget_key = f"wgt_{secrets.token_urlsafe(32)}"
            widget_secret = secrets.token_urlsafe(48)
            
            data = {
                "business_id": str(business_id),
                "widget_key": widget_key,
                "widget_secret": hashlib.sha256(widget_secret.encode()).hexdigest(),
                "name": name,
                "widget_type": widget_type,
                "allowed_domains": allowed_domains or [],
                "features": features or {
                    "voice": True,
                    "text": True,
                    "call": True
                },
                "theme_config": theme_config or {},
                "position": "bottom-right",
                "is_active": True,
                "rate_limit_per_minute": 60,
                "analytics_enabled": True
            }
            
            result = self.client.table("widget_configs").insert(data).execute()
            
            if result.data:
                widget = result.data[0]
                # Return secret only on creation
                widget["widget_secret"] = widget_secret
                logger.info(f"Created widget: {widget_key}")
                return widget
            else:
                raise Exception("Failed to create widget")
                
        except Exception as e:
            logger.error(f"Error creating widget: {e}")
            raise
    
    async def get_widget_config(
        self,
        widget_key: str,
        domain: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get widget configuration
        
        Args:
            widget_key: Widget API key
            domain: Requesting domain (for CORS validation)
            
        Returns:
            Widget configuration (without secret)
        """
        try:
            result = self.client.table("widget_configs")\
                .select("*")\
                .eq("widget_key", widget_key)\
                .eq("is_active", True)\
                .single()\
                .execute()
            
            if not result.data:
                return None
            
            widget = result.data
            
            # Validate domain if provided
            if domain and widget.get("allowed_domains"):
                if domain not in widget["allowed_domains"] and "*" not in widget["allowed_domains"]:
                    logger.warning(f"Domain {domain} not allowed for widget {widget_key}")
                    return None
            
            # Remove sensitive data
            widget.pop("widget_secret", None)
            
            return widget
            
        except Exception as e:
            logger.error(f"Error getting widget config: {e}")
            return None
    
    async def authenticate_widget_request(
        self,
        widget_key: str,
        widget_secret: str
    ) -> bool:
        """
        Authenticate widget API request
        
        Args:
            widget_key: Widget API key
            widget_secret: Widget secret
            
        Returns:
            Authentication success
        """
        try:
            result = self.client.table("widget_configs")\
                .select("widget_secret")\
                .eq("widget_key", widget_key)\
                .eq("is_active", True)\
                .single()\
                .execute()
            
            if not result.data:
                return False
            
            stored_secret_hash = result.data["widget_secret"]
            provided_secret_hash = hashlib.sha256(widget_secret.encode()).hexdigest()
            
            return stored_secret_hash == provided_secret_hash
            
        except Exception as e:
            logger.error(f"Error authenticating widget: {e}")
            return False
    
    async def track_widget_event(
        self,
        widget_id: UUID,
        business_id: UUID,
        event_type: str,
        event_data: Dict[str, Any],
        user_id: Optional[UUID] = None,
        session_id: Optional[str] = None
    ) -> bool:
        """
        Track widget analytics event
        
        Args:
            widget_id: Widget identifier
            business_id: Business identifier
            event_type: Event type
            event_data: Event data
            user_id: User identifier (optional)
            session_id: Session identifier (optional)
            
        Returns:
            Success status
        """
        try:
            data = {
                "widget_id": str(widget_id),
                "business_id": str(business_id),
                "event_type": event_type,
                "event_data": event_data,
                "user_id": str(user_id) if user_id else None,
                "session_id": session_id
            }
            
            result = self.client.table("widget_analytics").insert(data).execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error tracking widget event: {e}")
            return False
    
    async def get_widget_analytics(
        self,
        business_id: UUID,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get widget analytics for a business"""
        try:
            result = self.client.table("widget_analytics")\
                .select("*")\
                .eq("business_id", str(business_id))\
                .gte("created_at", start_date.isoformat())\
                .lte("created_at", end_date.isoformat())\
                .execute()
            
            events = result.data if result.data else []
            
            analytics = {
                "total_events": len(events),
                "unique_sessions": len(set(e.get("session_id") for e in events if e.get("session_id"))),
                "event_types": {},
                "conversion_funnel": {
                    "widget_loaded": 0,
                    "widget_opened": 0,
                    "voice_started": 0,
                    "call_initiated": 0,
                    "call_completed": 0
                }
            }
            
            # Count by event type
            for event in events:
                event_type = event.get("event_type", "unknown")
                analytics["event_types"][event_type] = analytics["event_types"].get(event_type, 0) + 1
                
                # Track conversion funnel
                if event_type in analytics["conversion_funnel"]:
                    analytics["conversion_funnel"][event_type] += 1
            
            # Calculate conversion rates
            if analytics["conversion_funnel"]["widget_loaded"] > 0:
                analytics["conversion_rate"] = (
                    analytics["conversion_funnel"]["call_completed"] / 
                    analytics["conversion_funnel"]["widget_loaded"] * 100
                )
            else:
                analytics["conversion_rate"] = 0
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting widget analytics: {e}")
            return {}
    
    async def update_widget_config(
        self,
        widget_key: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update widget configuration"""
        try:
            # Remove sensitive fields from updates
            updates.pop("widget_key", None)
            updates.pop("widget_secret", None)
            updates.pop("business_id", None)
            
            result = self.client.table("widget_configs")\
                .update(updates)\
                .eq("widget_key", widget_key)\
                .execute()
            
            if result.data:
                widget = result.data[0]
                widget.pop("widget_secret", None)
                return widget
            
            return None
            
        except Exception as e:
            logger.error(f"Error updating widget config: {e}")
            return None
    
    async def list_business_widgets(
        self,
        business_id: UUID
    ) -> List[Dict[str, Any]]:
        """List all widgets for a business"""
        try:
            result = self.client.table("widget_configs")\
                .select("*")\
                .eq("business_id", str(business_id))\
                .order("created_at", desc=True)\
                .execute()
            
            widgets = result.data if result.data else []
            
            # Remove secrets
            for widget in widgets:
                widget.pop("widget_secret", None)
            
            return widgets
            
        except Exception as e:
            logger.error(f"Error listing widgets: {e}")
            return []
    
    async def deactivate_widget(self, widget_key: str) -> bool:
        """Deactivate a widget"""
        try:
            result = self.client.table("widget_configs")\
                .update({"is_active": False})\
                .eq("widget_key", widget_key)\
                .execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error deactivating widget: {e}")
            return False
    
    async def check_rate_limit(
        self,
        widget_key: str,
        identifier: str
    ) -> bool:
        """
        Check if request is within rate limit
        
        Args:
            widget_key: Widget API key
            identifier: Request identifier (IP, user_id, etc.)
            
        Returns:
            True if within limit, False if exceeded
        """
        try:
            # Get widget rate limit
            widget = await self.get_widget_config(widget_key)
            if not widget:
                return False
            
            rate_limit = widget.get("rate_limit_per_minute", 60)
            
            # TODO: Implement Redis-based rate limiting
            # For now, return True (allow all requests)
            return True
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return False


# Global widget service instance
widget_service = WidgetService()
