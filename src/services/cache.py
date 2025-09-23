import json
import redis.asyncio as redis
import logging

from src.conf.config import settings
from src.schemas import UserResponse


logger = logging.getLogger(__name__)

#: Global Redis client instance (async)
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    encoding="utf-8",
    decode_responses=True,
)

#: Default cache expiration time in seconds (5 minutes)
CACHE_EXPIRE_SECONDS = 300


async def cache_user(user):
    
    """
    Cache a user object in Redis.

    - Stores user data under key ``user:{email}``.
    - Expires after ``CACHE_EXPIRE_SECONDS``.

    :param user: SQLAlchemy user model instance.
    :type user: User
    :return: None
    :rtype: None

    Example::

        await cache_user(user)
        # Redis key: "user:test@example.com"
        # Value: JSON {id, username, email, created_at, avatar, role}
    """    
    
    key = f"user:{user.email}"
    value = json.dumps(
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "created_at": str(user.created_at),
            "avatar": user.avatar,
            "role": user.role,
        }
    )
    await redis_client.set(key, value, ex=CACHE_EXPIRE_SECONDS)
    logger.info(f"USER cached in Redis (set): {user.email}")


async def get_cached_user(email: str):
    
    """
    Retrieve a cached user from Redis.

    - Looks up by key ``user:{email}``.
    - If found, returns a :class:`UserResponse` Pydantic model.
    - If not found, returns ``None``.

    :param email: Email address of the user.
    :type email: str
    :return: UserResponse if cached, else None.
    :rtype: UserResponse | None

    Example::

        user = await get_cached_user("test@example.com")
        if user:
            print(user.username)
    """    
    
    key = f"user:{email}"
    value = await redis_client.get(key)
    if value:
        data = json.loads(value)
        # повертаємо Pydantic модель
        logger.info(f"USER fetched from Redis (get): {email}")
        return UserResponse(**data)
    return None
