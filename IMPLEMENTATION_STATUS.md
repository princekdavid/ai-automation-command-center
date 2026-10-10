# Implementation Status

Last updated: 2026-10-11

## Foundation
- [x] Product vision and MVP scope documented
- [x] Dashboard modules, framework-agnostic architecture, and skill architecture documented
- [x] UI/UX principles, security model, agent rules, architecture decisions, changelog, and contribution rules documented

## Phase 1 — Discovery and Test Explorer
- [x] Python/FastAPI backend skeleton and canonical Framework DNA/Capability models
- [x] Read-only local project discovery and discovery REST endpoint
- [x] Canonical adapter interface, registry, and reference pytest adapter
- [x] Normalized discovered-test model and test discovery REST endpoint
- [x] Adapter capability reporting and backend CI workflow
- [x] React/TypeScript Test Explorer vertical slice
- [x] Framework-neutral execution request/result contracts
- [x] Controlled local pytest executor with explicit authorization, timeout, and JUnit normalization
- [x] Execution API integration and authorization/capability checks
- [x] Regression coverage for pytest collection semantics and normalized failure details
- [ ] Latest backend/frontend CI verified after the 2026-10-11 commits
- [ ] Discovery exclusions and filesystem boundary policy fully validated
- [ ] Execution controls, background lifecycle, cancellation, and run history
- [ ] Persistent evidence pipeline
- [ ] Deterministic failure analysis
- [ ] Additional framework adapters
- [ ] AI analysis

## Current State

The repository contains an initial discovery-to-Test-Explorer vertical slice and a controlled, synchronous pytest execution API. Execution requires explicit authorization; test IDs must resolve to tests discovered for the project, and the adapter must report execution support. The UI is currently discovery-focused and does not yet expose run controls or a live execution lifecycle.

Recent fixes on the open feature branches:
- Pytest AST discovery now targets module-level `test_*` functions and `test_*` methods inside `Test*` classes, avoiding nested helper false positives and duplicate method records.
- Discovery skips common generated/virtual-environment folders and rejects resolved test roots/files that escape the selected project directory.
- JUnit failure normalization now preserves a failure message supplied as an XML attribute when the element has no text body.

## Known Limitations

- Framework detection remains heuristic; dependency metadata is not yet parsed comprehensively by each package manager.
- Pytest markers, parametrization, fixtures, dynamic collection, and all pytest edge cases are not yet normalized.
- Discovery exclusions have initial safeguards but require more comprehensive tests, especially for symlinks and large monorepos.
- Only pytest is implemented as a reference adapter.
- The API accepts a local filesystem path; secure remote repository connectors are not implemented.
- Execution is synchronous and local. Background jobs, cancellation, persistent run history, artifact storage, and remote execution are unsupported.
- CI passed on earlier PR #6 commit `9fd283c94b64df74edbfd781b30b9ebef732d590`; new commits from 2026-10-11 still require fresh backend/frontend validation. Do not treat earlier checks as validation of the latest head.

## Next Steps

1. Obtain fresh backend and frontend CI results for the latest commits.
2. Complete discovery exclusion and symlink-boundary regression coverage.
3. Add capability-gated execution controls with explicit confirmation in Test Explorer.
4. Introduce a run lifecycle/persistence model before attempting background execution or cancellation.
5. Add durable evidence references and deterministic failure categories.
6. Add another framework adapter only after the normalized discovery/execution contracts are stable.

## Tracking Rule

Update this file after every meaningful implementation milestone. Never mark functionality complete without validation.
