"""Tests for GET /recent-searches.

The endpoint works without Turso configured (returns an empty feed), so the
shape test always runs. Param validation is also always testable.
"""

from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_recent_searches_shape():
    resp = client.get("/recent-searches")
    assert resp.status_code == 200
    body = resp.json()
    assert "searches" in body and isinstance(body["searches"], list)
    assert "total" in body and isinstance(body["total"], int)


def test_recent_searches_rejects_bad_limit():
    assert client.get("/recent-searches?limit=0").status_code == 422
    assert client.get("/recent-searches?limit=51").status_code == 422


def test_recent_searches_rejects_negative_offset():
    assert client.get("/recent-searches?offset=-1").status_code == 422
