import json
import os
import subprocess
import sys
import tempfile
import uuid


LEMMA_POD = "code-guardian"
TABLE_NAME = "intentartifacts"


def _run_lemma(args, input_data=None):
    """Run a lemma CLI command and return parsed JSON output."""
    cmd = ["lemma"] + args + ["--output", "json"]
    if input_data is not None:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(input_data, f)
            temp_path = f.name
        cmd.extend(["--file", temp_path])
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True
            )
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Lemma command failed: {e.stderr}")
        finally:
            os.unlink(temp_path)
    else:
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True
            )
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Lemma command failed: {e.stderr}")


def _list_records():
    """List all records from the intentartifacts table."""
    result = _run_lemma(["record", "list", TABLE_NAME, "--limit", "100"])
    if isinstance(result, dict) and "items" in result:
        return result["items"]
    if isinstance(result, list):
        return result
    return []


def _find_by_issue_id(issue_id):
    """Find a record by issue_id. Returns None if not found."""
    records = _list_records()
    for r in records:
        if r.get("issue_id") == issue_id:
            return r
    return None


def declare_intent(issue_id, description, allowed_files):
    """Declare a new intent artifact.

    Args:
        issue_id: The ticket or issue number (e.g. AUTH-101)
        description: What the task is about
        allowed_files: List of file glob patterns (e.g. ["src/auth/*"])

    Returns:
        The created record as a dict
    """
    existing = _find_by_issue_id(issue_id)
    if existing:
        raise ValueError(
            f"Intent for issue '{issue_id}' already exists "
            f"(id: {existing['id']}). Use update_intent() to modify it."
        )

    payload = {
        "issue_id": issue_id,
        "description": description,
        "allowed_files": json.dumps(allowed_files),
        "status": "active",
    }
    return _run_lemma(["record", "create", TABLE_NAME], payload)


def get_intent(identifier):
    """Get an intent by id (UUID) or issue_id (string).

    Args:
        identifier: UUID string or issue_id string

    Returns:
        The record as a dict, or None if not found
    """
    try:
        uuid.UUID(identifier)
        return _run_lemma(["record", "get", TABLE_NAME, identifier])
    except (ValueError, RuntimeError):
        return _find_by_issue_id(identifier)


def update_intent(identifier, updates):
    """Update fields on an existing intent.

    Args:
        identifier: UUID or issue_id to identify the record
        updates: Dict of fields to update

    Returns:
        The updated record as a dict
    """
    record = get_intent(identifier)
    if record is None:
        raise ValueError(f"Intent not found: {identifier}")

    return _run_lemma(
        ["record", "update", TABLE_NAME, record["id"]], updates
    )


def list_active_intents():
    """List all active intents.

    Returns:
        List of record dicts with status 'active'
    """
    records = _list_records()
    return [r for r in records if r.get("status") == "active"]


def complete_intent(identifier):
    """Mark an intent as completed.

    Args:
        identifier: UUID or issue_id

    Returns:
        The updated record as a dict
    """
    return update_intent(identifier, {"status": "completed"})


def get_allowed_files(identifier):
    """Get the allowed file patterns for an intent.

    Args:
        identifier: UUID or issue_id

    Returns:
        List of allowed file glob patterns, or empty list
    """
    record = get_intent(identifier)
    if record is None:
        return []

    raw = record.get("allowed_files", "[]")
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return []
    if isinstance(raw, list):
        return raw
    return []


def main():
    """CLI entry point for intent management."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python -m code_guardian.intent_manager declare --ticket <id> --desc <text> --files <glob1,glob2>")
        print("  python -m code_guardian.intent_manager get <id>")
        print("  python -m code_guardian.intent_manager list")
        print("  python -m code_guardian.intent_manager complete <id>")
        return

    command = sys.argv[1]

    if command == "declare":
        ticket = None
        desc = ""
        files = []
        for i, arg in enumerate(sys.argv[2:], start=2):
            if arg == "--ticket" and i + 1 < len(sys.argv):
                ticket = sys.argv[i + 1]
            elif arg == "--desc" and i + 1 < len(sys.argv):
                desc = sys.argv[i + 1]
            elif arg == "--files" and i + 1 < len(sys.argv):
                files = sys.argv[i + 1].split(",")
        if not ticket or not files:
            print("Error: --ticket and --files are required")
            sys.exit(1)
        result = declare_intent(ticket, desc, files)
        print(f"Intent declared: {result['id']}")
        print(f"  Issue: {result['issue_id']}")
        print(f"  Allowed files: {result['allowed_files']}")

    elif command == "get":
        if len(sys.argv) < 3:
            print("Error: provide intent id or issue_id")
            sys.exit(1)
        result = get_intent(sys.argv[2])
        if result is None:
            print(f"Not found: {sys.argv[2]}")
        else:
            print(json.dumps(result, indent=2))

    elif command == "list":
        intents = list_active_intents()
        if not intents:
            print("No active intents")
        else:
            for intent in intents:
                print(f"  {intent['issue_id']:20s} | {intent.get('status'):10s} | {intent.get('id')}")

    elif command == "complete":
        if len(sys.argv) < 3:
            print("Error: provide intent id or issue_id")
            sys.exit(1)
        result = complete_intent(sys.argv[2])
        print(f"Completed: {result['issue_id']}")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
