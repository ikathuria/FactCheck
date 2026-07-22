"""Turso (libSQL) persistence for the recent-searches feed.

Uses the shared client in `lib.turso`. Degrades gracefully: when Turso is not
configured, inserts are no-ops and recent_searches returns empty, so the rest of
the API works without the history backend.
"""

import uuid
from datetime import datetime, timezone

from ...lib import turso
from ...lib.types import SourceMode, VerdictEnum


def is_configured() -> bool:
    return turso.is_configured()


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
    v = verdict.value if isinstance(verdict, VerdictEnum) else str(verdict)
    try:
        turso.get_client().execute(
            "INSERT INTO searches "
            "(id, claim, claim_hash, verdict, confidence, source_mode, searched_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                uuid.uuid4().hex,
                claim,
                claim_hash,
                v,
                confidence,
                mode,
                datetime.now(timezone.utc).isoformat(),
            ],
        )
    except Exception:  # noqa: BLE001 — history write is best-effort
        return


def recent_searches(limit: int = 20, offset: int = 0) -> tuple[list[dict], int]:
    """Return (rows, total) ordered by searched_at desc. Empty if not configured."""
    if not is_configured():
        return [], 0
    try:
        client = turso.get_client()
        rs = client.execute(
            "SELECT id, claim, verdict, confidence, source_mode, searched_at "
            "FROM searches ORDER BY searched_at DESC LIMIT ? OFFSET ?",
            [limit, offset],
        )
        total = client.execute("SELECT COUNT(*) AS n FROM searches").rows[0]["n"]
        return [row.asdict() for row in rs.rows], int(total)
    except Exception:  # noqa: BLE001
        return [], 0
