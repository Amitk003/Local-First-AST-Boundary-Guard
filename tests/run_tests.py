"""Test runner for all Code Guardian modules.

Run with:
    python tests/run_tests.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def run_test_module(name, module_path):
    """Import and run all tests from a test module."""
    try:
        import importlib.util
        import importlib.machinery

        loader = importlib.machinery.SourceFileLoader(name, module_path)
        spec = importlib.util.spec_from_loader(name, loader)
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)

        if hasattr(module, "run"):
            p, f = module.run()
            return p, f
        else:
            return 0, 1
    except Exception as e:
        print(f"  ERROR loading {name}: {e}")
        return 0, 1


def main():
    """Run all test modules."""
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    test_modules = [
        ("file_scanner", os.path.join(tests_dir, "test_file_scanner.py")),
        ("checkers", os.path.join(tests_dir, "test_checkers.py")),
        ("risk_analyzer", os.path.join(tests_dir, "test_risk_analyzer.py")),
        ("review_packet", os.path.join(tests_dir, "test_review_packet.py")),
        ("release_notes", os.path.join(tests_dir, "test_release_notes.py")),
    ]

    print("=" * 55)
    print("  Code Guardian Test Runner")
    print("=" * 55)
    print()

    total_passed = 0
    total_failed = 0

    for name, path in test_modules:
        print(f"[{name}]")
        p, f = run_test_module(name, path)
        total_passed += p
        total_failed += f
        print()
        print(f"  result: {p} passed, {f} failed")
        print()

    print("=" * 55)
    print(f"  Total: {total_passed} passed, {total_failed} failed")

    if total_failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
