# Changelog

All notable project changes should be recorded here.

## Unreleased

### Added
- Framework-neutral discovery and execution contracts, adapter registry, and Test Explorer.
- Controlled local pytest execution with explicit opt-in authorization, timeout, and JUnit normalization.
- Deterministic failure-analysis API and UI with conservative unknown fallback and representative regression fixtures.
- SQLite execution history that persists normalized summaries rather than raw stdout/stderr or raw failure messages.
- Background execution lifecycle, status polling, cooperative cancellation, and bounded in-process workers.
- Opt-in local evidence artifact storage with generated IDs, execution-scoped reads, size/age/total-budget limits, SHA-256 integrity verification, and download API.
- Test Explorer links to evidence artifacts on historical run records.
- Regression coverage for artifact path escapes, symlinks, non-regular files, and restrictive directory/database permissions where supported.
- Documentation of cumulative integration state and local-only security boundaries.

### Security and limitations
- The cumulative stack is tracked in draft [PR #17](https://github.com/princekdavid/ai-automation-command-center/pull/17); no integration PR has been merged.
- The API has no authentication and must remain bound to localhost. CORS is not authentication.
- Running a test may execute arbitrary project code; the UI authorization checkbox is not a sandbox.
- Artifact retention is disabled by default. Evidence and history can contain sensitive data; history is unencrypted and has no retention policy.
- No remote execution, multi-user authorization, cloud artifact storage, AI analysis, self-healing, auto-merge, or deployment is implemented.
- Prior artifact read hardening passed backend [workflow #38170736828](https://github.com/princekdavid/ai-automation-command-center/actions/runs/38170736828) and frontend [workflow #38170736823](https://github.com/princekdavid/ai-automation-command-center/actions/runs/38170736823). Current database symlink/permission hardening is pending CI.
