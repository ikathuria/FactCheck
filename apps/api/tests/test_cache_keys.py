from src.features.cache.keys import cache_key
from src.lib.types import SourceMode


def test_same_claim_different_casing_same_key():
    a = cache_key("The Sky Is Blue", SourceMode.flexible)
    b = cache_key("  the sky is blue  ", SourceMode.flexible)
    assert a == b


def test_different_claim_different_key():
    a = cache_key("the sky is blue", SourceMode.flexible)
    b = cache_key("the sea is blue", SourceMode.flexible)
    assert a != b


def test_source_mode_affects_key():
    a = cache_key("the sky is blue", SourceMode.flexible)
    b = cache_key("the sky is blue", SourceMode.strict)
    assert a != b


def test_key_is_sha256_hex():
    key = cache_key("x", SourceMode.flexible)
    assert len(key) == 64
    assert all(c in "0123456789abcdef" for c in key)


def test_accepts_string_source_mode():
    assert cache_key("x", "flexible") == cache_key("x", SourceMode.flexible)
