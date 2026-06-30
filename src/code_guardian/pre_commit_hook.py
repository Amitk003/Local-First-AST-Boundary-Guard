import sys


def main():
    """Main entry point for the pre-commit hook."""
    try:
        from code_guardian.review_packet import review_packet_main
    except ImportError:
        print("Error: code_guardian package not found.")
        print("Make sure PYTHONPATH includes the src directory.")
        sys.exit(1)

    review_packet_main()


if __name__ == "__main__":
    main()
