# Implementation Status

Last updated: 2026-10-07

## Foundation
- [x] Product vision defined
- [x] MVP scope defined
- [x] Dashboard modules defined
- [x] Framework-agnostic architecture direction defined
- [x] Skill architecture direction defined
- [x] Repository foundation started
- [x] Skill architecture documented
- [x] Framework adapter contract documented
- [x] Dashboard specification documented
- [x] UI/UX principles documented
- [x] Security model documented
- [x] Agent rules documented
- [x] Architecture decisions documented
- [x] Changelog established
- [x] Contribution rules documented

## Phase 1 — Discovery Foundation
- [x] Initial implementation architecture documented
- [x] Python/FastAPI backend skeleton created
- [x] Canonical Framework DNA and Capability models created
- [x] Read-only local project discovery service implemented
- [x] Initial Python/pytest/Playwright/API detection implemented
- [x] Discovery REST endpoint implemented
- [x] Canonical adapter interface implemented
- [x] Adapter registry implemented
- [x] Reference pytest adapter implemented
- [x] Normalized discovered-test model implemented
- [x] Test discovery service implemented
- [x] Test discovery REST endpoint implemented
- [x] Unit/API tests added
- [x] Test Explorer contract documented
- [x] Explicit adapter capability reporting added
- [x] Reproducible backend CI workflow added
- [x] Framework-neutral execution request/result contracts defined
- [ ] CI workflow execution verified
- [ ] Discovery hardening/exclusion policy formally validated
- [x] React/TypeScript Test Explorer vertical slice implemented
- [x] Framework-native pytest execution integrated behind capability and explicit authorization checks
- [x] Execution/result API integration implemented
- [ ] Additional framework adapters implemented
- [ ] Evidence pipeline implemented
- [ ] Failure analysis implemented
- [ ] AI analysis implemented

## Current State

Phase 1 has a read-only discovery foundation, normalized test discovery, explicit adapter capabilities, a Test Explorer vertical slice, and a controlled pytest executor boundary. Execution is not yet exposed through the API because authorization and integration remain incomplete.

The reference pytest adapter remains discovery-only. A separate pytest executor now exists, but it requires explicit side-effect authorization and discovered-test mapping; API orchestration is still pending.

The Test Explorer contract defines the UI/backend boundary. The new React/TypeScript vertical slice consumes normalized tests and adapter capabilities through the backend API; it does not parse framework-specific source.

The dashboard remains discovery-first. The backend now exposes a controlled pytest execution endpoint; frontend execution controls remain intentionally gated until the execution UX and lifecycle model are implemented.

## Known Limitations

- Detection is heuristic and intentionally conservative.
- Dependency parsing is not yet package-manager aware.
- Filesystem exclusion behavior has initial safeguards but still requires formal validation.
- The pytest adapter needs richer support for markers, parametrization, fixtures, and other pytest metadata.
- Only one reference adapter is currently implemented.
- The current endpoint accepts a local filesystem path; secure remote repository connectors are not implemented yet.
- A first frontend/Test Explorer vertical slice is implemented; broader dashboard modules are not yet implemented.
- CI has been configured but its first run has not yet been verified.
- The pytest executor is exposed through a synchronous API boundary with explicit authorization; live/background execution, cancellation, remote execution, and artifact persistence remain unsupported.

## Next Step

1. Verify backend and frontend CI and resolve any failures.
2. Complete formal discovery exclusion validation.
3. Add execution controls to Test Explorer using reported capabilities and explicit confirmation.
4. Add run persistence/lifecycle APIs for live execution, cancellation, and history.
5. Harden pytest result matching, parametrization handling, environment policy, and evidence storage.
6. Add a second framework adapter only after the generic execution contracts remain stable.

## Tracking Rule

Update this file after every meaningful implementation milestone. Never mark functionality complete without validation.
