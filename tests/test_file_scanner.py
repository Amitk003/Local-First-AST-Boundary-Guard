"""Tests for the file scanner module."""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from code_guardian.file_scanner import is_file_allowed, check_file_scope


def test_is_file_allowed():
    """Test basic file matching against allowed patterns."""
    assert is_file_allowed("src/auth/login.py", ["src/auth/*"])
    assert is_file_allowed("src/auth/login.py", ["src/auth/*.py"])
    assert is_file_allowed("src/auth/login.py", ["src/**"])
    assert is_file_allowed("src/auth/login.py", ["**/*.py"])
    assert not is_file_allowed("src/payment/pay.py", ["src/auth/*"])
    assert not is_file_allowed("src/auth/login.py", ["src/payment/*"])


def test_is_file_allowed_multiple_patterns():
    """Test matching against multiple allowed patterns."""
    patterns = ["src/auth/*", "src/common/*"]
    assert is_file_allowed("src/auth/login.py", patterns)
    assert is_file_allowed("src/common/utils.py", patterns)
    assert not is_file_allowed("src/payment/pay.py", patterns)


def test_check_file_scope_all_allowed():
    """Test when all files are within allowed scope."""
    staged = ["src/auth/login.py", "src/auth/register.py"]
    result = check_file_scope(staged, ["src/auth/*"])
    assert len(result["unauthorized"]) == 0
    assert len(result["allowed"]) == 2


def test_check_file_scope_unauthorized():
    """Test when some files are outside allowed scope."""
    staged = ["src/auth/login.py", "src/payment/pay.py"]
    result = check_file_scope(staged, ["src/auth/*"])
    assert len(result["unauthorized"]) == 1
    assert result["unauthorized"][0] == "src/payment/pay.py"
    assert len(result["allowed"]) == 1
    assert result["allowed"][0] == "src/auth/login.py"


def test_check_file_scope_all_unauthorized():
    """Test when no files are within allowed scope."""
    staged = ["src/payment/pay.py", "src/db/migrate.py"]
    result = check_file_scope(staged, ["src/auth/*"])
    assert len(result["unauthorized"]) == 2
    assert len(result["allowed"]) == 0


def test_check_file_scope_no_patterns():
    """Test when no allowed patterns are provided (all files pass)."""
    staged = ["src/auth/login.py", "src/payment/pay.py"]
    result = check_file_scope(staged, [])
    assert len(result["unauthorized"]) == 0
    assert len(result["allowed"]) == 2


def test_check_file_scope_wildcard_extensions():
    """Test matching with wildcard file extensions."""
    patterns = ["src/auth/*.py", "docs/*.md"]
    assert is_file_allowed("src/auth/login.py", patterns)
    assert is_file_allowed("docs/readme.md", patterns)
    assert not is_file_allowed("src/auth/login.js", patterns)
    assert not is_file_allowed("src/payment/pay.py", patterns)


def test_check_file_scope_deep_paths():
    """Test matching in nested directory structures."""
    patterns = ["src/**/handlers/*"]
    assert is_file_allowed("src/auth/handlers/login.py", patterns)
    assert is_file_allowed("src/payment/handlers/pay.py", patterns)
    assert not is_file_allowed("src/auth/models/user.py", patterns)


def test_is_file_allowed_empty_pattern():
    """Test that empty patterns don't cause errors."""
    assert not is_file_allowed("src/auth/login.py", [""])
    assert not is_file_allowed("src/auth/login.py", ["  "])


def test_is_file_allowed_different_dirs():
    """Test that files in different directories don't match."""
    patterns = ["src/payment/*"]
    assert not is_file_allowed("src/auth/login.py", patterns)


def run():
    """Run all tests in this module."""
    tests = [
        test_is_file_allowed,
        test_is_file_allowed_multiple_patterns,
        test_check_file_scope_all_allowed,
        test_check_file_scope_unauthorized,
        test_check_file_scope_all_unauthorized,
        test_check_file_scope_no_patterns,
        test_check_file_scope_wildcard_extensions,
        test_check_file_scope_deep_paths,
        test_is_file_allowed_empty_pattern,
        test_is_file_allowed_different_dirs,
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
    print(f"file scanner tests: {p} passed, {f} failed")
