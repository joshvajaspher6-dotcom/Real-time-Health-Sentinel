import pytest
import uuid
from testsentry.collector import init_db, store_result
from testsentry.ai_triage import triage_failure
from testsentry.regression_detector import label_test


RUN_ID = str(uuid.uuid4())[:8]


def pytest_configure(config):
    """Initialize database when pytest starts."""
    init_db()
    print(f"\n[TestSentry] Run ID: {RUN_ID}")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Fires the moment each test finishes.
    Captures and stores result in DuckDB.
    """
    outcome = yield

    report = outcome.get_result()

    if report.when == "call":
        result = {
            "test_name": item.nodeid,
            "status": "PASSED" if report.passed else "FAILED",
            "duration": round(report.duration, 4),
            "error_msg": str(report.longrepr) if report.failed else None,
        }
        
        label = label_test(result, RUN_ID)
        
        store_result(result, RUN_ID, label)

        label_icon = {
            "NEWLY_FAILING": "🔴",
            "FIXED":         "✅",
            "STILL_FAILING": "⚠️",
            "STABLE":        "✓",
            "NEW_TEST":      "🆕",
            "REOPENED":      "🔁",
        }.get(label, "")

        print(f"\n[TestSentry] {result['status']} {label_icon} {label} — {result['test_name']} ({result['duration']}s)")

        if result["status"] == "FAILED":
            try:
                triage_failure(result)
            except Exception as e:
                print(f"\n[TestSentry] ⚠️ Triage error (skipping): {type(e).__name__}")
            