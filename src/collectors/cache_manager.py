"""
Cache manager for NBA data collection using Redis.
"""
import json
import logging
from typing import Any, Optional
import redis
import pandas as pd
from functools import wraps

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self, host='localhost', port=6379, db=0, expire_time=86400):
        """Initialize Redis cache manager."""
        self.redis_client = redis.Redis(host=host, port=port, db=db)
        self.expire_time = expire_time  # Default cache expiration of 24 hours
    
    def _serialize_value(self, value: Any) -> str:
        """Serialize value for Redis storage."""
        if isinstance(value, pd.DataFrame):
            return value.to_json(orient='split')
        return json.dumps(value)
    
    def _deserialize_value(self, value: str, return_type: str = 'dict') -> Any:
        """Deserialize value from Redis storage."""
        if value is None:
            return None
        
        if return_type == 'dataframe':
            return pd.read_json(value, orient='split')
        return json.loads(value)
    
    def get(self, key: str, return_type: str = 'dict') -> Optional[Any]:
        """Get value from cache."""
        try:
            value = self.redis_client.get(key)
            return self._deserialize_value(value, return_type) if value else None
        except Exception as e:
            logger.error(f"Error retrieving from cache: {str(e)}")
            return None
    
    def set(self, key: str, value: Any) -> bool:
        """Set value in cache with expiration."""
        try:
            serialized_value = self._serialize_value(value)
            return self.redis_client.setex(key, self.expire_time, serialized_value)
        except Exception as e:
            logger.error(f"Error setting cache: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"Error deleting from cache: {str(e)}")
            return False

def cache_result(prefix: str = '', expire_time: int = None):
    """Decorator for caching function results."""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Generate cache key
            key = f"{prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            cache_manager = getattr(self, 'cache_manager', None)
            if cache_manager:
                cached_result = cache_manager.get(key)
                if cached_result is not None:
                    logger.debug(f"Cache hit for {key}")
                    return cached_result
            
            # Execute function and cache result
            result = func(self, *args, **kwargs)
            if cache_manager and result is not None:
                cache_manager.set(key, result)
            
            return result
        return wrapper
    return decorator 