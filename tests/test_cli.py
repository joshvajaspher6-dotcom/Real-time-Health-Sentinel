from click.testing import CliRunner
from testsentry.cli import cli


def test_version_command():
    """Version command should print version info."""
    runner = CliRunner()
    result = runner.invoke(cli, ['version'])
    assert result.exit_code == 0
    assert 'TestSentry' in result.output


def test_help_command():
    """Help command should list all commands."""
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert 'scan' in result.output
    assert 'status' in result.output
    assert 'flaky' in result.output
    assert 'history' in result.output
    assert 'risk' in result.output


def test_status_no_runs():
    """Status with empty database should handle gracefully."""
    runner = CliRunner()
    result = runner.invoke(cli, ['status'])
    assert result.exit_code == 0


def test_flaky_no_data():
    """Flaky command with no data should handle gracefully."""
    runner = CliRunner()
    result = runner.invoke(cli, ['flaky'])
    assert result.exit_code == 0


def test_history_no_runs():
    """History with no runs should handle gracefully."""
    runner = CliRunner()
    result = runner.invoke(cli, ['history'])
    assert result.exit_code == 0


def test_risk_no_data():
    """Risk command should handle gracefully."""
    runner = CliRunner()
    result = runner.invoke(cli, ['risk'])
    assert result.exit_code == 0