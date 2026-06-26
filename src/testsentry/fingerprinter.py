import re
import hashlib


def normalise_trace(error_msg: str) -> str:
    """
    Strip all run-specific values from a stack trace
    so the same error always produces the same string.

    We remove:
    - Line numbers       (change every refactor)
    - Memory addresses   (change every run)
    - Absolute file paths (change per machine)
    - Timestamps         (change every run)
    - Process/thread IDs (change every run)
    """
    if not error_msg:
        return ""

    trace = error_msg

    # Strip line numbers — "line 47" → "line N"
    trace = re.sub(r'line \d+', 'line N', trace)

    # Strip memory addresses — "0x7f3a2b1c" → "0xADDR"
    trace = re.sub(r'0x[0-9a-fA-F]+', '0xADDR', trace)

    # Strip absolute file paths — "/home/joshva/..." → "/PATH/"
    trace = re.sub(r'/[\w/.-]+/', '/PATH/', trace)

    # Strip timestamps — "2026-06-26" → "DATE"
    trace = re.sub(r'\d{4}-\d{2}-\d{2}', 'DATE', trace)

    # Strip time values — "20:32:30" → "TIME"
    trace = re.sub(r'\d{2}:\d{2}:\d{2}', 'TIME', trace)

    # Strip process IDs — "pid=12345" → "pid=N"
    trace = re.sub(r'pid=\d+', 'pid=N', trace)

    # Collapse multiple spaces into one
    trace = re.sub(r' +', ' ', trace)

    return trace.strip()


def fingerprint(error_msg: str) -> str:
    """
    Generate a short unique hash for a normalised error.
    Same error → same hash every time.
    Different error → different hash.

    Returns first 16 characters of SHA-256 hash.
    """
    normalised = normalise_trace(error_msg)
    full_hash = hashlib.sha256(normalised.encode()).hexdigest()
    return full_hash[:16]