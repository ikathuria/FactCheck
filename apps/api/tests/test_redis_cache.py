"""Live Redis cache tests (skipped unless Upstash is configured)."""

import time
import uuid

from src.features.cache import redis_cache

from .conftest import requires_redis


@requires_redis
def test_set_and_get_roundtrip():
    key = f"fc:test:{uuid.uuid4()}"
    redis_cache.set(key, {"hello": "world", "n": 1})
    assert redis_cache.get(key) == {"hello": "world", "n": 1}


@requires_redis
def test_ttl_expiry():
    key = f"fc:test:{uuid.uuid4()}"
    redis_cache.set(key, {"v": 1}, ttl_seconds=1)
    assert redis_cache.get(key) is not None
    time.sleep(2)
    assert redis_cache.get(key) is None


def test_get_returns_none_when_not_configured(monkeypatch):
    """With no Upstash env, get() is a safe no-op returning None."""
    monkeypatch.delenv("UPSTASH_REDIS_REST_URL", raising=False)
    monkeypatch.delenv("UPSTASH_REDIS_REST_TOKEN", raising=False)
    assert redis_cache.is_configured() is False
    assert redis_cache.get("anything") is None
