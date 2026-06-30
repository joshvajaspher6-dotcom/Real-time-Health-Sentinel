from testsentry.ai_triage import langfuse
import pytest
import uuid
from testsentry.collector import init_db, store_result
from testsentry.ai_triage import triage_failure
from testsentry.health_engine import calculate_health_score
from testsentry.regression_detector import label_test
from testsentry.report_generator import generate_report


RUN_ID = str(uuid.uuid4())[:8]


def pytest_configure(config):
    """Initialize database when pytest starts."""
    init_db()
    print(f"\n[TestSentry] Run ID: {RUN_ID}")




def pytest_sessionfinish(session, exitstatus):
    """
    Fires after ALL tests finish.
    Calculate health score and generate HTML report.
    """
    score = calculate_health_score(RUN_ID)
    print(f"\n{'='*50}")
    print(f"[TestSentry] 🏥 HEALTH SCORE: {score['total_score']}/100 (Grade: {score['grade']})")
    print(f"  Speed:      {score['speed_score']}/20")
    print(f"  Stability:  {score['stability_score']}/20")
    print(f"  Flakiness:  {score['flakiness_score']}/20")
    print(f"  Coverage:   {score['coverage_score']}/20")
    print(f"  Quality:    {score['quality_score']}/20")
    print(f"  Pass rate:  {score['pass_rate']}%")
    print(f"  Flaky tests: {score['flaky_count']}")
    print(f"{'='*50}")

    generate_report(RUN_ID)

    langfuse.flush()
    print(f"[TestSentry] 📡 Langfuse traces sent")



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
 
            