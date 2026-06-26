import duckdb
import os
from datetime import datetime

# Database file lives in project root
DB_PATH = os.path.join(os.getcwd(), "testsentry.db")


def get_connection():
    """Get a connection to the TestSentry database."""
    return duckdb.connect(DB_PATH)


def init_db():
    """
    Create all tables if they don't exist.
    Called once when TestSentry starts.
    """
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS test_runs (
            run_id      VARCHAR,
            test_name   VARCHAR,
            status      VARCHAR,
            duration    FLOAT,
            error_msg   VARCHAR,
            label       VARCHAR DEFAULT 'STABLE',
            timestamp   TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS run_metadata (
            run_id      VARCHAR,
            started_at  TIMESTAMP,
            finished_at TIMESTAMP,
            total_tests INTEGER DEFAULT 0,
            passed      INTEGER DEFAULT 0,
            failed      INTEGER DEFAULT 0
        )
    """)
    conn.close()
    print("[TestSentry] Database initialized at testsentry.db")


def store_result(result: dict, run_id: str):
    """
    Save a single test result to DuckDB.
    Called after every test finishes.
    """
    conn = get_connection()
    conn.execute("""
        INSERT INTO test_runs
            (run_id, test_name, status, duration, error_msg, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, [
        run_id,
        result["test_name"],
        result["status"],
        result["duration"],
        result["error_msg"],
        datetime.now()
    ])
    conn.close()


def get_recent_runs(limit: int = 10):
    """
    Fetch the most recent test results.
    """
    conn = get_connection()
    df = conn.execute("""
        SELECT test_name, status, duration, timestamp
        FROM test_runs
        ORDER BY timestamp DESC
        LIMIT ?
    """, [limit]).fetchdf()
    conn.close()
    return df