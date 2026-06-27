"""Live end-to-end test of POST /verify (skipped without API keys)."""

from fastapi.testclient import TestClient

from src.lib.types import VerdictEnum
from src.main import app

from .conftest import requires_gemini, requires_tavily

client = TestClient(app)

_VALID_VERDICTS = {v.value for v in VerdictEnum}


def test_verify_rejects_empty_claim():
    resp = client.post("/verify", json={"claim": "", "source_mode": "flexible"})
    assert resp.status_code == 422


@requires_gemini
@requires_tavily
def test_verify_returns_valid_response():
    resp = client.post(
        "/verify",
        json={"claim": "The Eiffel Tower is in London", "source_mode": "flexible"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["verdict"] in _VALID_VERDICTS
    assert 0.0 <= body["confidence"] <= 1.0
    assert isinstance(body["sources"], list)
    assert body["cached"] is False
