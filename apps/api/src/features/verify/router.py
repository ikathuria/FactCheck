"""POST /verify endpoint."""

from fastapi import APIRouter, HTTPException

from ...lib.types import VerifyRequest, VerifyResponse
from . import pipeline

router = APIRouter()


@router.post("/verify", response_model=VerifyResponse)
def verify(request: VerifyRequest) -> VerifyResponse:
    """Run the 5-agent fact-check pipeline on a claim (no caching yet — Milestone 3)."""
    try:
        return pipeline.run(claim=request.claim, source_mode=request.source_mode)
    except Exception as e:  # noqa: BLE001 — surface pipeline failures as 502
        raise HTTPException(status_code=502, detail=f"Verification failed: {e}") from e
