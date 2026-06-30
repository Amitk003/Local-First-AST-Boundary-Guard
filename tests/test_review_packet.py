"""Tests for the review packet module."""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from code_guardian.review_packet import build_packet, format_packet, save_packet


def test_build_packet_approved():
    """Test building a packet when all checks pass."""
    intent = {"issue_id": "AUTH-101", "allowed_files": ["src/auth/*"]}
    staged = ["src/auth/login.py"]
    checks = {
        "scope": {"passed": True, "unauthorized": [], "allowed_files": ["src/auth/*"]},
        "tests": {"passed": True, "missing": []},
        "docs": {"passed": True, "missing": []},
        "risk": {"passed": True, "risks": [], "has_high": False, "has_medium": False},
    }

    packet = build_packet(intent, staged, checks, passed=True)
    assert packet["status"] == "approved"
    assert packet["summary"]["passed"] == 4
    assert packet["summary"]["failed"] == 0
    assert packet["intent"]["issue_id"] == "AUTH-101"


def test_build_packet_blocked():
    """Test building a packet when checks fail."""
    intent = {"issue_id": "AUTH-101", "allowed_files": ["src/auth/*"]}
    staged = ["src/auth/login.py", "src/payment/pay.py"]
    checks = {
        "scope": {"passed": False, "unauthorized": ["src/payment/pay.py"],
                   "allowed_files": ["src/auth/*"]},
        "tests": {"passed": True, "missing": []},
        "docs": {"passed": True, "missing": []},
        "risk": {"passed": True, "risks": [], "has_high": False, "has_medium": False},
    }

    packet = build_packet(intent, staged, checks, passed=False)
    assert packet["status"] == "blocked"
    assert packet["summary"]["failed"] == 1


def test_build_packet_no_intent():
    """Test building a packet with no active intent."""
    staged = ["src/utils/helper.py"]
    checks = {
        "scope": {"passed": True, "message": "no active intent - scope check skipped"},
        "tests": {"passed": True, "missing": []},
        "docs": {"passed": True, "missing": []},
        "risk": {"passed": True, "risks": [], "has_high": False, "has_medium": False},
    }

    packet = build_packet(None, staged, checks, passed=True)
    assert packet["status"] == "approved"
    assert packet["intent"] is None


def test_build_packet_all_failed():
    """Test building a packet when all checks fail."""
    staged = ["src/auth/login.py"]
    checks = {
        "scope": {"passed": False, "unauthorized": ["src/auth/login.py"],
                   "allowed_files": ["src/utils/*"]},
        "tests": {"passed": False, "missing": [
            {"source": "src/auth/login.py", "expected_test": "tests/test_auth_login.py"},
        ]},
        "docs": {"passed": False, "missing": [
            {"source": "src/auth/login.py", "expected_doc": "docs/auth/login.md"},
        ]},
        "risk": {"passed": False, "risks": [
            {"file": "src/auth/login.py", "level": "high", "reason": "auth code"},
        ], "has_high": True, "has_medium": False},
    }

    packet = build_packet(None, staged, checks, passed=False)
    assert packet["status"] == "blocked"
    assert packet["summary"]["failed"] == 4


def test_format_packet_approved():
    """Test formatting an approved packet."""
    intent = {"issue_id": "AUTH-101", "allowed_files": ["src/auth/*"]}
    staged = ["src/auth/login.py"]
    checks = {
        "scope": {"passed": True, "unauthorized": [], "allowed_files": ["src/auth/*"]},
        "tests": {"passed": True, "missing": []},
        "docs": {"passed": True, "missing": []},
        "risk": {"passed": True, "risks": [], "has_high": False, "has_medium": False},
    }

    packet = build_packet(intent, staged, checks, passed=True)
    text = format_packet(packet)
    assert "approved" in text.lower()
    assert "pass" in text.lower()


def test_save_packet():
    """Test saving a packet to a file."""
    packet = build_packet(None, [], {}, passed=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = save_packet(packet, tmpdir)
        assert os.path.exists(filepath)
        assert filepath.endswith(".json")

        with open(filepath) as f:
            content = f.read()
        assert '"status": "approved"' in content


def run():
    """Run all tests in this module."""
    tests = [
        test_build_packet_approved,
        test_build_packet_blocked,
        test_build_packet_no_intent,
        test_build_packet_all_failed,
        test_format_packet_approved,
        test_save_packet,
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
    print(f"review packet tests: {p} passed, {f} failed")
