import pytest


def pytest_configure(config):
    """TestSentry plugin loaded successfully."""
    pass


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Fires the moment each test finishes.
    Captures test name, status, duration, and error message.
    """
    outcome = yield  # let pytest run the test first

    report = outcome.get_result()

    # Only capture the actual test call, not setup/teardown
    if report.when == "call":
        result = {
            "test_name": item.nodeid,
            "status": "PASSED" if report.passed else "FAILED",
            "duration": round(report.duration, 4),
            "error_msg": str(report.longrepr) if report.failed else None,
        }

        
        print(f"\n[TestSentry] {result['status']} — {result['test_name']} ({result['duration']}s)")