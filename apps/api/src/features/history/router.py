"""GET /recent-searches endpoint."""

from fastapi import APIRouter, Query

from ...lib.types import RecentSearchesResponse
from . import store

router = APIRouter()


@router.get("/recent-searches", response_model=RecentSearchesResponse)
def recent_searches(
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
) -> RecentSearchesResponse:
    """Public feed of recently-checked claims, newest first."""
    rows, total = store.recent_searches(limit=limit, offset=offset)
    return RecentSearchesResponse(searches=rows, total=total)
