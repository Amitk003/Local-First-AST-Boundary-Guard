import sys


def get_intent_for_hook():
    """Try to get the active intent from the intent manager.

    Returns a dict with issue_id, allowed_files or None.
    """
    try:
        from code_guardian.intent_manager import list_active_intents, get_allowed_files

        intents = list_active_intents()
        if intents:
            intent = intents[0]
            return {
                "issue_id": intent.get("issue_id", "unknown"),
                "allowed_files": get_allowed_files(intent["id"]),
            }
    except Exception:
        pass
    return None


def run_checks():
    """Run all pre-commit checks and print results.

    Returns:
        Tuple of (passed: bool, results: dict)
    """
    from code_guardian.file_scanner import get_staged_files, check_file_scope
    from code_guardian.test_checker import check_tests_exist
    from code_guardian.docs_checker import check_docs_updated
    from code_guardian.risk_analyzer import analyze_risks

    staged = get_staged_files()
    intent = get_intent_for_hook()

    results = {"intent": intent, "staged_files": staged, "checks": {}}
    all_passed = True

    # File scope check
    if intent and intent["allowed_files"]:
        scope_result = check_file_scope(staged, intent["allowed_files"])
        results["checks"]["scope"] = {
            "passed": len(scope_result["unauthorized"]) == 0,
            "unauthorized": scope_result["unauthorized"],
            "allowed_files": intent["allowed_files"],
        }
        if not results["checks"]["scope"]["passed"]:
            all_passed = False
    else:
        results["checks"]["scope"] = {"passed": True, "message": "no active intent - scope check skipped"}

    # Test check
    test_result = check_tests_exist(staged)
    results["checks"]["tests"] = {
        "passed": len(test_result["missing_tests"]) == 0,
        "missing": test_result["missing_tests"],
    }
    if not results["checks"]["tests"]["passed"]:
        all_passed = False

    # Docs check
    docs_result = check_docs_updated(staged)
    results["checks"]["docs"] = {
        "passed": len(docs_result["missing_docs"]) == 0,
        "missing": docs_result["missing_docs"],
    }
    if not results["checks"]["docs"]["passed"]:
        all_passed = False

    # Risk analysis
    risk_result = analyze_risks()
    results["checks"]["risk"] = {
        "passed": not risk_result["has_high_risk"],
        "risks": risk_result["risks"],
        "has_high": risk_result["has_high_risk"],
        "has_medium": risk_result["has_medium_risk"],
    }
    if risk_result["has_high_risk"]:
        all_passed = False

    return all_passed, results


def print_review(results, passed):
    """Print a formatted review summary."""
    lines = []
    lines.append("Code Guardian Review")
    lines.append("=" * 50)
    lines.append("")

    # Intent
    intent = results.get("intent")
    if intent:
        lines.append(f"  Intent: {intent['issue_id']} (active)")
        lines.append(f"  Allowed files: {', '.join(intent['allowed_files'])}")
    else:
        lines.append("  Intent: none (scope check skipped)")
    lines.append("")

    # Files changed
    staged = results.get("staged_files", [])
    if staged:
        lines.append("  Files changed:")
        for f in staged:
            lines.append(f"    - {f}")
    else:
        lines.append("  No files staged for commit")
    lines.append("")

    # Check results
    checks = results.get("checks", {})
    for check_name in ["scope", "tests", "docs", "risk"]:
        check = checks.get(check_name)
        if check is None:
            continue

        status = "PASS" if check["passed"] else "FAIL"
        label = check_name.upper()

        if check_name == "scope":
            if "message" in check:
                lines.append(f"  [{label}] SKIP - {check['message']}")
            else:
                lines.append(f"  [{label}] {status}")
                if check.get("unauthorized"):
                    for f in check["unauthorized"]:
                        lines.append(f"    unauthorized: {f}")

        elif check_name == "tests":
            lines.append(f"  [{label}] {status}")
            if check.get("missing"):
                for item in check["missing"]:
                    lines.append(f"    missing: {item['expected_test']}")

        elif check_name == "docs":
            lines.append(f"  [{label}] {status}")
            if check.get("missing"):
                for item in check["missing"]:
                    lines.append(f"    missing: {item['expected_doc']}")

        elif check_name == "risk":
            if check.get("has_high"):
                lines.append(f"  [{label}] FAIL - high risk changes")
            elif check.get("has_medium"):
                lines.append(f"  [{label}] WARN - medium risk changes")
            else:
                lines.append(f"  [{label}] PASS")
            if check.get("risks"):
                for risk in check["risks"]:
                    lines.append(f"    {risk['level']}: {risk['file']} - {risk['reason']}")

    lines.append("")
    lines.append("=" * 50)

    if passed:
        lines.append("  Result: COMMIT APPROVED")
        lines.append("  All checks passed.")
    else:
        lines.append("  Result: COMMIT BLOCKED")
        lines.append("  One or more checks failed. Fix the issues above and try again.")

    print("\n".join(lines))


def main():
    """Main entry point for the pre-commit hook."""
    passed, results = run_checks()
    print_review(results, passed)

    if passed:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
