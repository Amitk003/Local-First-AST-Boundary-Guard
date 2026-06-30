# Architecture

## High Level Design

Code Guardian works like a gatekeeper between your code changes and git. When you run `git commit`, it checks your changes before allowing them.

### Flow

1. Developer runs `git commit`
2. Git pre-commit hook fires
3. Code Guardian agent runs these checks:
   - Intent check - did you change files you were not supposed to?
   - Test check - did you add tests for your changes?
   - Documentation check - did you update docs?
   - Risk analysis - are there dangerous changes?
4. A review packet is created with results
5. Commit is allowed or blocked

### Components

**Intent Manager**

Stores what task you are working on and which files you are allowed to change. Before coding, you declare your intent with a ticket number and list of allowed files.

**File Scanner**

Compares the files you changed against the allowed file list. If you changed a file outside the allowed list, it is flagged.

**Test Checker**

Looks at your changes to see if there are matching test files. If you added a function in `src/auth/login.py`, it checks for `tests/test_auth_login.py`.

**Documentation Checker**

Checks if documentation files were updated when you change public functions or APIs.

**Risk Analyzer**

Looks for dangerous changes like:
- Deleting production configuration files
- Removing authentication code
- Changing database migration files

**Review Packet Generator**

Creates a formatted output showing all the check results.

**Release Notes Generator**

Creates release notes from the commit messages and changes.

### Data Storage

Uses Lemma tables:

**IntentArtifacts table**

Stores ticket number, description, and list of allowed files.

**ReleaseChecklist table**

Stores release rules like whether tests or documentation are required.
