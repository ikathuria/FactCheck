"""Redis result cache (Upstash REST), 7-day TTL.

Degrades gracefully: when UPSTASH_REDIS_REST_URL/TOKEN are not configured, all
operations become no-ops (get -> None, set -> nothing) so /verify still works
without a cache, just re-running the pipeline each time.

Env:
    UPSTASH_REDIS_REST_URL    https://...upstash.io
    UPSTASH_REDIS_REST_TOKEN
"""

import json
import os

DEFAULT_TTL_SECONDS = 7 * 24 * 60 * 60  # 604800

_client = None


def is_configured() -> bool:
    url = os.environ.get("UPSTASH_REDIS_REST_URL", "")
    token = os.environ.get("UPSTASH_REDIS_REST_TOKEN", "")
    return url.startswith("http") and bool(token)


def _get_client():
    global _client
    if _client is None:
        from upstash_redis import Redis

        _client = Redis(
            url=os.environ["UPSTASH_REDIS_REST_URL"],
            token=os.environ["UPSTASH_REDIS_REST_TOKEN"],
        )
    return _client


def get(key: str) -> dict | None:
    """Return the cached dict for key, or None on miss / not-configured / error."""
    if not is_configured():
        return None
    try:
        raw = _get_client().get(key)
        return json.loads(raw) if raw else None
    except Exception:  # noqa: BLE001 — cache must never break the request path
        return None


def set(key: str, value: dict, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> None:
    """Store value (JSON-serialized) under key with a TTL. No-op if not configured."""
    if not is_configured():
        return
    try:
        _get_client().set(key, json.dumps(value, default=str), ex=ttl_seconds)
    except Exception:  # noqa: BLE001 — best-effort cache write
        return
