"""
Database service for Global Chat Service
Handles cross-business queries and global chat sessions
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4

from supabase import create_client, Client
from app.config import settings

logger = logging.getLogger(__name__)


class GlobalDatabaseService:
    """Database service for global chat operations"""
    
    def __init__(self):
        """Initialize database service"""
        self.client: Optional[Client] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize Supabase client"""
        if self._initialized:
            return
        
        try:
            self.client = create_client(
                settings.supabase_url,
                settings.supabase_key
            )
            self._initialized = True
            logger.info("Global database service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def create_global_session(
        self,
        user_id: Optional[UUID] = None,
        channel: str = "web",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new global chat session"""
        try:
            session_id = f"global_{uuid4().hex[:16]}"
            
            data = {
                "session_id": session_id,
                "session_type": "global",
                "business_id": None,  # Global sessions don't have a specific business
                "user_id": str(user_id) if user_id else None,
                "channel": channel,
                "context": context or {},
                "status": "active"
            }
            
            result = self.client.table("chat_sessions").insert(data).execute()
            
            if result.data:
                logger.info(f"Created global session: {session_id}")
                return result.data[0]
            else:
                raise Exception("Failed to create session")
                
        except Exception as e:
            logger.error(f"Error creating global session: {e}")
            raise
    
    async def search_businesses(
        self,
        query: str,
        category: Optional[str] = None,
        location: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search businesses across platform"""
        try:
            # Build query
            db_query = self.client.table("businesses")\
                .select("*, business_details(*), business_categories(name)")\
                .eq("status", "active")\
                .limit(limit)
            
            # Add category filter
            if category:
                db_query = db_query.eq("business_categories.name", category)
            
            # Execute search
            result = db_query.execute()
            
            # Filter by text search if query provided
            businesses = result.data if result.data else []
            
            if query and businesses:
                query_lower = query.lower()
                businesses = [
                    b for b in businesses
                    if query_lower in b.get("name", "").lower() or
                       query_lower in b.get("business_details", {}).get("description", "").lower()
                ]
            
            return businesses[:limit]
            
        except Exception as e:
            logger.error(f"Error searching businesses: {e}")
            return []
    
    async def check_availability(
        self,
        business_id: UUID,
        date: str,
        time: str,
        party_size: int = 1
    ) -> Dict[str, Any]:
        """Check availability for a business"""
        try:
            # Get business
            business = self.client.table("businesses")\
                .select("*")\
                .eq("id", str(business_id))\
                .single()\
                .execute()
            
            if not business.data:
                return {"available": False, "message": "Business not found"}
            
            # Check existing reservations
            reservations = self.client.table("reservations")\
                .select("*")\
                .eq("business_id", str(business_id))\
                .eq("reservation_date", date)\
                .eq("status", "confirmed")\
                .execute()
            
            # Simple availability logic (can be enhanced)
            existing_count = len(reservations.data) if reservations.data else 0
            max_capacity = 50  # Default capacity
            
            available = existing_count < max_capacity
            
            return {
                "available": available,
                "existing_reservations": existing_count,
                "max_capacity": max_capacity,
                "message": "Available" if available else "Fully booked"
            }
            
        except Exception as e:
            logger.error(f"Error checking availability: {e}")
            return {"available": False, "message": "Error checking availability"}
    
    async def create_order(
        self,
        business_id: UUID,
        customer_id: Optional[UUID],
        items: List[Dict[str, Any]],
        total_amount: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create an order through global chat"""
        try:
            order_number = f"ORD-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            
            data = {
                "business_id": str(business_id),
                "customer_id": str(customer_id) if customer_id else None,
                "order_number": order_number,
                "status": "pending",
                "total_amount": total_amount,
                "items": items,
                "metadata": metadata or {}
            }
            
            result = self.client.table("orders").insert(data).execute()
            
            if result.data:
                logger.info(f"Created order: {order_number}")
                return result.data[0]
            else:
                raise Exception("Failed to create order")
                
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            raise
    
    async def create_reservation(
        self,
        business_id: UUID,
        customer_id: Optional[UUID],
        date: str,
        time: str,
        party_size: int,
        customer_name: str,
        customer_phone: str,
        special_requests: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a reservation through global chat"""
        try:
            reservation_number = f"RES-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            
            data = {
                "business_id": str(business_id),
                "customer_id": str(customer_id) if customer_id else None,
                "reservation_number": reservation_number,
                "reservation_date": date,
                "party_size": party_size,
                "status": "pending",
                "customer_name": customer_name,
                "customer_phone": customer_phone,
                "special_requests": special_requests,
                "metadata": {}
            }
            
            result = self.client.table("reservations").insert(data).execute()
            
            if result.data:
                logger.info(f"Created reservation: {reservation_number}")
                return result.data[0]
            else:
                raise Exception("Failed to create reservation")
                
        except Exception as e:
            logger.error(f"Error creating reservation: {e}")
            raise
    
    async def get_business_recommendations(
        self,
        user_id: Optional[UUID] = None,
        category: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get personalized business recommendations"""
        try:
            query = self.client.table("businesses")\
                .select("*, business_details(*), business_categories(name)")\
                .eq("status", "active")\
                .limit(limit)
            
            if category:
                query = query.eq("business_categories.name", category)
            
            result = query.execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            return []
    
    async def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Save a message to global chat session"""
        try:
            # Get session UUID
            session = self.client.table("chat_sessions")\
                .select("id")\
                .eq("session_id", session_id)\
                .single()\
                .execute()
            
            if not session.data:
                raise Exception(f"Session {session_id} not found")
            
            data = {
                "session_id": session.data["id"],
                "role": role,
                "content": content,
                "message_type": "text",
                "ai_generated": role == "assistant",
                "metadata": metadata or {}
            }
            
            result = self.client.table("chat_messages").insert(data).execute()
            
            return result.data[0] if result.data else {}
            
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            raise


# Global instance
global_db_service = GlobalDatabaseService()
