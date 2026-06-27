"""Supabase persistence for the recent-searches feed.

Degrades gracefully: when SUPABASE_URL/SERVICE_KEY are not configured, inserts
are no-ops and recent_searches returns empty, so the rest of the API works
without the history backend.

Env:
    SUPABASE_URL          https://<project>.supabase.co
    SUPABASE_SERVICE_KEY  service role key (server-side only)
"""

import os

from ...lib.types import SourceMode, VerdictEnum

_client = None


def is_configured() -> bool:
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    return url.startswith("http") and bool(key)


def _get_client():
    global _client
    if _client is None:
        from supabase import create_client

        _client = create_client(
            os.environ["SUPABASE_URL"],
            os.environ["SUPABASE_SERVICE_KEY"],
        )
    return _client


def insert_search(
    *,
    claim: str,
    claim_hash: str,
    verdict: VerdictEnum | str,
    confidence: float,
    source_mode: SourceMode | str,
) -> None:
    """Insert a row into `searches`. No-op if not configured; never raises."""
    if not is_configured():
        return
    mode = source_mode.value if isinstance(source_mode, SourceMode) else str(source_mode)
    row = {
        "claim": claim,
        "claim_hash": claim_hash,
        "verdict": verdict.value if isinstance(verdict, VerdictEnum) else str(verdict),
        "confidence": confidence,
        "source_mode": mode,
    }
    try:
        _get_client().table("searches").insert(row).execute()
    except Exception:  # noqa: BLE001 — history write is best-effort
        return


def recent_searches(limit: int = 20, offset: int = 0) -> tuple[list[dict], int]:
    """Return (rows, total) ordered by searched_at desc. Empty if not configured."""
    if not is_configured():
        return [], 0
    try:
        client = _get_client()
        resp = (
            client.table("searches")
            .select("id, claim, verdict, confidence, source_mode, searched_at", count="exact")
            .order("searched_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        return resp.data or [], resp.count or 0
    except Exception:  # noqa: BLE001
        return [], 0
