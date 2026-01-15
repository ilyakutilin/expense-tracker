import hashlib
import json
from enum import Enum
from functools import wraps
from typing import Any, Callable

from loguru import logger
from pydantic import BaseModel, ValidationError
from redis import asyncio as aioredis

from app.core import exceptions as exc
from app.core.settings import settings


class Entity(str, Enum):
    ACCOUNT = "account"
    CURRENCY = "currency"
    TAG = "tag"
    TRANSACTION = "transaction"


class ContentType(str, Enum):
    DETAIL = "detail"
    LIST = "list"


class CachePrefix(BaseModel):
    entity: Entity
    content_type: ContentType

    def __str__(self) -> str:
        return f"{self.entity.value}:{self.content_type.value}"


class RedisCache:
    def __init__(self):
        self.redis: aioredis.Redis | None = None

    async def connect(self, url: str = settings.redis_settings.url):
        """Initialize Redis connection"""
        self.redis = await aioredis.from_url(
            url,
            encoding="utf-8",
            decode_responses=True,  # Get strings back, not bytes
        )

    async def disconnect(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.aclose()

    async def get(self, key: str) -> str | None:
        """Get raw value from cache"""
        if not self.redis:
            return None
        return await self.redis.get(key)

    async def set(
        self, key: str, value: str, expire: int = settings.redis_settings.EXPIRE_SECONDS
    ) -> bool:
        """Set raw value in cache with expiration"""
        if not self.redis:
            return False
        return await self.redis.set(key, value, ex=expire)

    async def delete(self, key: str) -> int:
        """Delete key from cache"""
        if not self.redis:
            return 0
        return await self.redis.delete(key)

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not self.redis:
            return 0

        keys = await self.redis.keys(pattern)
        if not keys:
            return 0

        return await self.redis.delete(*keys)

    async def clear_all(self) -> bool:
        """Clear entire cache"""
        if not self.redis:
            return False
        return await self.redis.flushdb()


# Global cache instance
cache = RedisCache()


def _serialize_value(value: Any) -> str:
    """
    Serialize value to JSON string.
    Handles Pydantic models, lists of models, and primitives.
    """
    if isinstance(value, BaseModel):
        # Single Pydantic model
        return value.model_dump_json()
    elif isinstance(value, list) and value and isinstance(value[0], BaseModel):
        # List of Pydantic models
        return json.dumps([item.model_dump() for item in value])
    elif isinstance(value, (dict, list, str, int, float, bool, type(None))):
        # Standard JSON-serializable types
        return json.dumps(value)
    else:
        # Fallback for other types
        return json.dumps(str(value))


def _deserialize_value(
    data: str, model_class: type[BaseModel]
) -> BaseModel | list[BaseModel]:
    """
    Deserialize JSON string back to original Pydantic schema.

    Args:
        data: JSON string from Redis
        model_class: Pydantic model class for deserialization
    """
    if not data:
        raise exc.CacheError("No data in cache")

    parsed: dict[str, Any] | list[dict[str, Any]] = json.loads(data)

    try:
        if isinstance(parsed, list):
            return [model_class.model_validate(item) for item in parsed]
        else:
            return model_class.model_validate(parsed)
    except ValidationError as e:
        raise exc.CacheError(f"Failed to validate JSON from cache: {e}")


def _validate_prefix(prefix_or_pattern: str) -> str:
    split = prefix_or_pattern.split(":", 2)
    if len(split) < 2:
        raise exc.CacheError(
            f"Prefix validation failed: wrong prefix structure: {prefix_or_pattern}"
        )

    try:
        validated_prefix = CachePrefix.model_validate(
            {"entity": split[0], "content_type": split[1]}
        )
        return str(validated_prefix)

    except ValidationError as e:
        raise exc.CacheError(f"Prefix validation failed: {e}")


def _extract_user_id(args: tuple) -> int:
    """
    Extract user_id from self.

    Args:
        args: Service method arguments tuple (first element should be 'self')

    Raises:
        CacheError: if there are no args, or if there are more than one arg
            (all arguments in the services are supposed to be keyword arguments),
            or if there is no user_id in self (only the user owned services are cached).

    Returns:
        user_id if found in self
    """
    if not args:
        raise exc.CacheError(
            "No args in the service method, so there is no self "
            "and it's not possible to extract user_id"
        )

    if len(args) > 1:
        raise exc.CacheError(
            f"There are {len(args)} args in the service method, while all arguments "
            "in the services are supposed to be keyword arguments"
        )

    if args and not hasattr(args[0], "user_id"):
        raise exc.CacheError("There is no user_id in the self of the service method")

    assert len(args) > 0
    return args[0].user_id


def _extract_object_id_kv(params: dict[str, Any]) -> tuple[str, int]:
    obj_id_kvs: list[tuple[str, int]] = []
    for k, v in params.items():
        if k.endswith("_id") and isinstance(v, int) and not isinstance(v, bool):
            obj_id_kvs.append((k, params.pop(k)))

    if len(obj_id_kvs) == 0:
        raise exc.CacheError("Could not find the object id key in kwargs")

    if len(obj_id_kvs) > 1:
        raise exc.CacheError(
            f"There are {len(obj_id_kvs)} id keys in kwargs while only one is expected"
        )

    return obj_id_kvs[0]


def _generate_cache_key(prefix: str, kwargs: dict[str, Any], user_id: int) -> str:
    """
    Generate unique cache key.
    Keys are deterministic - same params always produce same key.

    Format: prefix:user_id=X:param1=value1:param2=value2

    Args:
        prefix: Cache key prefix (e.g., 'transaction:list')
        kwargs: Dict of kwargs passed to the service method
        user_id: User ID to include in key (for multi-tenant isolation)

    Raises:
        CacheError: if the critical parts of the key to be generated are missing
            (like the object ID if applicable) or if the key generation fails
            for other reasons
    """
    key_parts = [_validate_prefix(prefix)]

    # Add user_id first
    key_parts.append(f"user_id={user_id}")

    # Get the object ID
    if ":detail" in prefix:
        obj_id_key, obj_id = _extract_object_id_kv(kwargs)
        key_parts.append(f"{obj_id_key}={obj_id}")

    # Sort kwargs for consistency
    for k, v in sorted(kwargs.items()):
        if isinstance(v, (str, int, float, bool)) or v is None:
            key_parts.append(f"{k}={v}")
        elif isinstance(v, (list, tuple)):
            # Handle lists/tuples (e.g., category_ids=[1,2,3])
            key_parts.append(f"{k}={','.join(map(str, v))}")
        elif isinstance(v, BaseModel):
            for field_name, field_value in v.model_dump(exclude_none=True).items():
                key_parts.append(f"{field_name}={field_value}")
        else:
            # Hash complex objects that couldn't be extracted
            key_parts.append(f"{k}={hashlib.md5(str(v).encode()).hexdigest()[:8]}")

    return ":".join(key_parts)


async def _invalidate_entire_entity(pattern: str):
    raw_entity = pattern.split(":", 1)[0]
    try:
        entity = Entity(raw_entity)
        logger.warning(f"The entire {entity.value} entity will now be invalidated")
        await cache.delete_pattern(f"{entity.value}*")
    except ValueError:
        logger.warning(
            f"Incorrect entity {raw_entity} - failed to invalidate. "
            "The entire cache DB will now be erased"
        )
        await cache.clear_all()


def cached(
    prefix: str,
    model_class: type[BaseModel],
    expire: int = settings.redis_settings.EXPIRE_SECONDS,
):
    """
    Decorator for caching function results with proper Pydantic serialization.
    Automatically extracts user_id from self if available.
    Expands Pydantic filter models into readable cache keys.

    Args:
        prefix: Cache key prefix (e.g., 'transaction:list', 'account:detail')
        model_class: Pydantic model class for deserialization
        expire: Cache expiration in seconds

    Examples:
        # Single item with user_id in self
        @cached(prefix="account:detail", expire=3600)
        async def get_account(self, account_id: int):
            # Key: "account:detail:user_id=123:account_id=5"

        # List with filter model
        @cached(prefix="account:list")
        async def get_expenses(self, filters: AccountFilters):
            # filters = AccountFilters(page=1, page_size=10, type='asset')
            # Key: "account:list:user_id=123:page=1:page_size=10:type=asset"
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # Extract user_id from self
                user_id: int = _extract_user_id(args)

                # Generate cache key
                cache_key = _generate_cache_key(prefix, kwargs, user_id)

                # Try to get from cache
                cached_data = await cache.get(cache_key)
                if cached_data:
                    return _deserialize_value(cached_data, model_class)
            except exc.CacheError as e:
                logger.warning(e)

            # Execute function and cache result
            result = await func(*args, **kwargs)

            # Serialize and cache
            if result is not None:
                serialized = _serialize_value(result)
                success = await cache.set(cache_key, serialized, expire)
                if not success:
                    logger.warning(f"Failed to set the cache by key {cache_key}")

            return result

        return wrapper

    return decorator


def invalidate_cache(*patterns: str):
    """
    Decorator to invalidate cache patterns after function execution.
    Supports parameter interpolation using curly braces.
    Automatically extracts user_id from self if available.

    Args:
        patterns: Cache key patterns to invalidate
            (supports wildcards and {param} interpolation)
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)

            if not patterns:
                logger.warning("No patterns to invalidate")

            try:
                # Extract user_id from self
                user_id = _extract_user_id(args)

                # Add user_id to kwargs for interpolation
                if user_id is not None:
                    kwargs["user_id"] = user_id
            except exc.CacheError as e:
                logger.warning(e)
                await _invalidate_entire_entity(patterns[0])

            # Invalidate specified cache patterns with interpolation
            for pattern in patterns:
                try:
                    # Interpolate parameters into normalized pattern
                    interpolated_pattern = pattern.format(**kwargs)

                    # Check if it's a wildcard pattern or exact key
                    if "*" in interpolated_pattern:
                        await cache.delete_pattern(interpolated_pattern)
                        return
                    else:
                        await cache.delete(interpolated_pattern)
                        return
                except KeyError as e:
                    logger.warning(
                        (
                            f"Warning: Cache invalidation pattern '{pattern}' "
                            f"references missing parameter: {e}"
                        )
                    )
                except Exception as e:
                    raise exc.CacheError(
                        f"Error interpolating cache pattern '{pattern}': {e}"
                    )

            await _invalidate_entire_entity(pattern)

            return result

        return wrapper

    return decorator
