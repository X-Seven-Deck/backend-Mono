"""Performance Engineering & Optimization"""
import logging
from typing import Any, Callable, Optional
import redis.asyncio as redis
from app.config import settings

logger = logging.getLogger(__name__)

class MultiLayerCacheManager:
    """Multi-layer caching strategy"""
    
    def __init__(self):
        self.l1_cache: dict = {}  # In-memory
        self.redis_client: Optional[redis.Redis] = None
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = await redis.from_url(
                f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
            )
        except Exception as e:
            logger.error(f"Redis connection error: {e}")
    
    async def get_with_fallback(
        self,
        key: str,
        fetch_func: Callable,
        ttl: int = 3600
    ) -> Any:
        """Multi-layer cache with fallback"""
        # L1: In-memory
        if key in self.l1_cache:
            return self.l1_cache[key]
        
        # L2: Redis
        if self.redis_client:
            try:
                value = await self.redis_client.get(key)
                if value:
                    self.l1_cache[key] = value
                    return value
            except Exception as e:
                logger.error(f"Redis get error: {e}")
        
        # Fetch from source
        value = await fetch_func()
        
        # Store in caches
        self.l1_cache[key] = value
        if self.redis_client:
            try:
                await self.redis_client.setex(key, ttl, value)
            except Exception as e:
                logger.error(f"Redis set error: {e}")
        
        return value

def get_cache_manager() -> MultiLayerCacheManager:
    return MultiLayerCacheManager()
