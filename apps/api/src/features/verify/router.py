"""POST /verify endpoint with Redis caching + Supabase history."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException

from ...lib.types import VerifyRequest, VerifyResponse
from ..cache import keys, redis_cache
from ..history import store
from . import pipeline

router = APIRouter()


@router.post("/verify", response_model=VerifyResponse)
def verify(request: VerifyRequest) -> VerifyResponse:
    """Run the 5-agent fact-check pipeline, with 7-day Redis caching.

    On cache hit: return the stored result with cached=true.
    On miss: run the pipeline, store in Redis (7-day TTL), record a summary row
    in Supabase, and return cached=false.
    """
    key = keys.cache_key(request.claim, request.source_mode)

    cached = redis_cache.get(key)
    if cached is not None:
        cached["cached"] = True
        return VerifyResponse(**cached)

    try:
        result = pipeline.run(claim=request.claim, source_mode=request.source_mode)
    except Exception as e:  # noqa: BLE001 — surface pipeline failures as 502
        raise HTTPException(status_code=502, detail=f"Verification failed: {e}") from e

    now = datetime.now(timezone.utc)
    result.cached = False
    result.cached_at = now
    result.ttl_expires_at = now + timedelta(seconds=redis_cache.DEFAULT_TTL_SECONDS)

    # Best-effort persistence (both layers no-op when not configured).
    redis_cache.set(key, result.model_dump(mode="json"))
    store.insert_search(
        claim=result.claim,
        claim_hash=key,
        verdict=result.verdict,
        confidence=result.confidence,
        source_mode=result.source_mode,
    )

    return result
