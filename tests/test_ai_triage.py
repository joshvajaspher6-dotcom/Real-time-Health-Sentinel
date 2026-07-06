from testsentry.ai_triage import triage_failure


def test_triage_skips_empty_error():
    """Should return None for empty error message."""
    result = triage_failure({
        "error_msg": "",
        "test_name": "tests/test_sample.py::test_something"
    })
    assert result is None


def test_triage_returns_none_without_key(monkeypatch):
    """Should return None when API key is not set."""
    monkeypatch.setenv("GROQ_API_KEY", "")
    import importlib
    import testsentry.ai_triage as ai
    ai.GROQ_API_KEY = ""
    result = triage_failure({
        "error_msg": "AssertionError: assert 1 == 2",
        "test_name": "tests/test_sample.py::test_something"
    })
    assert result is None