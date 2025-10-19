"""
Database Service for Chat Communication

Enterprise-grade database operations for chat sessions, messages, and analytics.
"""

import os
import sys
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import uuid4

# Add shared libs to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../shared"))

from libs.supabase_client import SupabaseManager

logger = logging.getLogger(__name__)


class DatabaseService:
    """
    Database service for chat operations with Supabase.
    
    Handles:
    - Chat session management
    - Message storage and retrieval
    - Participant management
    - Knowledge base operations
    - Analytics tracking
    - Template management
    """
    
    def __init__(self):
        self._initialized = False
        self.supabase: Optional[SupabaseManager] = None
    
    async def initialize(self):
        """Initialize database connection"""
        try:
            self.supabase = SupabaseManager(use_service_key=True)
            self._initialized = True
            logger.info("Database service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database service: {e}")
            raise
    
    # ============================================================================
    # CHAT SESSION OPERATIONS
    # ============================================================================
    
    async def create_chat_session(
        self,
        session_type: str,  # dedicated, dashboard, global
        business_id: Optional[str] = None,
        user_id: Optional[str] = None,
        channel: str = "web",
        context: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Create a new chat session.
        
        Args:
            session_type: Type of chat session
            business_id: Business ID (required for dedicated/dashboard)
            user_id: User ID
            channel: Communication channel
            context: Session context data
            metadata: Additional metadata
        
        Returns:
            Created session data
        """
        try:
            session_id = f"{session_type}_{uuid4().hex[:12]}"
            
            session_data = {
                "session_id": session_id,
                "session_type": session_type,
                "business_id": business_id,
                "user_id": user_id,
                "status": "active",
                "channel": channel,
                "context": context or {},
                "metadata": metadata or {},
                "message_count": 0,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = await self.supabase.insert("chat_sessions", session_data)
            
            logger.info(f"Created chat session: {session_id}")
            return result[0]
            
        except Exception as e:
            logger.error(f"Error creating chat session: {e}")
            raise
    
    async def get_chat_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get chat session by ID"""
        try:
            result = await self.supabase.select(
                "chat_sessions",
                columns="*",
                filters={"session_id": session_id}
            )
            
            if result:
                return result[0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting chat session: {e}")
            return None
    
    async def update_chat_session(
        self,
        session_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update chat session"""
        try:
            updates["updated_at"] = datetime.utcnow().isoformat()
            
            result = await self.supabase.update(
                "chat_sessions",
                data=updates,
                filters={"session_id": session_id}
            )
            
            if result:
                logger.info(f"Updated chat session: {session_id}")
                return result[0]
            return None
            
        except Exception as e:
            logger.error(f"Error updating chat session: {e}")
            raise
    
    async def close_chat_session(
        self,
        session_id: str,
        reason: Optional[str] = None
    ) -> bool:
        """Close chat session"""
        try:
            updates = {
                "status": "closed",
                "closed_at": datetime.utcnow().isoformat()
            }
            
            if reason:
                updates["metadata"] = {"close_reason": reason}
            
            await self.update_chat_session(session_id, updates)
            logger.info(f"Closed chat session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error closing chat session: {e}")
            return False
    
    async def get_active_sessions_for_business(
        self,
        business_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get active sessions for a business"""
        try:
            query = self.supabase.client.table("chat_sessions").select("*")
            query = query.eq("business_id", business_id)
            query = query.eq("status", "active")
            query = query.order("last_message_at", desc=True)
            query = query.limit(limit)
            
            result = query.execute()
            return result.data
            
        except Exception as e:
            logger.error(f"Error getting active sessions: {e}")
            return []
    
    # ============================================================================
    # MESSAGE OPERATIONS
    # ============================================================================
    
    async def add_message(
        self,
        session_id: str,
        role: str,  # user, assistant, system, agent
        content: str,
        sender_id: Optional[str] = None,
        sender_name: Optional[str] = None,
        message_type: str = "text",
        ai_generated: bool = False,
        ai_model: Optional[str] = None,
        intent: Optional[str] = None,
        entities: Optional[Dict] = None,
        actions: Optional[List] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Add message to chat session.
        
        Args:
            session_id: Session ID
            role: Message role
            content: Message content
            sender_id: Sender user ID
            sender_name: Sender display name
            message_type: Type of message
            ai_generated: Whether AI generated
            ai_model: AI model used
            intent: Detected intent
            entities: Extracted entities
            actions: Actions taken
            metadata: Additional metadata
        
        Returns:
            Created message data
        """
        try:
            message_data = {
                "session_id": await self._get_session_uuid(session_id),
                "role": role,
                "content": content,
                "sender_id": sender_id,
                "sender_name": sender_name,
                "message_type": message_type,
                "ai_generated": ai_generated,
                "ai_model": ai_model,
                "intent": intent,
                "entities": entities or {},
                "actions": actions or [],
                "metadata": metadata or {},
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = await self.supabase.insert("chat_messages", message_data)
            
            # Update session last_message_at
            await self.update_chat_session(
                session_id,
                {"last_message_at": datetime.utcnow().isoformat()}
            )
            
            logger.info(f"Added message to session {session_id}")
            return result[0]
            
        except Exception as e:
            logger.error(f"Error adding message: {e}")
            raise
    
    async def get_session_messages(
        self,
        session_id: str,
        limit: int = 50,
        offset: int = 0,
        include_deleted: bool = False
    ) -> List[Dict[str, Any]]:
        """Get messages for a session"""
        try:
            session_uuid = await self._get_session_uuid(session_id)
            
            query = self.supabase.client.table("chat_messages").select("*")
            query = query.eq("session_id", session_uuid)
            
            if not include_deleted:
                query = query.eq("is_deleted", False)
            
            query = query.order("created_at", desc=False)
            query = query.range(offset, offset + limit - 1)
            
            result = query.execute()
            return result.data
            
        except Exception as e:
            logger.error(f"Error getting session messages: {e}")
            return []
    
    async def update_message(
        self,
        message_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update message"""
        try:
            updates["edited_at"] = datetime.utcnow().isoformat()
            
            result = await self.supabase.update(
                "chat_messages",
                data=updates,
                filters={"id": message_id}
            )
            
            if result:
                return result[0]
            return None
            
        except Exception as e:
            logger.error(f"Error updating message: {e}")
            raise
    
    async def delete_message(self, message_id: str, hard_delete: bool = False) -> bool:
        """Delete message (soft or hard)"""
        try:
            if hard_delete:
                await self.supabase.delete(
                    "chat_messages",
                    filters={"id": message_id}
                )
            else:
                await self.update_message(
                    message_id,
                    {
                        "is_deleted": True,
                        "deleted_at": datetime.utcnow().isoformat()
                    }
                )
            
            logger.info(f"Deleted message: {message_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting message: {e}")
            return False
    
    # ============================================================================
    # KNOWLEDGE BASE OPERATIONS
    # ============================================================================
    
    async def add_knowledge_base_item(
        self,
        business_id: str,
        title: str,
        content: str,
        content_type: str,
        embedding: Optional[List[float]] = None,
        tags: Optional[List[str]] = None,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add knowledge base item"""
        try:
            kb_data = {
                "business_id": business_id,
                "title": title,
                "content": content,
                "content_type": content_type,
                "embedding": embedding,
                "tags": tags or [],
                "category": category,
                "is_active": True,
                "usage_count": 0,
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = await self.supabase.insert("chat_knowledge_base", kb_data)
            
            logger.info(f"Added knowledge base item: {title}")
            return result[0]
            
        except Exception as e:
            logger.error(f"Error adding knowledge base item: {e}")
            raise
    
    async def search_knowledge_base(
        self,
        business_id: str,
        query_embedding: List[float],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search knowledge base using vector similarity"""
        try:
            # Use Supabase function for vector search
            result = self.supabase.client.rpc(
                "search_knowledge_base",
                {
                    "p_business_id": business_id,
                    "p_query_embedding": query_embedding,
                    "p_limit": limit
                }
            ).execute()
            
            return result.data
            
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return []
    
    # ============================================================================
    # ANALYTICS OPERATIONS
    # ============================================================================
    
    async def record_chat_analytics(
        self,
        business_id: str,
        date: Optional[str] = None,
        metrics: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Record or update chat analytics for a date"""
        try:
            if not date:
                date = datetime.utcnow().date().isoformat()
            
            # Check if record exists
            existing = await self.supabase.select(
                "chat_analytics",
                filters={"business_id": business_id, "date": date}
            )
            
            if existing:
                # Update existing record
                result = await self.supabase.update(
                    "chat_analytics",
                    data=metrics or {},
                    filters={"business_id": business_id, "date": date}
                )
                return result[0]
            else:
                # Create new record
                analytics_data = {
                    "business_id": business_id,
                    "date": date,
                    **(metrics or {}),
                    "created_at": datetime.utcnow().isoformat()
                }
                
                result = await self.supabase.insert("chat_analytics", analytics_data)
                return result[0]
                
        except Exception as e:
            logger.error(f"Error recording analytics: {e}")
            raise
    
    async def get_chat_analytics(
        self,
        business_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """Get chat analytics for date range"""
        try:
            query = self.supabase.client.table("chat_analytics").select("*")
            query = query.eq("business_id", business_id)
            
            if start_date:
                query = query.gte("date", start_date)
            if end_date:
                query = query.lte("date", end_date)
            
            query = query.order("date", desc=True)
            query = query.limit(limit)
            
            result = query.execute()
            return result.data
            
        except Exception as e:
            logger.error(f"Error getting analytics: {e}")
            return []
    
    # ============================================================================
    # TEMPLATE OPERATIONS
    # ============================================================================
    
    async def get_chat_templates(
        self,
        business_id: str,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get chat templates for business"""
        try:
            filters = {"business_id": business_id, "is_active": True}
            if category:
                filters["category"] = category
            
            result = await self.supabase.select(
                "chat_templates",
                filters=filters
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting templates: {e}")
            return []
    
    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    
    async def _get_session_uuid(self, session_id: str) -> str:
        """Get UUID for session_id (query by session_id, return id)"""
        try:
            result = await self.supabase.select(
                "chat_sessions",
                columns="id",
                filters={"session_id": session_id}
            )
            
            if result:
                return result[0]["id"]
            raise ValueError(f"Session not found: {session_id}")
            
        except Exception as e:
            logger.error(f"Error getting session UUID: {e}")
            raise


# Singleton instance
db_service = DatabaseService()

