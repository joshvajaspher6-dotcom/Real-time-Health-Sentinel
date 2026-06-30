from testsentry.ownership_mapper import get_file_owners, get_file_change_frequency, get_at_risk_modules


def test_get_file_owners_returns_dict():
    """Should return a dictionary of filename -> email."""
    owners = get_file_owners(".")
    assert isinstance(owners, dict)


def test_get_file_owners_has_entries():
    """Our repo has commits, so owners should not be empty."""
    owners = get_file_owners(".")
    assert len(owners) > 0


def test_change_frequency_returns_dict():
    """Should return a dictionary of filename -> count."""
    changes = get_file_change_frequency(".")
    assert isinstance(changes, dict)


def test_change_frequency_has_positive_counts():
    """All change counts should be positive integers."""
    changes = get_file_change_frequency(".")
    for filepath, count in changes.items():
        assert count > 0


def test_at_risk_modules_returns_list():
    """Should return a list of risk dictionaries."""
    at_risk = get_at_risk_modules(".")
    assert isinstance(at_risk, list)


def test_at_risk_modules_have_required_keys():
    """Each entry should have filepath, owner, change_count, etc."""
    at_risk = get_at_risk_modules(".")
    if len(at_risk) > 0:
        first = at_risk[0]
        assert "filepath" in first
        assert "owner" in first
        assert "change_count" in first
        assert "risk_score" in first