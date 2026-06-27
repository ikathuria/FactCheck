from src.lib import tavily
from src.lib.types import SourceMode

from .conftest import requires_tavily


@requires_tavily
def test_flexible_search_returns_results():
    results = tavily.search("US national debt 2024", SourceMode.flexible)
    assert len(results) >= 1
    assert all("url" in r and "snippet" in r for r in results)


@requires_tavily
def test_strict_search_returns_results():
    results = tavily.search("H1B visa cap 2024", SourceMode.strict)
    assert len(results) >= 1
