import json
import os
import sys
from datetime import datetime


def build_packet(intent, staged_files, checks_results, passed):
    """Build a structured review packet with all check results.

    Args:
        intent: Dict with issue_id and allowed_files, or None
        staged_files: List of staged file paths
        checks_results: Dict with check names as keys, result dicts as values
        passed: True if all checks passed

    Returns:
        Dict with complete review data
    """
    now = datetime.utcnow().isoformat() + "Z"

    packet = {
        "review_id": now,
        "timestamp": now,
        "status": "approved" if passed else "blocked",
        "summary": {
            "total_checks": len(checks_results),
            "passed": sum(1 for c in checks_results.values() if c["passed"]),
            "failed": sum(1 for c in checks_results.values() if not c["passed"]),
        },
        "intent": intent,
        "files_changed": staged_files,
        "checks": {},
    }

    for name, result in checks_results.items():
        entry = {"status": "pass" if result["passed"] else "fail"}

        if name == "scope":
            if "message" in result:
                entry["message"] = result["message"]
                entry["status"] = "skip"
            else:
                entry["unauthorized"] = result.get("unauthorized", [])
                entry["allowed_files"] = result.get("allowed_files", [])

        elif name == "tests":
            missing = result.get("missing", [])
            if missing:
                entry["missing_tests"] = [
                    {"source": m["source"], "expected": m["expected_test"]}
                    for m in missing
                ]

        elif name == "docs":
            missing = result.get("missing", [])
            if missing:
                entry["missing_docs"] = [
                    {"source": m["source"], "expected": m["expected_doc"]}
                    for m in missing
                ]

        elif name == "risk":
            risks = result.get("risks", [])
            if risks:
                entry["risks"] = [
                    {
                        "file": r["file"],
                        "level": r["level"],
                        "reason": r["reason"],
                    }
                    for r in risks
                ]

        packet["checks"][name] = entry

    return packet


def format_packet(packet):
    """Format the review packet as a human-readable string.

    Args:
        packet: Dict from build_packet()

    Returns:
        Formatted string
    """
    lines = []
    lines.append("=" * 55)
    lines.append("  Code Guardian Review Packet")
    lines.append("=" * 55)
    lines.append("")

    status = packet["status"]
    if status == "approved":
        status_line = "  Status: APPROVED (commit allowed)"
    else:
        status_line = "  Status: BLOCKED (commit rejected)"
    lines.append(status_line)

    summary = packet["summary"]
    lines.append(
        f"  Checks: {summary['passed']} passed, "
        f"{summary['failed']} failed "
        f"(out of {summary['total_checks']})"
    )
    lines.append("")

    if packet["intent"]:
        intent = packet["intent"]
        lines.append(f"  Intent: {intent['issue_id']}")
        lines.append(f"  Allowed files: {', '.join(intent['allowed_files'])}")
    else:
        lines.append("  Intent: none")
    lines.append("")

    files = packet.get("files_changed", [])
    if files:
        lines.append("  Files changed:")
        for f in files:
            lines.append(f"    - {f}")
    else:
        lines.append("  Files changed: none")
    lines.append("")

    checks = packet.get("checks", {})
    for name in ["scope", "tests", "docs", "risk"]:
        check = checks.get(name)
        if check is None:
            continue

        if check["status"] == "pass":
            status_tag = "PASS"
            icon = "OK"
        elif check["status"] == "skip":
            status_tag = "SKIP"
            icon = "--"
        else:
            status_tag = "FAIL"
            icon = "XX"

        if name == "scope":
            lines.append(f"  [{status_tag}] File Scope Check")
            if "message" in check:
                lines.append(f"           {check['message']}")
            elif check.get("unauthorized"):
                for f in check["unauthorized"]:
                    lines.append(f"           Unauthorized: {f}")

        elif name == "tests":
            lines.append(f"  [{status_tag}] Test Files Check")
            if check.get("missing_tests"):
                for m in check["missing_tests"]:
                    lines.append(
                        f"           Missing: {m['expected']} "
                        f"(for {m['source']})"
                    )
            elif check["status"] == "pass":
                lines.append("           All tests present")

        elif name == "docs":
            lines.append(f"  [{status_tag}] Documentation Check")
            if check.get("missing_docs"):
                for m in check["missing_docs"]:
                    lines.append(
                        f"           Missing: {m['expected']} "
                        f"(for {m['source']})"
                    )
            elif check["status"] == "pass":
                lines.append("           Documentation up to date")

        elif name == "risk":
            lines.append(f"  [{status_tag}] Risk Analysis")
            if check.get("risks"):
                for r in check["risks"]:
                    lines.append(
                        f"           [{r['level']}] {r['file']} - {r['reason']}"
                    )
            elif check["status"] == "pass":
                lines.append("           No risky changes detected")

        lines.append("")

    lines.append("-" * 55)
    if status == "approved":
        lines.append("  All checks passed. Commit approved.")
    else:
        lines.append("  One or more checks failed. Fix the issues and try again.")
    lines.append("=" * 55)

    return "\n".join(lines)


def save_packet(packet, output_dir=None):
    """Save the review packet as a JSON file.

    Args:
        packet: Dict from build_packet()
        output_dir: Directory to save the packet file (default: current dir)

    Returns:
        Path to the saved file
    """
    if output_dir is None:
        output_dir = os.getcwd()

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"review_packet_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w") as f:
        json.dump(packet, f, indent=2)

    return filepath


def review_packet_main():
    """CLI entry point to generate a review packet and optionally save it."""
    from code_guardian.file_scanner import get_staged_files
    from code_guardian.intent_manager import list_active_intents, get_allowed_files
    from code_guardian.test_checker import check_tests_exist
    from code_guardian.docs_checker import check_docs_updated
    from code_guardian.risk_analyzer import analyze_risks

    staged = get_staged_files()

    intent = None
    try:
        intents = list_active_intents()
        if intents:
            intent_data = intents[0]
            intent = {
                "issue_id": intent_data.get("issue_id", "unknown"),
                "allowed_files": get_allowed_files(intent_data["id"]),
            }
    except Exception:
        pass

    checks = {}

    if intent and intent["allowed_files"]:
        from code_guardian.file_scanner import check_file_scope

        scope_result = check_file_scope(staged, intent["allowed_files"])
        checks["scope"] = {
            "passed": len(scope_result["unauthorized"]) == 0,
            "unauthorized": scope_result["unauthorized"],
            "allowed_files": intent["allowed_files"],
        }
    else:
        checks["scope"] = {"passed": True, "message": "no active intent - scope check skipped"}

    test_result = check_tests_exist(staged)
    checks["tests"] = {
        "passed": len(test_result["missing_tests"]) == 0,
        "missing": test_result["missing_tests"],
    }

    docs_result = check_docs_updated(staged)
    checks["docs"] = {
        "passed": len(docs_result["missing_docs"]) == 0,
        "missing": docs_result["missing_docs"],
    }

    risk_result = analyze_risks()
    checks["risk"] = {
        "passed": not risk_result["has_high_risk"],
        "risks": risk_result["risks"],
        "has_high": risk_result["has_high_risk"],
        "has_medium": risk_result["has_medium_risk"],
    }

    all_passed = all(c["passed"] for c in checks.values())

    packet = build_packet(intent, staged, checks, all_passed)
    text = format_packet(packet)

    print(text)

    if "--save" in sys.argv:
        filepath = save_packet(packet)
        print(f"\nPacket saved to: {filepath}")

    if not all_passed:
        sys.exit(1)


if __name__ == "__main__":
    review_packet_main()
