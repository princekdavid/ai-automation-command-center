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
- Artifact retention is disabled by default. Evidence and history can contain sensitive data; history is unencrypted but is now bounded by age and record count (configurable).
- No remote execution, multi-user authorization, cloud artifact storage, AI analysis, self-healing, auto-merge, or deployment is implemented.
- Database symlink/permission hardening passed backend [workflow #38171267669](https://github.com/princekdavid/ai-automation-command-center/actions/runs/38171267669) and frontend [workflow #38171267630](https://github.com/princekdavid/ai-automation-command-center/actions/runs/38171267630) on code/test head `4385760f5096c4e9292b0b38710370e98a179d0f`. Concurrent cleanup and history retention validation is pending on head `30054013f0fd373782662d715567e504ff203030`.
