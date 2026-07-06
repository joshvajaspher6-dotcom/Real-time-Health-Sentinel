from testsentry.coverage_analyzer import (
    get_coverage_summary,
    get_coverage_score
)


def test_coverage_summary_returns_dict():
    """Should always return a dict even without coverage.json."""
    summary = get_coverage_summary()
    assert isinstance(summary, dict)
    assert "total_pct" in summary
    assert "files" in summary


def test_coverage_score_returns_int():
    """Coverage score should always return an integer 0-20."""
    score = get_coverage_score()
    assert isinstance(score, int)
    assert 0 <= score <= 20


def test_coverage_score_zero_without_data(tmp_path, monkeypatch):
    """Without coverage.json, score should be 0."""
    monkeypatch.chdir(tmp_path)
    score = get_coverage_score()
    assert score == 0