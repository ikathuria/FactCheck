"""Live Turso cache tests (skipped unless Turso is configured)."""

import time
import uuid

from src.features.cache import turso_cache

from .conftest import requires_turso


@requires_turso
def test_set_and_get_roundtrip():
    key = f"fc:test:{uuid.uuid4()}"
    turso_cache.set(key, {"hello": "world", "n": 1})
    assert turso_cache.get(key) == {"hello": "world", "n": 1}


@requires_turso
def test_ttl_expiry():
    key = f"fc:test:{uuid.uuid4()}"
    turso_cache.set(key, {"v": 1}, ttl_seconds=1)
    assert turso_cache.get(key) is not None
    time.sleep(2)
    assert turso_cache.get(key) is None


def test_get_returns_none_when_not_configured(monkeypatch):
    """With no Turso env, get() is a safe no-op returning None."""
    monkeypatch.delenv("TURSO_DATABASE_URL", raising=False)
    monkeypatch.delenv("TURSO_AUTH_TOKEN", raising=False)
    assert turso_cache.is_configured() is False
    assert turso_cache.get("anything") is None
