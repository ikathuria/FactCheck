"""Shared Pydantic models and enums for the FactCheck API.

These mirror the API contract in PLAN.md and are the single source of truth for
request/response shapes used by the pipeline, router, and (mirrored) frontend.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class VerdictEnum(str, Enum):
    """Possible fact-check verdicts. Never binary TRUE/FALSE by design."""

    supported = "supported"
    refuted = "refuted"
    contested = "contested"
    insufficient_evidence = "insufficient_evidence"


class SourceMode(str, Enum):
    """Source filtering mode for evidence retrieval."""

    strict = "strict"
    flexible = "flexible"


class DomainType(str, Enum):
    """Credibility tier of a source's domain."""

    government = "government"
    academic = "academic"
    established_news = "established_news"
    other = "other"


class Source(BaseModel):
    """A single cited evidence source."""

    url: str
    title: str
    snippet: str
    credibility_score: float = Field(ge=0.0, le=1.0)
    domain_type: DomainType


class VerifyRequest(BaseModel):
    """POST /verify request body."""

    claim: str = Field(min_length=1, max_length=500)
    source_mode: SourceMode = SourceMode.flexible


class VerifyResponse(BaseModel):
    """POST /verify response body."""

    claim: str
    verdict: VerdictEnum
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    sources: list[Source] = Field(default_factory=list)
    cached: bool = False
    cached_at: datetime | None = None
    ttl_expires_at: datetime | None = None
    # Extras beyond the minimal contract — useful for the frontend.
    sub_claims: list[str] = Field(default_factory=list)
    source_mode: SourceMode = SourceMode.flexible
    source_mode_fallback: bool = False


class RecentSearch(BaseModel):
    """A single row in the recent-searches feed."""

    id: str
    claim: str
    verdict: VerdictEnum
    confidence: float = Field(ge=0.0, le=1.0)
    source_mode: SourceMode
    searched_at: datetime


class RecentSearchesResponse(BaseModel):
    """GET /recent-searches response body."""

    searches: list[RecentSearch] = Field(default_factory=list)
    total: int = 0
