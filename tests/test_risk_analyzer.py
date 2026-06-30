"""Tests for the risk analyzer module."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from code_guardian.risk_analyzer import (
    _match_glob,
    _check_file_risks,
    format_risks,
)


def test_match_glob_exact():
    """Test exact file path matching."""
    assert _match_glob("src/auth/login.py", "src/auth/login.py")
    assert not _match_glob("src/auth/other.py", "src/auth/login.py")


def test_match_glob_wildcard():
    """Test wildcard glob matching."""
    assert _match_glob("src/auth/login.py", "src/auth/*")
    assert _match_glob("src/auth/login.py", "**/login.py")
    assert not _match_glob("src/payment/pay.py", "src/auth/*")


def test_match_glob_double_star():
    """Test double-star (**) glob matching."""
    assert _match_glob("src/auth/login.py", "**/auth/*")
    assert _match_glob("src/payment/auth/login.py", "**/auth/*")
    assert not _match_glob("src/payment/pay.py", "**/auth/*")


def test_check_file_risks_auth_file():
    """Test detection of auth file changes."""
    risks = _check_file_risks([("M", "src/auth/login.py")])
    auth_risks = [r for r in risks if "authentication" in r["reason"]]
    assert len(auth_risks) > 0


def test_check_file_risks_deleted_file():
    """Test detection of deleted files."""
    risks = _check_file_risks([("D", "src/config.py")])
    deleted = [r for r in risks if r.get("status") == "deleted"]
    assert len(deleted) > 0


def test_check_file_risks_migration():
    """Test detection of migration file changes."""
    risks = _check_file_risks([("M", "db/migrations/001_init.py")])
    migration_risks = [r for r in risks if "migration" in r["reason"]]
    assert len(migration_risks) > 0


def test_check_file_risks_docker():
    """Test detection of Docker file changes."""
    risks = _check_file_risks([("M", "Dockerfile")])
    docker_risks = [r for r in risks if "docker" in r["reason"].lower()]
    assert len(docker_risks) > 0


def test_check_file_risks_dependencies():
    """Test detection of dependency file changes."""
    risks = _check_file_risks([("M", "requirements.txt")])
    dep_risks = [r for r in risks if "dependencies" in r["reason"]]
    assert len(dep_risks) > 0


def test_check_file_risks_ci():
    """Test detection of CI/CD file changes."""
    risks = _check_file_risks([("M", ".github/workflows/ci.yml")])
    ci_risks = [r for r in risks if "CI/CD" in r["reason"]]
    assert len(ci_risks) > 0


def test_check_file_risks_no_risk():
    """Test that normal source files don't trigger risks."""
    risks = _check_file_risks([("M", "src/app/utils/helper.py")])
    assert len(risks) == 0


def test_format_risks_no_risks():
    """Test formatting when no risks found."""
    result = {
        "risks": [],
        "has_high_risk": False,
        "has_medium_risk": False,
        "risk_count": 0,
    }
    formatted = format_risks(result)
    assert formatted is None


def test_format_risks_with_risks():
    """Test formatting when risks are found."""
    result = {
        "risks": [
            {"file": "src/auth/login.py", "level": "high",
             "reason": "auth code modified", "status": "M"},
        ],
        "has_high_risk": True,
        "has_medium_risk": False,
        "risk_count": 1,
    }
    formatted = format_risks(result)
    assert formatted is not None
    assert "high risk" in formatted.lower()


def run():
    """Run all tests in this module."""
    tests = [
        test_match_glob_exact,
        test_match_glob_wildcard,
        test_match_glob_double_star,
        test_check_file_risks_auth_file,
        test_check_file_risks_deleted_file,
        test_check_file_risks_migration,
        test_check_file_risks_docker,
        test_check_file_risks_dependencies,
        test_check_file_risks_ci,
        test_check_file_risks_no_risk,
        test_format_risks_no_risks,
        test_format_risks_with_risks,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            failed += 1
            print(f"  FAIL: {test.__name__} - {e}")

    return passed, failed


if __name__ == "__main__":
    p, f = run()
    print(f"risk analyzer tests: {p} passed, {f} failed")
