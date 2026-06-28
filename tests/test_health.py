from testsentry.health_engine import calculate_health_score, get_grade
from testsentry.collector import store_result


def test_grade_a():
    assert get_grade(95) == "A"
    assert get_grade(90) == "A"


def test_grade_b():
    assert get_grade(89) == "B"
    assert get_grade(75) == "B"


def test_grade_f():
    assert get_grade(30) == "F"
    assert get_grade(0) == "F"


def test_health_score_returns_dict():
    """Health score should return a dict with all keys."""

    
    for i in range(5):
        store_result({
            "test_name": f"tests/test_health_fake.py::test_{i}",
            "status": "PASSED",
            "duration": 0.05,
            "error_msg": None
        }, "run_health_test", "STABLE")

    score = calculate_health_score("run_health_test")

    assert "total_score" in score
    assert "speed_score" in score
    assert "stability_score" in score
    assert "flakiness_score" in score
    assert "coverage_score" in score
    assert "quality_score" in score
    assert "grade" in score
    assert 0 <= score["total_score"] <= 100


def test_perfect_score():
    """All passing, fast tests should score high."""
    for i in range(10):
        store_result({
            "test_name": f"tests/test_perfect.py::test_{i}",
            "status": "PASSED",
            "duration": 0.01,
            "error_msg": None
        }, "run_perfect", "STABLE")

    score = calculate_health_score("run_perfect")
    assert score["total_score"] >= 60