import os
import re
import sys


def _get_test_candidates(source_file):
    """Generate possible test file paths for a given source file.

    Common patterns checked:
      src/module/feature.py -> tests/test_module_feature.py
      src/module/feature.py -> tests/test_feature.py
      src/module/feature.py -> tests/module/test_feature.py
      src/module/feature.py -> tests/module/test_module_feature.py

    Args:
        source_file: Relative path to the source file

    Returns:
        List of potential test file paths
    """
    candidates = []

    base_name = os.path.basename(source_file)
    name_no_ext = os.path.splitext(base_name)[0]

    parts = source_file.replace("\\", "/").split("/")

    src_index = -1
    for i, part in enumerate(parts):
        if part in ("src", "app", "lib", "module"):
            src_index = i
            break

    if src_index >= 0:
        relative_parts = parts[src_index + 1:]
    else:
        relative_parts = parts

    rel_path = "/".join(relative_parts)
    rel_dir = os.path.dirname(rel_path) if len(relative_parts) > 1 else ""

    # Pattern 1: tests/test_<module>_<feature>.py
    if rel_dir:
        dir_slug = rel_dir.replace("/", "_").replace("\\", "_")
        candidates.append(f"tests/test_{dir_slug}_{name_no_ext}.py")

    # Pattern 2: tests/test_<feature>.py
    candidates.append(f"tests/test_{name_no_ext}.py")

    # Pattern 3: tests/<module_dir>/test_<feature>.py
    if rel_dir:
        candidates.append(f"tests/{rel_dir}/test_{name_no_ext}.py")

    # Pattern 4: test_<feature>.py in same directory
    candidates.append(
        f"{os.path.dirname(source_file)}/test_{name_no_ext}.py"
    )

    # Pattern 5: tests/<module_dir>/test_<module>_<feature>.py
    if rel_dir:
        dir_slug = rel_dir.replace("/", "_").replace("\\", "_")
        candidates.append(
            f"tests/{rel_dir}/test_{dir_slug}_{name_no_ext}.py"
        )

    return candidates


def _is_test_file(file_path):
    """Check if a file is a test file based on name pattern."""
    base = os.path.basename(file_path)
    return base.startswith("test_") or base.endswith("_test.py")


def _is_source_file(file_path):
    """Check if a file is a code source file (not test or config)."""
    ext = os.path.splitext(file_path)[1]
    source_exts = {
        ".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java",
        ".rb", ".php", ".c", ".cpp", ".h", ".hpp",
    }
    base = os.path.basename(file_path)

    if _is_test_file(file_path):
        return False

    if base.startswith("."):
        return False

    if ext in (".md", ".rst", ".txt", ".json", ".yaml", ".yml", ".toml", ".cfg", ".ini"):
        return False

    return ext in source_exts


def check_tests_exist(staged_files, repo_root=None):
    """Check if test files exist for changed source files.

    Args:
        staged_files: List of changed file paths (relative to repo root)
        repo_root: Repository root directory (optional)

    Returns:
        Dict with keys:
            missing_tests: List of dicts with 'source' and 'expected_test' keys
            test_files_found: List of test files that were changed
    """
    if repo_root is None:
        repo_root = os.getcwd()

    missing_tests = []
    test_files_changed = [f for f in staged_files if _is_test_file(f)]
    source_files = [f for f in staged_files if _is_source_file(f)]

    for source in source_files:
        found = False
        candidates = _get_test_candidates(source)

        for candidate in candidates:
            full_path = os.path.join(repo_root, candidate)
            if os.path.exists(full_path):
                found = True
                break

            for changed_test in test_files_changed:
                candidate_base = os.path.basename(candidate)
                changed_base = os.path.basename(changed_test)
                if candidate_base == changed_base:
                    found = True
                    break

            if found:
                break

        if not found:
            missing_tests.append(
                {"source": source, "expected_test": candidates[0]}
            )

    return {
        "missing_tests": missing_tests,
        "test_files_changed": test_files_changed,
    }


def format_test_check(result):
    """Format test check result for display.

    Args:
        result: Dict from check_tests_exist()

    Returns:
        Formatted string, or None if nothing to report
    """
    if not result["missing_tests"]:
        return None

    lines = []
    lines.append("missing test files")
    lines.append("")
    for item in result["missing_tests"]:
        lines.append(f"  {item['source']} -> expected: {item['expected_test']}")
    lines.append("")

    return "\n".join(lines)


def main():
    """CLI entry point for test checking."""
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        from code_guardian.file_scanner import get_staged_files

        staged = get_staged_files()
        result = check_tests_exist(staged)
        msg = format_test_check(result)
        if msg:
            print(msg)
            sys.exit(1)
        else:
            print("tests verification passed")
    else:
        print("usage: python -m code_guardian.test_checker check")


if __name__ == "__main__":
    main()
