import os
import re
import subprocess
import sys


HIGH_RISK_PATTERNS = [
    {
        "pattern": r"(password|secret|token|credential|api.?key)",
        "reason": "credentials or secrets detected in diff",
        "level": "high",
    },
    {
        "pattern": r"(DROP\s+TABLE|DELETE\s+FROM|TRUNCATE\s+)",
        "reason": "database destructive operation detected",
        "level": "high",
    },
    {
        "pattern": r"(exec\s*\(|eval\s*\(|os\.system|subprocess\.)",
        "reason": "dynamic code execution detected",
        "level": "high",
    },
]

HIGH_RISK_FILES = [
    {
        "patterns": ["**/migrations/*", "**/alembic/*", "**/db/migrate*"],
        "reason": "database migration modified",
        "level": "high",
    },
    {
        "patterns": [
            "**/Dockerfile*", "**/docker-compose*", "**/Dockerfile.*",
        ],
        "reason": "docker/deployment config modified",
        "level": "medium",
    },
    {
        "patterns": [
            ".env*", "**/config/production*", "**/config/prod*",
            "**/secrets*", "**/credentials*",
        ],
        "reason": "production configuration or secrets file modified",
        "level": "high",
    },
    {
        "patterns": [
            "**/ci*", "**/.github/workflows/*", "**/Jenkinsfile*",
            "**/.gitlab-ci*",
        ],
        "reason": "CI/CD pipeline modified",
        "level": "medium",
    },
    {
        "patterns": [
            "requirements.txt", "Pipfile*", "pyproject.toml",
            "package.json", "Cargo.toml", "go.mod",
        ],
        "reason": "project dependencies modified",
        "level": "medium",
    },
    {
        "patterns": ["**/auth*", "**/login*", "**/oauth*", "**/sso*"],
        "reason": "authentication/authorization code modified",
        "level": "high",
    },
    {
        "patterns": ["**/security*", "**/encrypt*", "**/crypto*"],
        "reason": "security-related code modified",
        "level": "high",
    },
]


def _get_file_statuses():
    """Get list of (status, file_path) for staged files.

    Status: A (added), M (modified), D (deleted), R (renamed)
    """
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
                entries.append((parts[0], parts[1]))
            elif len(parts) == 1 and parts[0].startswith("R"):
                sub_parts = parts[0].split("\t")
                if len(sub_parts) >= 3:
                    entries.append((sub_parts[0], sub_parts[2]))
        return entries
    except subprocess.CalledProcessError as e:
        print(f"error getting file statuses: {e.stderr}")
        return []


def _get_diff_content(file_path):
    """Get the staged diff content for a specific file."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", file_path],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout
    except subprocess.CalledProcessError:
        return ""


def _match_glob(file_path, pattern):
    """Check if a file path matches a glob pattern (supports **)."""
    import fnmatch

    normalized_path = file_path.replace("\\", "/")
    pattern = pattern.replace("\\", "/")

    if pattern.startswith("**/"):
        suffix = pattern[3:]
        parts = normalized_path.split("/")
        for i in range(len(parts)):
            subpath = "/".join(parts[i:])
            if fnmatch.fnmatch(subpath, suffix):
                return True
        return fnmatch.fnmatch(normalized_path, suffix)

    return fnmatch.fnmatch(normalized_path, pattern)


def _check_file_risks(file_statuses):
    """Check for risks based on file paths and their change status.

    Args:
        file_statuses: List of (status, file_path) tuples

    Returns:
        List of risk dicts with keys: file, status, reason, level
    """
    risks = []

    for status, file_path in file_statuses:
        if status == "D":
            risks.append({
                "file": file_path,
                "status": "deleted",
                "reason": "file deleted",
                "level": "medium",
            })

        for rule in HIGH_RISK_FILES:
            for pattern in rule["patterns"]:
                if _match_glob(file_path, pattern):
                    risks.append({
                        "file": file_path,
                        "status": status,
                        "reason": rule["reason"],
                        "level": rule["level"],
                    })
                    break

    return risks


def _check_content_risks(file_statuses):
    """Check for risks by scanning diff content.

    Args:
        file_statuses: List of (status, file_path) tuples

    Returns:
        List of risk dicts
    """
    risks = []

    for status, file_path in file_statuses:
        if status == "D":
            continue

        diff = _get_diff_content(file_path)

        for rule in HIGH_RISK_PATTERNS:
            matches = re.findall(
                rule["pattern"], diff, re.IGNORECASE
            )
            if matches:
                risks.append({
                    "file": file_path,
                    "status": status,
                    "reason": rule["reason"],
                    "level": rule["level"],
                    "matches": list(set(matches))[:3],
                })

    return risks


def analyze_risks():
    """Run risk analysis on all staged changes.

    Returns:
        Dict with:
            risks: List of all risks found
            has_high_risk: True if any high-level risk found
            has_medium_risk: True if any medium-level risk found
            risk_count: Total number of risks
    """
    file_statuses = _get_file_statuses()

    file_risks = _check_file_risks(file_statuses)
    content_risks = _check_content_risks(file_statuses)

    all_risks = file_risks + content_risks

    return {
        "risks": all_risks,
        "has_high_risk": any(r["level"] == "high" for r in all_risks),
        "has_medium_risk": any(r["level"] == "medium" for r in all_risks),
        "risk_count": len(all_risks),
    }


def format_risks(result):
    """Format risk analysis result for display.

    Args:
        result: Dict from analyze_risks()

    Returns:
        Formatted string, or None if no risks found
    """
    if not result["risks"]:
        return None

    lines = []
    lines.append("risk analysis")
    lines.append("")

    high_risks = [r for r in result["risks"] if r["level"] == "high"]
    medium_risks = [r for r in result["risks"] if r["level"] == "medium"]

    if high_risks:
        lines.append("  high risk:")
        for r in high_risks:
            status_flag = ""
            if r.get("status") == "D":
                status_flag = " [deleted]"
            elif r.get("status") == "A":
                status_flag = " [new]"
            lines.append(f"    {r['file']}{status_flag}")
            lines.append(f"      reason: {r['reason']}")
        lines.append("")

    if medium_risks:
        lines.append("  medium risk:")
        for r in medium_risks:
            status_flag = ""
            if r.get("status") == "D":
                status_flag = " [deleted]"
            elif r.get("status") == "A":
                status_flag = " [new]"
            lines.append(f"    {r['file']}{status_flag}")
            lines.append(f"      reason: {r['reason']}")
        lines.append("")

    if result["has_high_risk"]:
        lines.append("result: FAIL - high risk changes detected")
    elif result["has_medium_risk"]:
        lines.append("result: WARN - medium risk changes detected")
    else:
        lines.append("result: PASS - no risky changes")

    return "\n".join(lines)


def main():
    """CLI entry point for risk analysis."""
    result = analyze_risks()
    msg = format_risks(result)

    if msg:
        print(msg)

    if result["has_high_risk"]:
        sys.exit(2)
    elif result["has_medium_risk"]:
        sys.exit(1)
    else:
        if not msg:
            print("risk analysis: no risky changes detected")
        sys.exit(0)


if __name__ == "__main__":
    main()
