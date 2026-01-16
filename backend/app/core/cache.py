import hashlib
import json
from functools import wraps
from typing import Any, Callable

from loguru import logger
from pydantic import BaseModel, ValidationError
from redis import asyncio as aioredis

from app.core import exceptions as exc
from app.core.settings import settings
from app.schemas.cache import CachePattern


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

    async def delete(self, pattern: str) -> int:
        if not self.redis:
            return 0

        if "*" in pattern:
            keys = await self.redis.keys(pattern)
            if not keys:
                return 0
            return await self.redis.delete(*keys)
        else:
            return await self.redis.delete(pattern)

    async def clear_all(self) -> bool:
        """Clear entire cache"""
        if not self.redis:
            return False
        return await self.redis.flushdb()


# Global cache instance
cache = RedisCache()


def _serialize_value(value: Any) -> str:
    if isinstance(value, BaseModel):
        # Single Pydantic model
        return value.model_dump_json()
    elif isinstance(value, list):
        if value and all(isinstance(item, BaseModel) for item in value):
            return json.dumps([item.model_dump() for item in value])
        else:
            return json.dumps(value)
    elif isinstance(value, (dict, list, str, int, float, bool, type(None))):
        # Standard JSON-serializable types
        return json.dumps(value)
    else:
        # Fallback for other types
        return json.dumps(str(value))


def _deserialize_value(
    data: str, model_class: type[BaseModel]
) -> BaseModel | list[BaseModel]:
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


def _extract_user_id(args: tuple) -> int:
    if not args:
        raise exc.CacheError(
            "No args in the service method, so there is no self "
            "and it's not possible to extract user_id"
        )

    for arg in args:
        user_id = getattr(arg, "user_id", None)
        if user_id and isinstance(user_id, int):
            return user_id

    raise exc.CacheError(f"User ID has not been found in args: {args}")


def _interpolate_pattern(
    pattern: CachePattern, args: tuple[Any], kwargs: dict[str, Any]
) -> tuple[str, dict[str, Any]]:
    if pattern.is_user_owned:
        user_id: int = _extract_user_id(args)
        kwargs["user_id"] = user_id

    try:
        interpolated_pattern = str(pattern).format(**kwargs)
    except KeyError as e:
        raise exc.CacheError(
            f"Failed to interpolate the cache pattern: {e} is missing from kwargs"
        )

    remaining_kwargs = kwargs.copy()
    if pattern.obj_id_key:
        remaining_kwargs.pop(pattern.obj_id_key)

    return interpolated_pattern, remaining_kwargs


def _generate_cache_key(
    pattern: CachePattern, args: tuple[Any], kwargs: dict[str, Any]
) -> str:
    interpolated_pattern, remaining_kwargs = _interpolate_pattern(pattern, args, kwargs)

    key_parts: list[str] = [interpolated_pattern]

    for k, v in sorted(remaining_kwargs.items()):
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


async def _emergency_invalidation(entity: str):
    delete_count = await cache.delete(entity + "*")
    if delete_count == 0:
        logger.warning(
            (
                f"Failed to invalidate cache for the entire {entity} entity. "
                "Will flush the entire cache now"
            )
        )
        success = await cache.clear_all()
        if success:
            logger.warning(
                (
                    "The entire cache has been flushed. This should not have happened "
                    "under normal operation and requires further troubleshoting"
                )
            )
        else:
            logger.warning("An attempt to flush the entire cache DB failed")
    else:
        logger.warning(
            (
                f"Cache for the entire {entity} entity has been deleted. This should "
                "not have happened under normal operation and requires further "
                "troubleshoting"
            )
        )


def cached(
    *,
    pattern: CachePattern,
    response_model: type[BaseModel],
    expire: int = settings.redis_settings.EXPIRE_SECONDS,
):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key: str = ""
            try:
                # Generate cache key
                cache_key = _generate_cache_key(pattern, args, kwargs)

                # Try to get from cache
                cached_data = await cache.get(cache_key)
                if cached_data:
                    deserialized = _deserialize_value(cached_data, response_model)
                    logger.info(f"Cache hit for {cache_key}")
                    return deserialized
            except exc.CacheError as e:
                logger.warning(e)

            logger.info("No data in cache, will query the DB")
            result = await func(*args, **kwargs)

            # Serialize and cache
            if result is not None and cache_key:
                serialized = _serialize_value(result)
                success = await cache.set(cache_key, serialized, expire)
                if not success:
                    logger.warning(f"Failed to set the cache by key {cache_key}")

            return result

        return wrapper

    return decorator


def invalidate_cache(*patterns: CachePattern):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)

            for pattern in patterns:
                try:
                    interpolated_pattern, _ = _interpolate_pattern(
                        pattern, args, kwargs
                    )

                    deleted_count = await cache.delete(interpolated_pattern + "*")
                    if pattern.obj_id_key and deleted_count == 0:
                        logger.warning(
                            (
                                f"Key following the pattern {str(pattern)} has not "
                                "been found in cache. Will invalidate cache for the "
                                f"entire {pattern.entity} entity"
                            )
                        )
                        await _emergency_invalidation(pattern.entity.value)

                except exc.CacheError as e:
                    logger.warning(
                        (
                            f"Failed to invalidate cache for pattern {str(pattern)}: "
                            f"{e}. Will invalidate cache for the entire "
                            f"{pattern.entity} entity"
                        )
                    )
                    await _emergency_invalidation(pattern.entity.value)

            return result

        return wrapper

    return decorator
