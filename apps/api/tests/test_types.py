import pytest
from pydantic import ValidationError

from src.lib.types import (
    DomainType,
    Source,
    SourceMode,
    VerdictEnum,
    VerifyRequest,
    VerifyResponse,
)


def test_verify_request_defaults_to_flexible():
    req = VerifyRequest(claim="The sky is blue")
    assert req.source_mode == SourceMode.flexible


def test_verify_request_rejects_empty_claim():
    with pytest.raises(ValidationError):
        VerifyRequest(claim="")


def test_verify_request_rejects_overlong_claim():
    with pytest.raises(ValidationError):
        VerifyRequest(claim="x" * 501)


def test_source_confidence_bounds():
    with pytest.raises(ValidationError):
        Source(
            url="https://x.gov",
            title="t",
            snippet="s",
            credibility_score=1.5,
            domain_type=DomainType.government,
        )


def test_verify_response_roundtrip():
    resp = VerifyResponse(
        claim="c",
        verdict=VerdictEnum.supported,
        confidence=0.9,
        reasoning="because",
    )
    assert resp.cached is False
    assert resp.verdict == VerdictEnum.supported
    assert resp.sources == []
