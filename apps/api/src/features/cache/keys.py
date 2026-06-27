"""Cache key generation."""

import hashlib

from ...lib.types import SourceMode


def cache_key(claim: str, source_mode: SourceMode | str) -> str:
    """SHA-256 of the normalized "{claim}:{source_mode}".

    Normalization (lowercase + strip) means the same claim with different casing
    or surrounding whitespace maps to the same key.
    """
    mode = source_mode.value if isinstance(source_mode, SourceMode) else str(source_mode)
    raw = f"{claim.strip().lower()}:{mode}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
