"""
Database service for Dedicated Business Chat
Handles all database operations with Supabase
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from supabase import create_client, Client
from app.config import settings

logger = logging.getLogger(__name__)


class DatabaseService:
    """Database service for chat operations"""
    
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
            logger.info("Database service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database service: {e}")
            raise
    
    async def create_session(
        self,
        business_id: UUID,
        user_id: Optional[UUID] = None,
        channel: str = "web",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new chat session"""
        try:
            session_id = f"dedicated_{business_id}_{uuid4().hex[:12]}"
            
            data = {
                "session_id": session_id,
                "session_type": "dedicated",
                "business_id": str(business_id),
                "user_id": str(user_id) if user_id else None,
                "channel": channel,
                "context": context or {},
                "status": "active"
            }
            
            result = self.client.table("chat_sessions").insert(data).execute()
            
            if result.data:
                logger.info(f"Created chat session: {session_id}")
                return result.data[0]
            else:
                raise Exception("Failed to create session")
                
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get chat session by ID"""
        try:
            result = self.client.table("chat_sessions")\
                .select("*")\
                .eq("session_id", session_id)\
                .single()\
                .execute()
            
            return result.data if result.data else None
            
        except Exception as e:
            logger.error(f"Error getting session {session_id}: {e}")
            return None
    
    async def get_business_sessions(
        self,
        business_id: UUID,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get all sessions for a business"""
        try:
            query = self.client.table("chat_sessions")\
                .select("*")\
                .eq("business_id", str(business_id))\
                .eq("session_type", "dedicated")\
                .order("created_at", desc=True)\
                .limit(limit)
            
            if status:
                query = query.eq("status", status)
            
            result = query.execute()
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error getting business sessions: {e}")
            return []
    
    async def update_session(
        self,
        session_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update chat session"""
        try:
            result = self.client.table("chat_sessions")\
                .update(updates)\
                .eq("session_id", session_id)\
                .execute()
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"Error updating session {session_id}: {e}")
            return None
    
    async def close_session(self, session_id: str) -> bool:
        """Close a chat session"""
        try:
            updates = {
                "status": "closed",
                "closed_at": datetime.utcnow().isoformat()
            }
            
            result = await self.update_session(session_id, updates)
            return result is not None
            
        except Exception as e:
            logger.error(f"Error closing session {session_id}: {e}")
            return False
    
    async def create_message(
        self,
        session_id: str,
        role: str,
        content: str,
        message_type: str = "text",
        sender_id: Optional[UUID] = None,
        ai_generated: bool = False,
        ai_model: Optional[str] = None,
        intent: Optional[str] = None,
        entities: Optional[Dict[str, Any]] = None,
        actions: Optional[List[Dict[str, Any]]] = None,
        processing_time: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new chat message"""
        try:
            # Get session to get session UUID
            session = await self.get_session(session_id)
            if not session:
                raise Exception(f"Session {session_id} not found")
            
            data = {
                "session_id": session["id"],
                "role": role,
                "content": content,
                "message_type": message_type,
                "sender_id": str(sender_id) if sender_id else None,
                "ai_generated": ai_generated,
                "ai_model": ai_model,
                "intent": intent,
                "entities": entities or {},
                "actions": actions or [],
                "processing_time": processing_time,
                "metadata": metadata or {}
            }
            
            result = self.client.table("chat_messages").insert(data).execute()
            
            if result.data:
                logger.info(f"Created message in session {session_id}")
                return result.data[0]
            else:
                raise Exception("Failed to create message")
                
        except Exception as e:
            logger.error(f"Error creating message: {e}")
            raise
    
    async def get_session_messages(
        self,
        session_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get messages for a session"""
        try:
            # Get session UUID
            session = await self.get_session(session_id)
            if not session:
                return []
            
            result = self.client.table("chat_messages")\
                .select("*")\
                .eq("session_id", session["id"])\
                .eq("is_deleted", False)\
                .order("created_at", desc=False)\
                .range(offset, offset + limit - 1)\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error getting messages for session {session_id}: {e}")
            return []
    
    async def get_recent_context(
        self,
        session_id: str,
        max_messages: int = 20
    ) -> List[Dict[str, Any]]:
        """Get recent messages for context"""
        try:
            messages = await self.get_session_messages(session_id, limit=max_messages)
            return messages[-max_messages:] if messages else []
            
        except Exception as e:
            logger.error(f"Error getting recent context: {e}")
            return []
    
    async def search_knowledge_base(
        self,
        business_id: UUID,
        query_embedding: List[float],
        top_k: int = 5,
        content_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Search knowledge base using vector similarity"""
        try:
            # Note: This requires a custom RPC function in Supabase
            # For now, we'll do a simple text search
            query = self.client.table("chat_knowledge_base")\
                .select("*")\
                .eq("business_id", str(business_id))\
                .eq("is_active", True)\
                .limit(top_k)
            
            if content_types:
                query = query.in_("content_type", content_types)
            
            result = query.execute()
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return []
    
    async def get_business_context(self, business_id: UUID) -> Optional[Dict[str, Any]]:
        """Get business context information"""
        try:
            # Get business details
            business = self.client.table("businesses")\
                .select("*, business_details(*), business_categories(name)")\
                .eq("id", str(business_id))\
                .single()\
                .execute()
            
            if not business.data:
                return None
            
            # Get knowledge base count
            kb_count = self.client.table("chat_knowledge_base")\
                .select("id", count="exact")\
                .eq("business_id", str(business_id))\
                .eq("is_active", True)\
                .execute()
            
            # Get template count
            template_count = self.client.table("chat_templates")\
                .select("id", count="exact")\
                .eq("business_id", str(business_id))\
                .eq("is_active", True)\
                .execute()
            
            return {
                "business": business.data,
                "knowledge_base_count": kb_count.count if kb_count else 0,
                "template_count": template_count.count if template_count else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting business context: {e}")
            return None
    
    async def update_message_feedback(
        self,
        message_id: UUID,
        rating: int,
        comment: Optional[str] = None
    ) -> bool:
        """Update message feedback"""
        try:
            updates = {
                "feedback_rating": rating,
                "feedback_comment": comment
            }
            
            result = self.client.table("chat_messages")\
                .update(updates)\
                .eq("id", str(message_id))\
                .execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error updating message feedback: {e}")
            return False
    
    async def record_analytics(
        self,
        business_id: UUID,
        date: datetime,
        metrics: Dict[str, Any]
    ) -> bool:
        """Record chat analytics"""
        try:
            data = {
                "business_id": str(business_id),
                "date": date.date().isoformat(),
                **metrics
            }
            
            # Upsert analytics
            result = self.client.table("chat_analytics")\
                .upsert(data, on_conflict="business_id,date")\
                .execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error recording analytics: {e}")
            return False


# Global database service instance
db_service = DatabaseService()
