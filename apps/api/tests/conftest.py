"""Shared pytest fixtures/markers.

Live tests (those that hit Gemini or Tavily) are skipped automatically when the
relevant API keys are absent — so CI without secrets stays green, while a local
run with keys exercises the real pipeline.
"""

import os

import pytest

requires_gemini = pytest.mark.skipif(
    not os.environ.get("GEMINI_API_KEY"),
    reason="GEMINI_API_KEY not set — skipping live LLM test",
)

requires_tavily = pytest.mark.skipif(
    not os.environ.get("TAVILY_API_KEY"),
    reason="TAVILY_API_KEY not set — skipping live search test",
)

requires_redis = pytest.mark.skipif(
    not os.environ.get("UPSTASH_REDIS_REST_URL", "").startswith("http"),
    reason="Upstash Redis not configured — skipping live cache test",
)

requires_supabase = pytest.mark.skipif(
    not os.environ.get("SUPABASE_URL", "").startswith("http"),
    reason="Supabase not configured — skipping live storage test",
)
