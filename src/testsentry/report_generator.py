import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

from testsentry.health_engine import calculate_health_score
from testsentry.regression_detector import get_regression_summary
from testsentry.ownership_mapper import get_at_risk_modules
from testsentry.collector import get_connection


def get_ai_stats(run_id: str) -> dict:
    """Get AI triage statistics for this run."""
    conn = get_connection()

    total_failures = conn.execute("""
        SELECT COUNT(*) FROM test_runs
        WHERE run_id = ? AND status = 'FAILED'
    """, [run_id]).fetchone()[0]

    cache_hits = conn.execute("""
        SELECT SUM(hit_count) FROM triage_cache
    """).fetchone()[0] or 0

    api_calls = conn.execute("""
        SELECT COUNT(*) FROM triage_cache
    """).fetchone()[0]

    conn.close()

    return {
        "total_failures": total_failures,
        "api_calls":      api_calls,
        "cache_hits":      cache_hits,
    }


def generate_report(run_id: str, output_path: str = "report.html"):
    """
    Generate the complete HTML health report.
    Combines health score, regression summary,
    ownership mapping, and AI stats.
    """
    health = calculate_health_score(run_id)
    regression = get_regression_summary(run_id)
    
    try:
        at_risk = get_at_risk_modules(".") or []
    except Exception as e:
        print(f"[TestSentry] ⚠️  Could not fetch at-risk modules: {e}")
        at_risk = []

    ai_stats = get_ai_stats(run_id)

    
    template_dir = os.path.join(os.path.dirname(__file__), "..", "..", "templates")
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("report.html")

    html = template.render(
        run_id=run_id,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        health=health,
        regression=regression,
        at_risk=at_risk,
        ai_stats=ai_stats
    )

    with open(output_path, "w") as f:
        f.write(html)

    print(f"\n[TestSentry] 📄 Report generated: {output_path}")
    return output_path