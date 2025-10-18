"""
Redis client for caching and memory management

Provides async Redis operations for LangGraph memory, caching, and session management.
"""

import redis.asyncio as aioredis
from redis.asyncio import Redis
from typing import Optional, Any, Dict
import json
from datetime import timedelta
from app.config import settings
from app.utils import logger


class RedisClient:
    """Async Redis client wrapper with convenience methods"""
    
    def __init__(self):
        self.client: Optional[Redis] = None
        self._connected = False
    
    async def connect(self) -> None:
        """Establish Redis connection"""
        try:
            self.client = await aioredis.from_url(
                f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}",
                password=settings.redis_password,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
            )
            # Test connection
            await self.client.ping()
            self._connected = True
            logger.info(f"Connected to Redis at {settings.redis_host}:{settings.redis_port}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close Redis connection"""
        if self.client:
            await self.client.close()
            self._connected = False
            logger.info("Disconnected from Redis")
    
    async def get(self, key: str) -> Optional[str]:
        """Get value by key"""
        if not self._connected:
            await self.connect()
        try:
            return await self.client.get(key)
        except Exception as e:
            logger.error(f"Redis GET error for key {key}: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: str, 
        ttl: Optional[int] = None
    ) -> bool:
        """Set key-value pair with optional TTL"""
        if not self._connected:
            await self.connect()
        try:
            if ttl:
                await self.client.setex(key, ttl, value)
            else:
                await self.client.set(key, value)
            return True
        except Exception as e:
            logger.error(f"Redis SET error for key {key}: {e}")
            return False
    
    async def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        """Get JSON value by key"""
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error for key {key}: {e}")
        return None
    
    async def set_json(
        self, 
        key: str, 
        value: Dict[str, Any], 
        ttl: Optional[int] = None
    ) -> bool:
        """Set JSON value with optional TTL"""
        try:
            json_str = json.dumps(value)
            return await self.set(key, json_str, ttl)
        except Exception as e:
            logger.error(f"JSON encode error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key"""
        if not self._connected:
            await self.connect()
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self._connected:
            await self.connect()
        try:
            return await self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis EXISTS error for key {key}: {e}")
            return False
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on key"""
        if not self._connected:
            await self.connect()
        try:
            await self.client.expire(key, seconds)
            return True
        except Exception as e:
            logger.error(f"Redis EXPIRE error for key {key}: {e}")
            return False
    
    async def hset(self, name: str, key: str, value: str) -> bool:
        """Set hash field"""
        if not self._connected:
            await self.connect()
        try:
            await self.client.hset(name, key, value)
            return True
        except Exception as e:
            logger.error(f"Redis HSET error for hash {name}, key {key}: {e}")
            return False
    
    async def hget(self, name: str, key: str) -> Optional[str]:
        """Get hash field"""
        if not self._connected:
            await self.connect()
        try:
            return await self.client.hget(name, key)
        except Exception as e:
            logger.error(f"Redis HGET error for hash {name}, key {key}: {e}")
            return None
    
    async def hgetall(self, name: str) -> Dict[str, str]:
        """Get all hash fields"""
        if not self._connected:
            await self.connect()
        try:
            return await self.client.hgetall(name)
        except Exception as e:
            logger.error(f"Redis HGETALL error for hash {name}: {e}")
            return {}
    
    async def lpush(self, key: str, *values: str) -> bool:
        """Push values to list (left)"""
        if not self._connected:
            await self.connect()
        try:
            await self.client.lpush(key, *values)
            return True
        except Exception as e:
            logger.error(f"Redis LPUSH error for key {key}: {e}")
            return False
    
    async def lrange(self, key: str, start: int, end: int) -> list:
        """Get list range"""
        if not self._connected:
            await self.connect()
        try:
            return await self.client.lrange(key, start, end)
        except Exception as e:
            logger.error(f"Redis LRANGE error for key {key}: {e}")
            return []
    
    async def incr(self, key: str) -> Optional[int]:
        """Increment key"""
        if not self._connected:
            await self.connect()
        try:
            return await self.client.incr(key)
        except Exception as e:
            logger.error(f"Redis INCR error for key {key}: {e}")
            return None


# Global Redis client instance
redis_client = RedisClient()
