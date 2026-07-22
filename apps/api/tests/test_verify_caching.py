"""Deterministic test of the /verify cache hit/miss flow.

Stubs the pipeline and an in-memory cache so the caching contract is verified
without live Turso or LLM quota: two identical requests run the pipeline once,
and the second response is served from cache with cached=true.
"""

from fastapi.testclient import TestClient

from src.features.cache import turso_cache
from src.features.history import store
from src.features.verify import pipeline, router
from src.lib.types import SourceMode, VerdictEnum, VerifyResponse
from src.main import app

client = TestClient(app)


def test_second_identical_request_is_cached(monkeypatch):
    calls = {"n": 0}

    def fake_run(claim: str, source_mode: SourceMode) -> VerifyResponse:
        calls["n"] += 1
        return VerifyResponse(
            claim=claim,
            verdict=VerdictEnum.refuted,
            confidence=0.9,
            reasoning="stub",
            source_mode=source_mode,
        )

    fake_store: dict[str, dict] = {}

    monkeypatch.setattr(pipeline, "run", fake_run)
    monkeypatch.setattr(router.pipeline, "run", fake_run)
    monkeypatch.setattr(router.turso_cache, "get", lambda k: fake_store.get(k))
    monkeypatch.setattr(
        router.turso_cache, "set", lambda k, v, ttl_seconds=0: fake_store.__setitem__(k, v)
    )
    monkeypatch.setattr(router.store, "insert_search", lambda **kwargs: None)

    payload = {"claim": "The Eiffel Tower is in London", "source_mode": "flexible"}

    first = client.post("/verify", json=payload)
    assert first.status_code == 200
    assert first.json()["cached"] is False
    assert calls["n"] == 1

    second = client.post("/verify", json=payload)
    assert second.status_code == 200
    assert second.json()["cached"] is True
    assert calls["n"] == 1  # pipeline NOT re-run on cache hit


def test_modules_importable():
    # Sanity: the no-op layers report unconfigured cleanly in a bare env.
    assert isinstance(turso_cache.is_configured(), bool)
    assert isinstance(store.is_configured(), bool)
