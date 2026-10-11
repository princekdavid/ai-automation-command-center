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
- Background lifecycle/cancellation and persistent evidence artifact storage remain pending. Local history stores normalized summaries only; the database is unencrypted and has no retention policy. Failure categorization remains heuristic; representative Playwright timeout/locator, pytest fixture, HTTP authorization, network reset, and assertion fixtures are covered by regression tests.
- Failure-analysis CI passed on commit `1aaa61d0e4077a2438ae0dcd71801449ade67a33` (backend workflow #99; frontend workflow #68). The combined execution-history integration branch still requires its own validation.

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

- The cumulative integration candidate still requires fresh backend and frontend CI validation after reconciliation with the latest failure-analysis branch.
