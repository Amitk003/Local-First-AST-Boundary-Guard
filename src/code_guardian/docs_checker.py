import os
import sys


DOC_EXTENSIONS = {".md", ".rst", ".txt"}
DOC_DIRS = {"docs", "documentation", "doc", "wiki"}


def _is_doc_file(file_path):
    """Check if a file is a documentation file."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext in DOC_EXTENSIONS:
        return True
    parts = file_path.replace("\\", "/").split("/")
    for part in parts[:-1]:
        if part.lower() in DOC_DIRS:
            return True
    return False


def _is_test_file(file_path):
    """Check if a file is a test file based on name pattern."""
    base = os.path.basename(file_path)
    return base.startswith("test_") or base.endswith("_test.py")


def _is_source_file(file_path):
    """Check if a file is a code source file (not test or doc)."""
    ext = os.path.splitext(file_path)[1]
    source_exts = {
        ".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java",
        ".rb", ".php", ".c", ".cpp", ".h", ".hpp",
    }
    base = os.path.basename(file_path)

    if base.startswith("."):
        return False

    if _is_test_file(file_path):
        return False

    if ext in DOC_EXTENSIONS:
        return False

    if ext in (".json", ".yaml", ".yml", ".toml", ".cfg", ".ini", ".env"):
        return False

    return ext in source_exts


def _find_related_doc_paths(source_file):
    """Generate related documentation paths for a source file.

    Args:
        source_file: Relative path to the source file (e.g. src/auth/login.py)

    Returns:
        List of possible documentation file paths
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

    # Pattern 1: docs/<module>/<feature>.md
    if rel_dir:
        candidates.append(f"docs/{rel_dir}/{name_no_ext}.md")

    # Pattern 2: docs/<module>_<feature>.md
    if rel_dir:
        dir_slug = rel_dir.replace("/", "_").replace("\\", "_")
        candidates.append(f"docs/{dir_slug}_{name_no_ext}.md")

    # Pattern 3: docs/<feature>.md
    candidates.append(f"docs/{name_no_ext}.md")

    # Pattern 4: README.md in the source directory
    source_dir = os.path.dirname(source_file)
    candidates.append(f"{source_dir}/README.md")

    return candidates


def check_docs_updated(staged_files, repo_root=None):
    """Check if documentation was updated when source files changed.

    Args:
        staged_files: List of changed file paths
        repo_root: Repository root directory

    Returns:
        Dict with:
            missing_docs: List of source files without doc updates
            doc_files_changed: List of doc files that changed
            source_files_changed: List of source files changed
    """
    if repo_root is None:
        repo_root = os.getcwd()

    doc_files_changed = [f for f in staged_files if _is_doc_file(f)]
    source_files = [f for f in staged_files if _is_source_file(f)]

    missing_docs = []

    for source in source_files:
        found = False

        candidates = _find_related_doc_paths(source)

        for candidate in candidates:
            full_path = os.path.join(repo_root, candidate)
            if os.path.exists(full_path):
                found = True
                break

            for doc_file in doc_files_changed:
                candidate_base = os.path.basename(candidate)
                doc_base = os.path.basename(doc_file)
                if candidate_base == doc_base:
                    found = True
                    break

            if found:
                break

        if not found:
            missing_docs.append(
                {"source": source, "expected_doc": candidates[0]}
            )

    return {
        "missing_docs": missing_docs,
        "doc_files_changed": doc_files_changed,
        "source_files_changed": source_files,
    }


def format_docs_check(result):
    """Format documentation check result for display.

    Args:
        result: Dict from check_docs_updated()

    Returns:
        Formatted string, or None if nothing to report
    """
    if not result["missing_docs"]:
        return None

    lines = []
    lines.append("missing documentation updates")
    lines.append("")
    for item in result["missing_docs"]:
        lines.append(f"  {item['source']} -> expected: {item['expected_doc']}")
    lines.append("")

    return "\n".join(lines)


def main():
    """CLI entry point for docs checking."""
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        from code_guardian.file_scanner import get_staged_files

        staged = get_staged_files()
        result = check_docs_updated(staged)
        msg = format_docs_check(result)
        if msg:
            print(msg)
            sys.exit(1)
        else:
            print("documentation verification passed")
    else:
        print("usage: python -m code_guardian.docs_checker check")


if __name__ == "__main__":
    main()
