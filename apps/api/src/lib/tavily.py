"""Tavily web-search client + source-mode filtering.

Env:
    TAVILY_API_KEY   required
"""

import os

from tavily import TavilyClient

from .types import SourceMode

# Strict-mode allowlist: government, academic, and established-news domains.
# Used as Tavily `include_domains`. Academic TLD patterns (.edu/.ac.uk) can't be
# expressed as exact domains here, so strict mode relies on these explicit hosts
# plus the SourceScorer's domain tiering for the rest.
GOVERNMENT_DOMAINS = [
    "who.int", "cdc.gov", "nih.gov", "whitehouse.gov", "usa.gov",
    "congress.gov", "senate.gov", "house.gov", "hhs.gov", "dol.gov", "uscis.gov",
    "gao.gov", "archives.gov", "fec.gov",
]
NEWS_DOMAINS = [
    "apnews.com", "reuters.com", "bbc.com", "bbc.co.uk",
    "npr.org", "pbs.org",
]
STRICT_INCLUDE_DOMAINS = GOVERNMENT_DOMAINS + NEWS_DOMAINS

_client: TavilyClient | None = None


def get_client() -> TavilyClient:
    """Return a lazily-initialized singleton Tavily client."""
    global _client
    if _client is None:
        api_key = os.environ.get("TAVILY_API_KEY", "")
        if not api_key:
            raise RuntimeError("TAVILY_API_KEY is not set")
        _client = TavilyClient(api_key=api_key)
    return _client


def search(query: str, source_mode: SourceMode, max_results: int = 5) -> list[dict]:
    """Run a Tavily search and return normalized result dicts.

    strict mode applies the domain allowlist; flexible returns all results.
    Each returned dict: url, title, snippet, tavily_score, published_date.
    """
    kwargs: dict = {
        "query": query,
        "search_depth": "advanced",
        "max_results": max_results,
    }
    if source_mode == SourceMode.strict:
        kwargs["include_domains"] = STRICT_INCLUDE_DOMAINS

    response = get_client().search(**kwargs)
    return [
        {
            "url": r.get("url", ""),
            "title": r.get("title", ""),
            "snippet": r.get("content", ""),
            "tavily_score": r.get("score", 0.0),
            "published_date": r.get("published_date"),
        }
        for r in response.get("results", [])
        if r.get("url")
    ]
