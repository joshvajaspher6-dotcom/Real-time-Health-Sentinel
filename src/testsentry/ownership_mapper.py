import git
import os
from testsentry.collector import get_connection


def get_file_owners(repo_path: str = ".", max_commits: int = 50) -> dict:
    """
    Return {filename: last_author_email} from git log.
    Walks through recent commits and records the FIRST (most recent)
    author who touched each file.
    """
    try:
        repo = git.Repo(repo_path)
    except git.InvalidGitRepositoryError:
        print("[TestSentry] ⚠️ Not a git repository — skipping ownership mapping")
        return {}

    owners = {}

    try:
        for commit in repo.iter_commits(max_count=max_commits):
            for filepath in commit.stats.files:
                if filepath not in owners:
                    owners[filepath] = commit.author.email
    except Exception as e:
        print(f"[TestSentry] ⚠️ Error reading git history: {e}")

    return owners


def get_file_change_frequency(repo_path: str = ".", max_commits: int = 50) -> dict:
    """
    Return {filename: change_count} — how many times
    each file was changed in recent commits.
    """
    try:
        repo = git.Repo(repo_path)
    except git.InvalidGitRepositoryError:
        return {}

    change_counts = {}

    try:
        for commit in repo.iter_commits(max_count=max_commits):
            for filepath in commit.stats.files:
                change_counts[filepath] = change_counts.get(filepath, 0) + 1
    except Exception as e:
        print(f"[TestSentry] ⚠️ Error reading git history: {e}")

    return change_counts


def get_at_risk_modules(repo_path: str = ".") -> list:
    """
    Join ownership + change frequency + test failure data
    to build the 'Who Needs to Act' risk table.

    Risk score = change_count × (number of failures in that file's tests)
    """
    owners = get_file_owners(repo_path)
    changes = get_file_change_frequency(repo_path)

    
    conn = get_connection()
    failure_rows = conn.execute("""
        SELECT test_name, COUNT(*) as failure_count
        FROM test_runs
        WHERE status = 'FAILED'
        GROUP BY test_name
    """).fetchall()
    conn.close()

    
    file_failures = {}
    for test_name, count in failure_rows:
        
        file_path = test_name.split("::")[0]
        file_failures[file_path] = file_failures.get(file_path, 0) + count

  
    at_risk = []
    all_files = set(list(changes.keys()) + list(file_failures.keys()))

    for filepath in all_files:
        change_count = changes.get(filepath, 0)
        failure_count = file_failures.get(filepath, 0)
        owner = owners.get(filepath, "unowned")

        risk_score = change_count * (failure_count + 1)

        if change_count > 0 or failure_count > 0:
            at_risk.append({
                "filepath":      filepath,
                "owner":         owner,
                "change_count":  change_count,
                "failure_count": failure_count,
                "risk_score":    risk_score
            })

   
    at_risk.sort(key=lambda x: x["risk_score"], reverse=True)

    return at_risk[:10] 