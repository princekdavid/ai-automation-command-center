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

### Security and limitations
- Execution is local and synchronous; it is not an OS-level sandbox.
- Running a test may execute arbitrary project code; explicit authorization is required.
- No repository mutation, package installation, deployment, remote execution, retries, or self-healing is implemented.
- Background lifecycle/cancellation and persistent evidence artifact storage remain pending. Local history stores normalized summaries only; the database is unencrypted and has no retention policy. Deterministic failure categorization is implemented but requires broader fixture validation.
- Backend tests and frontend build passed on code commit `8a8bcf2a91aa014fa655ed576ed2368b6ea7d9aa`; see the Implementation Status for the exact workflow links.

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
