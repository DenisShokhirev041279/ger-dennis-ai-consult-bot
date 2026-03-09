import time
from cachetools import TTLCache

# In-memory rate limiter: 15 messages per minute per user
_cache = TTLCache(maxsize=10000, ttl=60)

def is_rate_limited(user_id: int) -> bool:
    """
    Check if the user has exceeded the message rate limit (15 per minute).
    Returns True if limited, False if allowed.
    """
    count = _cache.get(user_id, 0)
    if count >= 15:
        return True
    
    _cache[user_id] = count + 1
    return False
