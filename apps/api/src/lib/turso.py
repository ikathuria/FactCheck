"""Shared Turso (libSQL) client for the result cache and search history.

Both storage layers live in a single Turso database, so this module owns the
one connection and the one `is_configured()` check they share.

Degrades gracefully: when TURSO_DATABASE_URL/TURSO_AUTH_TOKEN are absent,
`is_configured()` is False and callers become no-ops, so the API works with no
storage backend at all.

Env:
    TURSO_DATABASE_URL    libsql://<db>-<org>.turso.io (the URL `turso db show` prints)
    TURSO_AUTH_TOKEN      database auth token (`turso db tokens create <db>`)
"""

import os

_client = None

_SCHEMES = ("libsql://", "wss://", "https://", "http://")


def is_configured() -> bool:
    url = os.environ.get("TURSO_DATABASE_URL", "")
    token = os.environ.get("TURSO_AUTH_TOKEN", "")
    return url.startswith(_SCHEMES) and bool(token)


def _http_url(url: str) -> str:
    """Normalize a Turso URL to the HTTP transport.

    The Turso CLI hands out `libsql://` URLs, which libsql-client maps to a
    WebSocket (Hrana-over-wss) handshake that current Turso servers reject.
    The HTTP transport (`https://`) works, so rewrite the scheme.
    """
    if url.startswith("libsql://"):
        return "https://" + url[len("libsql://") :]
    if url.startswith("wss://"):
        return "https://" + url[len("wss://") :]
    if url.startswith("ws://"):
        return "http://" + url[len("ws://") :]
    return url


def get_client():
    """Return a process-wide synchronous libSQL client (lazy singleton)."""
    global _client
    if _client is None:
        from libsql_client import create_client_sync

        _client = create_client_sync(
            _http_url(os.environ["TURSO_DATABASE_URL"]),
            auth_token=os.environ["TURSO_AUTH_TOKEN"],
        )
    return _client
