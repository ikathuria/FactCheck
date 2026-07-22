"""Result cache backed by Turso (libSQL), 7-day TTL.

Turso/SQLite has no native key expiry, so TTL is emulated: every row carries an
`expires_at` unix timestamp; reads ignore expired rows and each write also
sweeps them. Uses the shared client in `lib.turso`.

Degrades gracefully: when Turso is not configured, get() -> None and set() is a
no-op, so /verify still works (just re-running the pipeline each time).
"""

import json
import time

from ...lib import turso

DEFAULT_TTL_SECONDS = 7 * 24 * 60 * 60  # 604800


def is_configured() -> bool:
    return turso.is_configured()


def get(key: str) -> dict | None:
    """Return the cached dict for key, or None on miss / expired / not-configured / error."""
    if not is_configured():
        return None
    try:
        rs = turso.get_client().execute(
            "SELECT value FROM cache WHERE key = ? AND expires_at > ?",
            [key, int(time.time())],
        )
        if not rs.rows:
            return None
        return json.loads(rs.rows[0]["value"])
    except Exception:  # noqa: BLE001 — cache must never break the request path
        return None


def set(key: str, value: dict, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> None:
    """Store value (JSON) under key with a TTL, and sweep expired rows. No-op if not configured."""
    if not is_configured():
        return
    now = int(time.time())
    try:
        from libsql_client import Statement

        turso.get_client().batch(
            [
                Statement(
                    "INSERT OR REPLACE INTO cache (key, value, expires_at) VALUES (?, ?, ?)",
                    [key, json.dumps(value, default=str), now + ttl_seconds],
                ),
                Statement("DELETE FROM cache WHERE expires_at <= ?", [now]),
            ]
        )
    except Exception:  # noqa: BLE001 — best-effort cache write
        return
