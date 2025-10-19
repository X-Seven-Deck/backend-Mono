"""
Redis Cache Service for Chat Communication

High-performance caching for sessions, messages, and rate limiting.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import timedelta
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class CacheService:
    """
    Redis Cache Service
    
    Features:
    - Session caching
    - Message caching
    - Rate limiting
    - Presence tracking
    - Typing indicators
    - User status
    """
    
    def __init__(self):
        self._initialized = False
        self.redis_client: Optional[redis.Redis] = None
        
        # Configuration
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", 6379))
        self.redis_db = int(os.getenv("REDIS_DB", 1))
        self.redis_password = os.getenv("REDIS_PASSWORD", "")
        
        # Default TTLs
        self.session_ttl = 3600  # 1 hour
        self.message_cache_ttl = 1800  # 30 minutes
        self.presence_ttl = 300  # 5 minutes
        self.typing_ttl = 10  # 10 seconds
    
    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = await redis.from_url(
                f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}",
                password=self.redis_password if self.redis_password else None,
                encoding="utf-8",
                decode_responses=True
            )
            
            # Test connection
            await self.redis_client.ping()
            
            self._initialized = True
            logger.info("Cache service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize cache service: {e}")
            raise
    
    # ============================================================================
    # SESSION CACHING
    # ============================================================================
    
    async def cache_session(
        self,
        session_id: str,
        session_data: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Cache session data"""
        try:
            key = f"session:{session_id}"
            value = json.dumps(session_data)
            
            await self.redis_client.setex(
                key,
                ttl or self.session_ttl,
                value
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error caching session: {e}")
            return False
    
    async def get_cached_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get cached session data"""
        try:
            key = f"session:{session_id}"
            value = await self.redis_client.get(key)
            
            if value:
                return json.loads(value)
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached session: {e}")
            return None
    
    async def invalidate_session(self, session_id: str) -> bool:
        """Invalidate session cache"""
        try:
            key = f"session:{session_id}"
            await self.redis_client.delete(key)
            return True
            
        except Exception as e:
            logger.error(f"Error invalidating session: {e}")
            return False
    
    async def extend_session_ttl(
        self,
        session_id: str,
        ttl: Optional[int] = None
    ) -> bool:
        """Extend session TTL"""
        try:
            key = f"session:{session_id}"
            await self.redis_client.expire(key, ttl or self.session_ttl)
            return True
            
        except Exception as e:
            logger.error(f"Error extending session TTL: {e}")
            return False
    
    # ============================================================================
    # MESSAGE CACHING
    # ============================================================================
    
    async def cache_recent_messages(
        self,
        session_id: str,
        messages: List[Dict[str, Any]],
        max_messages: int = 50
    ) -> bool:
        """Cache recent messages for quick retrieval"""
        try:
            key = f"messages:{session_id}"
            
            # Store as list
            pipeline = self.redis_client.pipeline()
            
            # Clear existing
            pipeline.delete(key)
            
            # Add messages (store as JSON strings)
            for message in messages[-max_messages:]:
                pipeline.rpush(key, json.dumps(message))
            
            # Set TTL
            pipeline.expire(key, self.message_cache_ttl)
            
            await pipeline.execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error caching messages: {e}")
            return False
    
    async def get_cached_messages(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get cached messages"""
        try:
            key = f"messages:{session_id}"
            
            # Get last N messages
            messages = await self.redis_client.lrange(key, -limit, -1)
            
            return [json.loads(msg) for msg in messages]
            
        except Exception as e:
            logger.error(f"Error getting cached messages: {e}")
            return []
    
    async def add_message_to_cache(
        self,
        session_id: str,
        message: Dict[str, Any],
        max_messages: int = 50
    ) -> bool:
        """Add single message to cache"""
        try:
            key = f"messages:{session_id}"
            
            # Add message
            await self.redis_client.rpush(key, json.dumps(message))
            
            # Trim to max messages
            await self.redis_client.ltrim(key, -max_messages, -1)
            
            # Extend TTL
            await self.redis_client.expire(key, self.message_cache_ttl)
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding message to cache: {e}")
            return False
    
    # ============================================================================
    # RATE LIMITING
    # ============================================================================
    
    async def check_rate_limit(
        self,
        identifier: str,
        max_requests: int = 100,
        window_seconds: int = 60
    ) -> bool:
        """
        Check rate limit for identifier.
        
        Args:
            identifier: Unique identifier (user_id, ip_address, etc.)
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds
        
        Returns:
            True if within limit, False if exceeded
        """
        try:
            key = f"rate_limit:{identifier}"
            
            # Get current count
            count = await self.redis_client.get(key)
            
            if count is None:
                # First request in window
                await self.redis_client.setex(key, window_seconds, 1)
                return True
            
            count = int(count)
            
            if count >= max_requests:
                return False
            
            # Increment count
            await self.redis_client.incr(key)
            return True
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return True  # Allow on error to not block service
    
    async def get_rate_limit_status(
        self,
        identifier: str,
        max_requests: int = 100
    ) -> Dict[str, Any]:
        """Get rate limit status for identifier"""
        try:
            key = f"rate_limit:{identifier}"
            
            count = await self.redis_client.get(key)
            ttl = await self.redis_client.ttl(key)
            
            if count is None:
                return {
                    "requests_made": 0,
                    "requests_remaining": max_requests,
                    "reset_in_seconds": 0
                }
            
            count = int(count)
            
            return {
                "requests_made": count,
                "requests_remaining": max(0, max_requests - count),
                "reset_in_seconds": ttl if ttl > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting rate limit status: {e}")
            return {"requests_made": 0, "requests_remaining": max_requests, "reset_in_seconds": 0}
    
    # ============================================================================
    # PRESENCE & TYPING INDICATORS
    # ============================================================================
    
    async def set_user_online(
        self,
        user_id: str,
        session_id: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Set user as online"""
        try:
            key = f"presence:{user_id}"
            
            presence_data = {
                "status": "online",
                "session_id": session_id,
                "timestamp": str(int(timedelta(seconds=0).total_seconds())),
                **(metadata or {})
            }
            
            await self.redis_client.setex(
                key,
                self.presence_ttl,
                json.dumps(presence_data)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting user online: {e}")
            return False
    
    async def set_user_offline(self, user_id: str) -> bool:
        """Set user as offline"""
        try:
            key = f"presence:{user_id}"
            await self.redis_client.delete(key)
            return True
            
        except Exception as e:
            logger.error(f"Error setting user offline: {e}")
            return False
    
    async def get_user_presence(self, user_id: str) -> Dict[str, Any]:
        """Get user presence status"""
        try:
            key = f"presence:{user_id}"
            value = await self.redis_client.get(key)
            
            if value:
                return json.loads(value)
            
            return {"status": "offline"}
            
        except Exception as e:
            logger.error(f"Error getting user presence: {e}")
            return {"status": "offline"}
    
    async def set_typing_indicator(
        self,
        session_id: str,
        user_id: str,
        is_typing: bool = True
    ) -> bool:
        """Set typing indicator for user in session"""
        try:
            key = f"typing:{session_id}:{user_id}"
            
            if is_typing:
                await self.redis_client.setex(key, self.typing_ttl, "1")
            else:
                await self.redis_client.delete(key)
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting typing indicator: {e}")
            return False
    
    async def get_typing_users(self, session_id: str) -> List[str]:
        """Get list of users currently typing in session"""
        try:
            pattern = f"typing:{session_id}:*"
            keys = await self.redis_client.keys(pattern)
            
            # Extract user IDs from keys
            user_ids = [key.split(":")[-1] for key in keys]
            
            return user_ids
            
        except Exception as e:
            logger.error(f"Error getting typing users: {e}")
            return []
    
    # ============================================================================
    # BUSINESS CONTEXT CACHING
    # ============================================================================
    
    async def cache_business_context(
        self,
        business_id: str,
        context_data: Dict[str, Any],
        ttl: int = 3600
    ) -> bool:
        """Cache business context for quick access"""
        try:
            key = f"business_context:{business_id}"
            value = json.dumps(context_data)
            
            await self.redis_client.setex(key, ttl, value)
            return True
            
        except Exception as e:
            logger.error(f"Error caching business context: {e}")
            return False
    
    async def get_business_context(self, business_id: str) -> Optional[Dict[str, Any]]:
        """Get cached business context"""
        try:
            key = f"business_context:{business_id}"
            value = await self.redis_client.get(key)
            
            if value:
                return json.loads(value)
            return None
            
        except Exception as e:
            logger.error(f"Error getting business context: {e}")
            return None
    
    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Generic set operation"""
        try:
            if ttl:
                await self.redis_client.setex(key, ttl, json.dumps(value))
            else:
                await self.redis_client.set(key, json.dumps(value))
            return True
            
        except Exception as e:
            logger.error(f"Error in set operation: {e}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """Generic get operation"""
        try:
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
            
        except Exception as e:
            logger.error(f"Error in get operation: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Generic delete operation"""
        try:
            await self.redis_client.delete(key)
            return True
            
        except Exception as e:
            logger.error(f"Error in delete operation: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            return await self.redis_client.exists(key) > 0
            
        except Exception as e:
            logger.error(f"Error checking existence: {e}")
            return False
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Cache service closed")


# Singleton instance
cache_service = CacheService()

