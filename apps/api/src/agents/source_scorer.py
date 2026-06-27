"""Agent 3: SourceScorer — credibility-score sources by domain, filter < 0.4."""

from urllib.parse import urlparse

from ..lib.types import DomainType

SCORE_THRESHOLD = 0.4

_GOVERNMENT_HOSTS = {
    "who.int", "cdc.gov", "nih.gov", "whitehouse.gov", "usa.gov",
    "congress.gov", "senate.gov", "house.gov", "hhs.gov", "dol.gov", "uscis.gov",
    "gao.gov", "archives.gov", "fec.gov",
}
_NEWS_HOSTS = {
    "apnews.com", "reuters.com", "bbc.com", "bbc.co.uk", "npr.org", "pbs.org",
}
_GOV_PATTERNS = (".gov", ".gc.ca", ".mil")
_EDU_PATTERNS = (".edu", ".ac.uk", ".ac.")


def score_domain(url: str) -> tuple[float, DomainType]:
    """Return (credibility_score, domain_type) for a URL."""
    try:
        host = urlparse(url).netloc.lower()
    except Exception:  # noqa: BLE001
        host = url.lower()

    if host in _GOVERNMENT_HOSTS or any(p in host for p in _GOV_PATTERNS):
        return 1.0, DomainType.government
    if any(p in host for p in _EDU_PATTERNS):
        return 0.85, DomainType.academic
    if host in _NEWS_HOSTS or any(host.endswith("." + h) for h in _NEWS_HOSTS):
        return 0.7, DomainType.established_news
    return 0.4, DomainType.other


def score(evidence: list[dict]) -> list[dict]:
    """Add credibility_score + domain_type to each chunk; drop those below threshold.

    Returns chunks sorted by credibility then Tavily relevance (descending).
    """
    scored: list[dict] = []
    for item in evidence:
        cred, domain_type = score_domain(item.get("url", ""))
        if cred >= SCORE_THRESHOLD:
            scored.append({**item, "credibility_score": cred, "domain_type": domain_type})

    scored.sort(
        key=lambda x: (x["credibility_score"], x.get("tavily_score", 0.0)),
        reverse=True,
    )
    return scored
