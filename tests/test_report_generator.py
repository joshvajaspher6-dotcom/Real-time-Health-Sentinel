from testsentry.report_generator import get_ai_stats
from testsentry.collector import store_result


def test_get_ai_stats_returns_dict():
    """AI stats should return dict with required keys."""
    stats = get_ai_stats("nonexistent_run_xyz")
    assert isinstance(stats, dict)
    assert "total_failures" in stats
    assert "api_calls" in stats
    assert "cache_hits" in stats


def test_get_ai_stats_zero_for_unknown_run():
    """Unknown run should return zero failures."""
    stats = get_ai_stats("totally_unknown_run_abc123")
    assert stats["total_failures"] == 0