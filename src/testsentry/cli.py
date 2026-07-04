import click
from testsentry.report_generator import generate_report
from testsentry.collector import get_recent_runs


@click.group()
def cli():
    """TestSentry — Intelligent Test Suite Health Monitor"""
    pass


@cli.command()
@click.option('--output', default='report.html', help='Output file path')
@click.option('--runs', default=30, help='Number of recent runs to analyze')
def scan(output, runs):
    """Generate a TestSentry health report."""
    click.echo("[TestSentry] 🔍 Scanning test history...")

    # Get most recent run ID
    df = get_recent_runs(1)
    if df.empty:
        click.echo("[TestSentry] ⚠️ No test runs found. Run pytest first.")
        return

    # Get run_id from most recent run
    from testsentry.collector import get_connection
    conn = get_connection()
    row = conn.execute("""
        SELECT run_id FROM test_runs
        ORDER BY timestamp DESC
        LIMIT 1
    """).fetchone()
    conn.close()

    if not row:
        click.echo("[TestSentry] ⚠️ No runs found in database.")
        return

    run_id = row[0]
    click.echo(f"[TestSentry] 📊 Analyzing run: {run_id}")

    generate_report(run_id, output)
    click.echo(f"[TestSentry] ✅ Report saved to {output}")


@cli.command()
def status():
    """Show current test suite status."""
    df = get_recent_runs(5)
    if df.empty:
        click.echo("No test runs found.")
        return
    click.echo(df.to_string())


def main():
    cli()