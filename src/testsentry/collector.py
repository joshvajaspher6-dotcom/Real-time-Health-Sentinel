import duckdb
import os
from datetime import datetime


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
    conn.execute("""
        CREATE TABLE IF NOT EXISTS triage_cache (
            fingerprint     VARCHAR PRIMARY KEY,
            category        VARCHAR,
            confidence_pct  INTEGER,
            why_it_failed   VARCHAR,
            suggested_fix   VARCHAR,
            affected_module VARCHAR,
            hit_count       INTEGER DEFAULT 0,
            created_at      TIMESTAMP
        )
    """)
    conn.close()
    print("[TestSentry] Database initialized at testsentry.db")


def store_result(result: dict, run_id: str, label: str = "NEW_TEST"):
    """
    Save a single test result to DuckDB.
    Called after every test finishes.
    """
    conn = get_connection()
    conn.execute("""
        INSERT INTO test_runs
            (run_id, test_name, status, duration, error_msg, label, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, [
        run_id,
        result["test_name"],
        result["status"],
        result["duration"],
        result["error_msg"],
        label,
        datetime.now()
    ])
    conn.close()


def get_recent_runs(limit: int = 10):
    """
    Fetch the most recent test results.
    """
    conn = get_connection()
    rows = conn.execute("""
        SELECT test_name, status, duration, timestamp
        FROM test_runs
        ORDER BY timestamp DESC
        LIMIT ?
    """, [limit]).fetchall()
    conn.close()
    return rows

def cache_lookup(fp: str):
    """
    Check if a fingerprint exists in the triage cache.
    Returns cached result dict or None if not found.
    """
    conn = get_connection()
    row = conn.execute("""
        SELECT category, confidence_pct, why_it_failed,
               suggested_fix, affected_module
        FROM triage_cache
        WHERE fingerprint = ?
    """, [fp]).fetchone()

    if row:
        # Increment hit counter
        conn.execute("""
            UPDATE triage_cache
            SET hit_count = hit_count + 1
            WHERE fingerprint = ?
        """, [fp])
        conn.close()
        return {
            "category":        row[0],
            "confidence_pct":  row[1],
            "why_it_failed":   row[2],
            "suggested_fix":   row[3],
            "affected_module": row[4],
            "cache_hit":       True
        }

    conn.close()
    return None


def cache_store(fp: str, triage_result: dict):
    """
    Store a new triage result in the cache.
    Called after every fresh AI API call.
    """
    conn = get_connection()
    conn.execute("""
        INSERT OR REPLACE INTO triage_cache
            (fingerprint, category, confidence_pct,
             why_it_failed, suggested_fix, affected_module,
             hit_count, created_at)
        VALUES (?, ?, ?, ?, ?, ?, 0, ?)
    """, [
        fp,
        triage_result["category"],
        triage_result["confidence_pct"],
        triage_result["why_it_failed"],
        triage_result["suggested_fix"],
        triage_result.get("affected_module", "unknown"),
        datetime.now()
    ])
    conn.close()