"""
Cache Service for Dedicated Business Chat
Redis-based caching for sessions, messages, and context
"""

import logging
import json
from typing import Optional, Dict, Any, List
from datetime import timedelta

import redis.asyncio as redis
from app.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Redis cache service for chat data"""
    
    def __init__(self):
        """Initialize cache service"""
        self.redis_client: Optional[redis.Redis] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize Redis connection"""
        if self._initialized:
            return
        
        try:
            self.redis_client = await redis.from_url(
                f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}",
                password=settings.redis_password if settings.redis_password else None,
                encoding="utf-8",
                decode_responses=True
            )
            
            # Test connection
            await self.redis_client.ping()
            
            self._initialized = True
            logger.info("Cache service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize cache service: {e}")
            # Don't raise - allow service to work without cache
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
    
    def _session_key(self, session_id: str) -> str:
        """Generate Redis key for session"""
        return f"chat:session:{session_id}"
    
    def _messages_key(self, session_id: str) -> str:
        """Generate Redis key for messages"""
        return f"chat:messages:{session_id}"
    
    def _context_key(self, session_id: str) -> str:
        """Generate Redis key for context"""
        return f"chat:context:{session_id}"
    
    def _business_context_key(self, business_id: str) -> str:
        """Generate Redis key for business context"""
        return f"chat:business:{business_id}"
    
    async def cache_session(
        self,
        session_id: str,
        session_data: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Cache session data"""
        if not self._initialized:
            return False
        
        try:
            key = self._session_key(session_id)
            ttl = ttl or settings.session_cache_ttl
            
            await self.redis_client.setex(
                key,
                ttl,
                json.dumps(session_data, default=str)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error caching session: {e}")
            return False
    
    async def get_cached_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get cached session data"""
        if not self._initialized:
            return None
        
        try:
            key = self._session_key(session_id)
            data = await self.redis_client.get(key)
            
            if data:
                return json.loads(data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached session: {e}")
            return None
    
    async def cache_messages(
        self,
        session_id: str,
        messages: List[Dict[str, Any]],
        ttl: Optional[int] = None
    ) -> bool:
        """Cache session messages"""
        if not self._initialized:
            return False
        
        try:
            key = self._messages_key(session_id)
            ttl = ttl or settings.cache_ttl
            
            await self.redis_client.setex(
                key,
                ttl,
                json.dumps(messages, default=str)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error caching messages: {e}")
            return False
    
    async def get_cached_messages(self, session_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached messages"""
        if not self._initialized:
            return None
        
        try:
            key = self._messages_key(session_id)
            data = await self.redis_client.get(key)
            
            if data:
                return json.loads(data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached messages: {e}")
            return None
    
    async def append_message(
        self,
        session_id: str,
        message: Dict[str, Any]
    ) -> bool:
        """Append a message to cached messages"""
        if not self._initialized:
            return False
        
        try:
            messages = await self.get_cached_messages(session_id) or []
            messages.append(message)
            
            return await self.cache_messages(session_id, messages)
            
        except Exception as e:
            logger.error(f"Error appending message: {e}")
            return False
    
    async def cache_business_context(
        self,
        business_id: str,
        context: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Cache business context"""
        if not self._initialized:
            return False
        
        try:
            key = self._business_context_key(business_id)
            ttl = ttl or settings.cache_ttl * 2  # Cache business context longer
            
            await self.redis_client.setex(
                key,
                ttl,
                json.dumps(context, default=str)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error caching business context: {e}")
            return False
    
    async def get_cached_business_context(self, business_id: str) -> Optional[Dict[str, Any]]:
        """Get cached business context"""
        if not self._initialized:
            return None
        
        try:
            key = self._business_context_key(business_id)
            data = await self.redis_client.get(key)
            
            if data:
                return json.loads(data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached business context: {e}")
            return None
    
    async def invalidate_session(self, session_id: str) -> bool:
        """Invalidate all cache for a session"""
        if not self._initialized:
            return False
        
        try:
            keys = [
                self._session_key(session_id),
                self._messages_key(session_id),
                self._context_key(session_id)
            ]
            
            await self.redis_client.delete(*keys)
            return True
            
        except Exception as e:
            logger.error(f"Error invalidating session cache: {e}")
            return False
    
    async def set_rate_limit(
        self,
        identifier: str,
        limit: int,
        window: int
    ) -> bool:
        """Set rate limit for identifier"""
        if not self._initialized:
            return True  # Allow if cache not available
        
        try:
            key = f"ratelimit:{identifier}"
            current = await self.redis_client.get(key)
            
            if current and int(current) >= limit:
                return False
            
            pipe = self.redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, window)
            await pipe.execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting rate limit: {e}")
            return True  # Allow on error


# Global cache service instance
cache_service = CacheService()
