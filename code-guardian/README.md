# code-guardian pod

Code Guardian pod for pre-commit AI checks. Contains IntentArtifacts and ReleaseChecklist tables.

## Tables

**IntentArtifacts** - Stores what task a developer is working on and which files they are allowed to change.

**ReleaseChecklist** - Stores release rules: whether tests and docs are required, and whether they passed.

## Build loop
```bash
lemma pods import ./code-guardian --dry-run   # validate
lemma pods import ./code-guardian             # upsert by resource name
```

## Verify
```bash
lemma pods describe
lemma agents chat hello "what can you do in this pod?"
```
