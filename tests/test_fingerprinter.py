from testsentry.fingerprinter import normalise_trace, fingerprint


def test_same_error_same_hash():
    """Same error with different line numbers must produce same hash."""
    error1 = "AssertionError at line 47, memory 0x7f3a2b"
    error2 = "AssertionError at line 89, memory 0x9c1d4e"

    assert fingerprint(error1) == fingerprint(error2)


def test_different_errors_different_hash():
    """Different errors must produce different hashes."""
    error1 = "AssertionError: expected 4 got 5"
    error2 = "ConnectionRefusedError: localhost:5432"

    assert fingerprint(error1) != fingerprint(error2)


def test_normalise_removes_line_numbers():
    """Line numbers must be stripped."""
    trace = "Error at line 47 and line 89"
    normalised = normalise_trace(trace)

    assert "47" not in normalised
    assert "89" not in normalised
    assert "line N" in normalised


def test_normalise_removes_memory_addresses():
    """Memory addresses must be stripped."""
    trace = "object at 0x7f3a2b1c and 0x9c1d4e"
    normalised = normalise_trace(trace)

    assert "0x7f3a2b1c" not in normalised
    assert "0xADDR" in normalised


def test_empty_error_returns_empty():
    """Empty error must return empty string."""
    assert fingerprint("") == fingerprint("")
    assert normalise_trace("") == ""