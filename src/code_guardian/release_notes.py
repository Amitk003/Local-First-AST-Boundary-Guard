import os
import subprocess
import sys
from datetime import datetime
from collections import defaultdict


FEATURE_DIRS = {"feature", "feat", "new"}
FIX_DIRS = {"fix", "bugfix", "hotfix", "patch"}
TEST_PREFIXES = {"test_", "test-"}
DOC_EXTENSIONS = {".md", ".rst", ".txt", ".adoc"}
CONFIG_EXTENSIONS = {
    ".json", ".yaml", ".yml", ".toml", ".cfg", ".ini",
    ".env", ".conf",
}
CONFIG_FILES = {
    "requirements.txt", "package.json", "Cargo.toml", "go.mod",
    "pyproject.toml", "Pipfile", "Makefile", "Dockerfile",
    ".pre-commit-config.yaml",
}


def _get_commit_message():
    """Get the commit message being used for this commit."""
    try:
        result = subprocess.run(
            ["git", "log", "--format=%s", "-1"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return ""


def _classify_file(file_path):
    """Classify a file change into a release note category.

    Returns:
        Tuple of (category, description)
    """
    base = os.path.basename(file_path)
    ext = os.path.splitext(file_path)[1].lower()
    name_lower = base.lower()
    path_lower = file_path.lower()

    if base in CONFIG_FILES or ext in CONFIG_EXTENSIONS:
        return ("chore", f"Updated configuration: {file_path}")

    if ext in DOC_EXTENSIONS:
        return ("docs", f"Updated documentation: {file_path}")

    if name_lower.startswith("test_") or name_lower.endswith("_test.py"):
        return ("tests", f"Added/modified tests: {file_path}")

    if any(d in path_lower for d in FEATURE_DIRS):
        return ("features", f"New feature: {file_path}")

    if any(d in path_lower for d in FIX_DIRS):
        return ("fixes", f"Bug fix: {file_path}")

    if ext in (".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java"):
        dir_name = os.path.basename(os.path.dirname(file_path))
        clean_name = os.path.splitext(base)[0]
        return ("features", f"Updated {clean_name} in {dir_name}")

    return ("other", f"Changed: {file_path}")


def _get_staged_files_with_status():
    """Get (status, file) tuples for staged changes."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-status"],
            capture_output=True,
            text=True,
            check=True,
        )
        entries = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t", 1)
            if len(parts) == 2:
                status_code = parts[0][0]
                entries.append((status_code, parts[1]))
        return entries
    except subprocess.CalledProcessError:
        return []


def _status_label(status_code):
    """Convert git status code to a readable label."""
    labels = {
        "A": "added",
        "M": "modified",
        "D": "deleted",
        "R": "renamed",
        "C": "copied",
    }
    return labels.get(status_code, "changed")


def generate_release_notes(version=None):
    """Generate release notes from staged changes.

    Args:
        version: Optional version string (e.g. "1.4.0")

    Returns:
        Dict with release notes data
    """
    files = _get_staged_files_with_status()
    commit_msg = _get_commit_message()

    categories = defaultdict(list)

    for status_code, file_path in files:
        category, description = _classify_file(file_path)
        categories[category].append({
            "file": file_path,
            "status": _status_label(status_code),
            "description": description,
        })

    return {
        "version": version or get_next_version(),
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "commit_message": commit_msg,
        "categories": dict(categories),
        "total_files": len(files),
    }


def get_next_version():
    """Guess the next version by looking at git tags or using default."""
    try:
        result = subprocess.run(
            ["git", "tag", "--sort=-v:refname"],
            capture_output=True,
            text=True,
            check=True,
        )
        tags = [t.strip() for t in result.stdout.splitlines() if t.strip()]
        if tags:
            latest = tags[0].lstrip("v")
            parts = latest.split(".")
            parts[-1] = str(int(parts[-1]) + 1)
            return ".".join(parts)
    except (subprocess.CalledProcessError, ValueError, IndexError):
        pass
    return "0.1.0"


def format_release_notes(data):
    """Format release notes as a readable string.

    Args:
        data: Dict from generate_release_notes()

    Returns:
        Formatted string
    """
    lines = []
    lines.append(f"Release v{data['version']}")
    lines.append(f"Date: {data['date']}")
    if data["commit_message"]:
        lines.append(f"Commit: {data['commit_message']}")
    lines.append("")
    lines.append("-" * 40)
    lines.append("")

    categories = data["categories"]
    all_labels = {
        "features": "Features",
        "fixes": "Bug Fixes",
        "tests": "Tests",
        "docs": "Documentation",
        "chore": "Chores",
        "other": "Other Changes",
    }

    has_content = False
    for key, label in all_labels.items():
        items = categories.get(key, [])
        if not items:
            continue
        has_content = True
        lines.append(f"  {label}")
        lines.append("")
        for item in items:
            lines.append(f"    - {item['description']}")
        lines.append("")

    if not has_content:
        lines.append("  No significant changes.")
        lines.append("")

    lines.append(f"  Total files changed: {data['total_files']}")

    return "\n".join(lines)


def save_release_notes(data, output_dir=None):
    """Save release notes to a file.

    Args:
        data: Dict from generate_release_notes()
        output_dir: Directory to save to (default: current dir)

    Returns:
        Path to the saved file
    """
    if output_dir is None:
        output_dir = os.getcwd()

    content = format_release_notes(data)
    filename = f"release_notes_v{data['version']}.md"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w") as f:
        f.write(content)

    return filepath


def main():
    """CLI entry point for release notes generation."""
    version = None
    save = False

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--version" and i + 1 < len(args):
            version = args[i + 1]
            i += 2
        elif args[i] == "--save":
            save = True
            i += 1
        else:
            i += 1

    data = generate_release_notes(version)
    text = format_release_notes(data)

    print(text)

    if save:
        filepath = save_release_notes(data)
        print(f"\nSaved to: {filepath}")


if __name__ == "__main__":
    main()
