from src.agents import source_scorer
from src.lib.types import DomainType


def test_government_domain_scores_high():
    score, domain_type = source_scorer.score_domain("https://www.uscis.gov/newsroom/alert")
    assert score == 1.0
    assert domain_type == DomainType.government


def test_academic_domain():
    score, domain_type = source_scorer.score_domain("https://www.harvard.edu/research")
    assert score == 0.85
    assert domain_type == DomainType.academic


def test_established_news_domain():
    score, domain_type = source_scorer.score_domain("https://www.reuters.com/world")
    assert score == 0.7
    assert domain_type == DomainType.established_news


def test_unknown_blog_scores_floor():
    score, domain_type = source_scorer.score_domain("https://some-random-blog.example/post")
    assert score == 0.4
    assert domain_type == DomainType.other


def test_score_sorts_and_keeps_threshold():
    evidence = [
        {"url": "https://blog.example/x", "title": "b", "snippet": "s", "tavily_score": 0.9},
        {"url": "https://cdc.gov/y", "title": "g", "snippet": "s", "tavily_score": 0.1},
    ]
    scored = source_scorer.score(evidence)
    # gov should sort first despite lower tavily score
    assert scored[0]["domain_type"] == DomainType.government
    assert all(s["credibility_score"] >= source_scorer.SCORE_THRESHOLD for s in scored)
