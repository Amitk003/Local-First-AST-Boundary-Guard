"""Tests for the release notes module."""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from code_guardian.release_notes import (
    _classify_file,
    format_release_notes,
    save_release_notes,
)


def test_classify_file_feature():
    """Test classification of feature files."""
    category, desc = _classify_file("src/features/login.py")
    assert category == "features"


def test_classify_file_fix():
    """Test classification of bug fix files."""
    category, desc = _classify_file("src/fixes/login.py")
    assert category == "fixes"


def test_classify_file_test():
    """Test classification of test files."""
    category, desc = _classify_file("tests/test_login.py")
    assert category == "tests"


def test_classify_file_docs():
    """Test classification of documentation files."""
    category, desc = _classify_file("docs/api.md")
    assert category == "docs"


def test_classify_file_config():
    """Test classification of config files."""
    category, desc = _classify_file("requirements.txt")
    assert category == "chore"
    category, desc = _classify_file("config.json")
    assert category == "chore"


def test_classify_file_source():
    """Test classification of regular source files."""
    category, desc = _classify_file("src/app/utils.py")
    assert category == "features"


def test_format_release_notes_empty():
    """Test formatting when no files changed."""
    data = {
        "version": "1.0.0",
        "date": "2026-06-30",
        "commit_message": "test commit",
        "categories": {},
        "total_files": 0,
    }
    text = format_release_notes(data)
    assert "1.0.0" in text
    assert "2026-06-30" in text


def test_format_release_notes_with_data():
    """Test formatting when files are categorized."""
    data = {
        "version": "1.0.0",
        "date": "2026-06-30",
        "commit_message": "test commit",
        "categories": {
            "features": [
                {"file": "src/features/login.py", "status": "added",
                 "description": "New feature: src/features/login.py"},
            ],
            "fixes": [
                {"file": "src/fixes/bug.py", "status": "modified",
                 "description": "Bug fix: src/fixes/bug.py"},
            ],
            "tests": [
                {"file": "tests/test_login.py", "status": "added",
                 "description": "Added/modified tests: tests/test_login.py"},
            ],
        },
        "total_files": 3,
    }
    text = format_release_notes(data)
    assert "Features" in text
    assert "Bug Fixes" in text
    assert "Tests" in text
    assert "3" in text


def test_save_release_notes():
    """Test saving release notes to a file."""
    data = {
        "version": "1.0.0",
        "date": "2026-06-30",
        "commit_message": "test",
        "categories": {},
        "total_files": 0,
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = save_release_notes(data, tmpdir)
        assert os.path.exists(filepath)
        assert filepath.endswith(".md")

        with open(filepath) as f:
            content = f.read()
        assert "1.0.0" in content


def run():
    """Run all tests in this module."""
    tests = [
        test_classify_file_feature,
        test_classify_file_fix,
        test_classify_file_test,
        test_classify_file_docs,
        test_classify_file_config,
        test_classify_file_source,
        test_format_release_notes_empty,
        test_format_release_notes_with_data,
        test_save_release_notes,
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
    print(f"release notes tests: {p} passed, {f} failed")
