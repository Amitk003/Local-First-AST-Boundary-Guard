# Code Guardian

Code Guardian is an AI assistant that checks your code before a git commit happens. It acts like a reviewer and security guard for your code changes.

## The Problem

When developers work in teams, they often:

- Change files they should not touch
- Forget to write tests
- Forget to update documentation
- Introduce bugs
- Create messy pull requests

These problems are usually found after pushing code to GitHub, which wastes time.

## The Solution

Code Guardian checks your code before the commit happens. It looks at what you changed and verifies:

1. Are the changes in allowed files?
2. Are tests included?
3. Is documentation updated?
4. Are there any risky changes?

If something is wrong, the commit is blocked. If everything is correct, the commit succeeds.

## How It Works

1. You declare what task you are working on and which files you want to change
2. When you run `git commit`, Code Guardian runs automatically
3. It checks your changes against the rules
4. It creates a review packet showing what passed and what failed
5. It blocks or allows the commit

## Quick Start

### Prerequisites

- Python 3.11 or higher
- Git
- Lemma SDK (installed via uv)

### Setup

1. Install the package:

```bash
pip install -r requirements.txt
```

2. Start the Lemma daemon:

```bash
lemma daemon start --background
```

3. Create the Lemma pod:

```bash
lemma pod create code-guardian --with-starter
```

4. Install the pre-commit hook:

```bash
pre-commit install
```

### Usage

1. Declare your intent before coding:

```bash
python -m code_guardian.intent_manager declare --ticket AUTH-101 --allowed-files "src/auth/*"
```

2. Make your code changes

3. Try to commit:

```bash
git commit -m "Added Google OAuth login"
```

Code Guardian will:

- Check if you changed files outside the allowed scope
- Verify tests exist
- Check documentation updates
- Analyze risks
- Generate release notes

4. If everything is good, the commit succeeds. If not, you get a review packet with details on what went wrong.

## Project Structure

```
code-guardian/
  src/
    code_guardian/       - Main code
  tests/                 - Test files
  docs/                  - Documentation
```

## Tech Stack

- Python for the backend logic
- Lemma SDK for pod, tables, and agent infrastructure
- pre-commit framework for git hook integration
- tree-sitter for code analysis
