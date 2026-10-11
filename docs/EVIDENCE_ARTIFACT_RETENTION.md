# Evidence Artifact Storage and Retention (MVP)

Status: proposed implementation contract
Branch: `feat/evidence-artifact-retention`
Scope: local, single-user MVP only. This document does not claim the feature is implemented.

## Goal

Let a developer inspect evidence from a completed test run without making the execution-history database store raw logs or unbounded test output. Keep summaries in SQLite; keep optional evidence files in a separate local artifact directory with explicit size and retention limits.

## In scope

- Persist a bounded, normalized evidence bundle for a completed execution.
- Associate artifacts with the execution request ID and expose metadata through the API.
- Support listing metadata and retrieving an artifact only for a known execution.
- Apply retention cleanup deterministically.
- Document the local filesystem trust boundary and configuration.

## Out of scope

- Cloud/object storage, multi-user access, remote repository connectors, encryption/key management, automatic uploads, AI processing of artifacts, and long-term audit/compliance guarantees.
- Treating local test execution as a sandbox. Tests may execute arbitrary code and can produce sensitive output.

## Contract

### Storage separation

- Keep normalized run summaries and artifact metadata in the existing SQLite history store.
- Store artifact bytes under a dedicated configurable root (default: `~/.ai-automation-command-center/artifacts`).
- Do not store raw stdout/stderr or raw failure messages in the history database.
- Artifact metadata should include: artifact ID, execution request ID, kind, relative storage key, byte size, SHA-256 digest, creation time, and media type.
- Never use a caller-provided filename as a filesystem path. Generate storage keys server-side.

### Default data minimization

- Artifact persistence is disabled unless explicitly enabled by configuration.
- When enabled, persist only the normalized JUnit result bundle and a bounded diagnostic log excerpt; do not collect environment variables, process environment dumps, credentials, cookies, or full request/response bodies.
- Apply byte limits before writing and reject or truncate oversized inputs according to one documented deterministic policy.
- Do not expose absolute host paths in API responses. Return opaque artifact IDs and relative metadata only.
- Treat all artifacts as potentially sensitive because test output can contain secrets or customer data.

### Filesystem safety

- Resolve the configured root once and verify each target remains beneath it.
- Use generated names and atomic file replacement; do not follow symlinks into locations outside the root.
- Handle missing, unreadable, corrupt, or already-deleted artifacts without crashing the history API.
- Never accept arbitrary paths from API callers for read/delete operations.
- Use restrictive file permissions where supported; document platform differences.

### Retention

- Configuration must support a maximum age and a maximum total artifact-storage budget.
- Cleanup runs at startup and opportunistically after terminal execution, with bounded work per pass.
- Delete oldest artifacts first until both limits are satisfied; keep the history row but mark artifact metadata as expired/deleted.
- Cleanup must be idempotent and safe to rerun.
- If metadata and bytes disagree, reconcile without deleting files outside the artifact root.
- Defaults should be conservative and documented; allow disabling artifact retention without disabling normalized history.

### API behavior

- Artifact listing returns metadata only and is bounded/paginated.
- Artifact download uses an opaque artifact ID scoped to a known execution and sets a safe content type and attachment disposition.
- Missing, expired, or unknown artifacts return a consistent not-found response without leaking filesystem details.
- Artifact storage failure must not turn a completed test run into a false test failure. Surface a separate evidence-persistence warning in the execution summary.

## Required tests

- Save/read a valid artifact and verify digest and byte count.
- Disabled-by-default behavior.
- Reject path traversal and prove generated paths remain inside the root.
- Symlink and root-boundary cases where supported by the platform.
- Enforce per-artifact size and total storage budget.
- Age-based expiry and oldest-first budget cleanup.
- Idempotent cleanup, missing file, corrupt metadata, and partial-write recovery.
- API authorization/scope, pagination bounds, and non-leaking not-found responses.
- Evidence persistence failure does not overwrite the actual test outcome.
- Confirm raw logs/messages are absent from SQLite history records.

## Definition of done

- Implementation and tests are committed on this feature branch.
- Backend tests pass on the exact proposed head; frontend build passes if API/UI changes are included.
- Configuration and operational limitations are documented.
- `IMPLEMENTATION_STATUS.md` and `CHANGELOG.md` distinguish implemented behavior from planned work.
- A draft PR is opened; no direct push to `main`, no auto-merge, and no paid AI service.
