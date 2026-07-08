from testsentry.email_notifier import build_email, build_plain_text


SAMPLE_HEALTH = {
    "total_score": 75,
    "grade": "B",
    "pass_rate": 96.3
}

SAMPLE_FAILING = [{
    "test_name": "tests/test_sample.py::test_checkout",
    "owner": "joshva@test.com",
    "category": "ENV_ISSUE",
    "suggested_fix": "Start the database before tests"
}]


def test_build_email_with_failures():
    """Email should contain failure info."""
    subject, html = build_email(
        run_id="test123",
        newly_failing=SAMPLE_FAILING,
        fixed=[],
        health_score=SAMPLE_HEALTH,
        repo_name="TestSentry"
    )
    assert "TestSentry Alert" in subject
    assert "test_checkout" in html
    assert "ENV_ISSUE" in html


def test_build_email_with_fixed():
    """Email should show fixed tests."""
    subject, html = build_email(
        run_id="test456",
        newly_failing=[],
        fixed=[{"test_name": "tests/test_sample.py::test_login"}],
        health_score=SAMPLE_HEALTH,
        repo_name="TestSentry"
    )
    assert "resolved" in subject
    assert "test_login" in html


def test_plain_text_fallback():
    """Plain text version should contain key info."""
    text = build_plain_text(
        newly_failing=SAMPLE_FAILING,
        fixed=[],
        health_score=SAMPLE_HEALTH,
        run_id="test789"
    )
    assert "NEWLY FAILING" in text
    assert "test_checkout" in text
    assert "ENV_ISSUE" in text


def test_notification_skips_without_credentials():
    """Should skip if no email credentials set."""
    import testsentry.email_notifier as em
    original_from = em.EMAIL_FROM
    original_pass = em.EMAIL_PASSWORD
    em.EMAIL_FROM = None
    em.EMAIL_PASSWORD = None
    result = em.send_email_notification(
        run_id="test",
        newly_failing=[],
        fixed=[],
        health_score={},
        repo_name="test"
    )
    assert result == False
    em.EMAIL_FROM = original_from
    em.EMAIL_PASSWORD = original_pass