"""Tests for the test checker and docs checker modules."""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from code_guardian.test_checker import (
    _get_test_candidates,
    check_tests_exist,
    _is_test_file,
    _is_source_file,
)
from code_guardian.docs_checker import (
    check_docs_updated,
    _is_doc_file,
)


def test_is_test_file():
    """Test test file detection."""
    assert _is_test_file("tests/test_login.py")
    assert _is_test_file("tests/test_auth_login.py")
    assert not _is_test_file("src/auth/login.py")
    assert not _is_test_file("README.md")


def test_is_source_file():
    """Test source file detection."""
    assert _is_source_file("src/auth/login.py")
    assert _is_source_file("src/app.js")
    assert not _is_source_file("tests/test_login.py")
    assert not _is_source_file("docs/api.md")
    assert not _is_source_file("config.json")


def test_get_test_candidates():
    """Test test file candidate generation."""
    candidates = _get_test_candidates("src/auth/login.py")
    assert "tests/test_auth_login.py" in candidates
    assert "tests/test_login.py" in candidates
    assert "tests/auth/test_login.py" in candidates
    assert "src/auth/test_login.py" in candidates
    assert len(candidates) >= 4


def test_get_test_candidates_no_src_dir():
    """Test candidate generation for files without src/ prefix."""
    candidates = _get_test_candidates("utils/helper.py")
    assert len(candidates) >= 2


def test_get_test_candidates_root_level():
    """Test candidate generation for root level files."""
    candidates = _get_test_candidates("main.py")
    assert len(candidates) >= 1


def test_check_tests_exist_no_source():
    """Test when no source files changed (only test files)."""
    result = check_tests_exist(["tests/test_login.py"])
    assert len(result["missing_tests"]) == 0
    assert len(result["test_files_changed"]) == 1


def test_check_tests_exist_empty():
    """Test with empty staged files list."""
    result = check_tests_exist([])
    assert len(result["missing_tests"]) == 0
    assert len(result["test_files_changed"]) == 0


def test_check_tests_exist_missing():
    """Test when test file does not exist for a source change."""
    result = check_tests_exist(["src/auth/login.py"])
    assert len(result["missing_tests"]) > 0


def test_check_tests_exist_with_test_in_staged():
    """Test when test file is in staged changes."""
    result = check_tests_exist(
        ["src/auth/login.py", "tests/test_auth_login.py"]
    )
    assert len(result["missing_tests"]) == 0


def test_is_doc_file():
    """Test documentation file detection."""
    assert _is_doc_file("docs/api.md")
    assert _is_doc_file("README.md")
    assert not _is_doc_file("src/auth/login.py")
    assert not _is_doc_file("tests/test_login.py")


def test_check_docs_updated_no_source():
    """Test when no source files changed (only doc files)."""
    result = check_docs_updated(["docs/api.md"])
    assert len(result["missing_docs"]) == 0


def test_check_docs_updated_empty():
    """Test with empty staged files list."""
    result = check_docs_updated([])
    assert len(result["missing_docs"]) == 0


def test_check_docs_updated_missing():
    """Test when doc file is missing for a source change."""
    result = check_docs_updated(["src/auth/login.py"])
    assert len(result["missing_docs"]) > 0


def run():
    """Run all tests in this module."""
    tests = [
        test_is_test_file,
        test_is_source_file,
        test_get_test_candidates,
        test_get_test_candidates_no_src_dir,
        test_get_test_candidates_root_level,
        test_check_tests_exist_no_source,
        test_check_tests_exist_empty,
        test_check_tests_exist_missing,
        test_check_tests_exist_with_test_in_staged,
        test_is_doc_file,
        test_check_docs_updated_no_source,
        test_check_docs_updated_empty,
        test_check_docs_updated_missing,
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
    print(f"checker tests: {p} passed, {f} failed")
