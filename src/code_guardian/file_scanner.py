import fnmatch
import os
import subprocess
import sys


def get_staged_files():
    """Get list of files staged for commit.

    Returns:
        List of file paths relative to repo root
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
            capture_output=True,
            text=True,
            check=True,
            cwd=_get_repo_root(),
        )
        files = [f.strip() for f in result.stdout.splitlines() if f.strip()]
        return files
    except subprocess.CalledProcessError as e:
        print(f"Error getting staged files: {e.stderr}")
        return []


def get_changed_files():
    """Get list of all changed files (staged + unstaged).

    Returns:
        List of file paths relative to repo root
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=ACMR"],
            capture_output=True,
            text=True,
            check=True,
            cwd=_get_repo_root(),
        )
        staged = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
            capture_output=True,
            text=True,
            check=True,
            cwd=_get_repo_root(),
        )
        all_files = set()
        for f in result.stdout.splitlines():
            if f.strip():
                all_files.add(f.strip())
        for f in staged.stdout.splitlines():
            if f.strip():
                all_files.add(f.strip())
        return sorted(all_files)
    except subprocess.CalledProcessError as e:
        print(f"Error getting changed files: {e.stderr}")
        return []


def _get_repo_root():
    """Get the git repo root directory."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return os.getcwd()


def is_file_allowed(file_path, allowed_patterns):
    """Check if a file path matches any of the allowed glob patterns.

    Args:
        file_path: Relative file path (e.g. src/auth/login.py)
        allowed_patterns: List of glob patterns (e.g. ["src/auth/*"])

    Returns:
        True if the file matches at least one allowed pattern
    """
    for pattern in allowed_patterns:
        pattern = pattern.strip()
        if not pattern:
            continue

        if fnmatch.fnmatch(file_path, pattern):
            return True

        if fnmatch.fnmatch(os.path.basename(file_path), pattern):
            return True

        dir_pattern = pattern.rstrip("/") + "/*"
        if fnmatch.fnmatch(file_path, dir_pattern):
            return True

        dir_pattern2 = pattern.rstrip("/") + "/**"
        if fnmatch.fnmatch(file_path, dir_pattern2):
            return True

    return False


def check_file_scope(staged_files, allowed_patterns):
    """Check which files are outside the allowed scope.

    Args:
        staged_files: List of file paths
        allowed_patterns: List of allowed glob patterns

    Returns:
        Dict with keys:
            allowed: List of files that are within allowed scope
            unauthorized: List of files that are outside allowed scope
    """
    if not allowed_patterns:
        return {"allowed": staged_files, "unauthorized": []}

    allowed = []
    unauthorized = []

    for file_path in staged_files:
        if is_file_allowed(file_path, allowed_patterns):
            allowed.append(file_path)
        else:
            unauthorized.append(file_path)

    return {"allowed": allowed, "unauthorized": unauthorized}


def format_scope_violation(violations, allowed_patterns):
    """Format scope violation message for display.

    Args:
        violations: Dict from check_file_scope()
        allowed_patterns: List of allowed file patterns

    Returns:
        Formatted string describing violations
    """
    if not violations["unauthorized"]:
        return None

    lines = []
    lines.append("unauthorized file modification detected")
    lines.append("")
    lines.append("changed:")
    for f in violations["unauthorized"]:
        lines.append(f"  - {f}")
    lines.append("")
    lines.append("allowed:")
    for p in allowed_patterns:
        lines.append(f"  - {p}")
    lines.append("")
    lines.append("commit blocked")

    return "\n".join(lines)


def main():
    """CLI entry point for file scanning."""
    if len(sys.argv) < 2:
        staged = get_staged_files()
        if not staged:
            print("no staged files found")
            return
        for f in staged:
            print(f)
        return

    command = sys.argv[1]

    if command == "check":
        allowed = sys.argv[2:] if len(sys.argv) > 2 else []
        staged = get_staged_files()
        violations = check_file_scope(staged, allowed)
        msg = format_scope_violation(violations, allowed)
        if msg:
            print(msg)
            sys.exit(1)
        else:
            print("all file changes are within allowed scope")

    elif command == "staged":
        files = get_staged_files()
        for f in files:
            print(f)

    elif command == "changed":
        files = get_changed_files()
        for f in files:
            print(f)

    else:
        print(f"unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
