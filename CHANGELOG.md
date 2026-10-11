# Changelog

All notable project changes should be recorded here.

## Unreleased

### Added
- Framework-neutral execution request/result contracts and normalized per-test outcomes
- Controlled local pytest executor with explicit authorization, timeout, and JUnit normalization
- Execution API and authorization/capability checks
- React/TypeScript Test Explorer with project discovery, normalized test details, and adapter capability visibility
- Explicit authorization checkbox and single-test execution controls with normalized result display
- Regression tests for pytest collection semantics, generated-directory exclusions, symlink boundaries, and JUnit class-method result mapping
- Backend and frontend CI workflow definitions
- Local frontend CORS support with an explicit origin allowlist
- README instructions for local setup, validation, and execution safety
- Deterministic failure-analysis API with transparent keyword rules and UI category display
- Local SQLite execution history with bounded list/detail endpoints and recent-runs UI
- Bounded in-process background execution with accepted/running/terminal status, status polling, and cooperative pytest cancellation
- Opt-in local evidence artifact storage with generated IDs, SHA-256 checks, per-artifact and total-storage limits, retention cleanup, best-effort JUnit report retention, execution-scoped metadata/download endpoints, and regression tests; backend CI passed on exact source head `5d696b39bce1142e3e8e528df8e3f074aef4c50b` (workflow run #69)

### Security and limitations
- Execution is local and is not an OS-level sandbox; running a test may execute arbitrary project code.
- Explicit authorization is required before executing trusted local projects.
- No repository mutation, package installation, deployment, remote execution, retries, or self-healing is implemented.
- Background execution is process-local, not a durable queue.
- Local history stores normalized summaries only; the database is unencrypted and has no retention policy.
- Artifact persistence is disabled by default. When enabled, JUnit report retention is best-effort and does not change test outcomes; API metadata/download access is scoped by execution ID. Backend CI passed on exact source head `5d696b39bce1142e3e8e528df8e3f074aef4c50b` (workflow run #69). The Test Explorer does not yet show artifact links.
- Historical backend/frontend workflow links and exact commits are recorded in `IMPLEMENTATION_STATUS.md`; no CI pass is claimed for the newly added artifact module yet.

## Previous Foundation
- Product vision and non-goals
- Product requirements document
- High-level architecture
- Implementation status tracking
- Development rules and product roadmap
- Skill architecture specification
- Framework adapter contract and dashboard specification
- UI/UX principles and security model
- Agent rules and architecture decision record
