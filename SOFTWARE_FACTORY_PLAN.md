# Software Factory Pipeline — Implementation Plan

**Status:** Proposed  
**Owner:** Project maintainer  
**Last updated:** 2026-10-11  
**Related:** `PRD.md`, `ARCHITECTURE.md`, `AGENT_RULES.md`, `DEVELOPMENT_RULES.md`, `SECURITY.md`, `IMPLEMENTATION_STATUS.md`

## 1. Purpose

Define a small, auditable path from a well-scoped engineering task to a validated draft pull request. The goal is to borrow the useful software-factory pattern—persistent context, bounded work, deterministic checks, and explicit handoffs—without requiring paid hosted coding agents or starting with a complex multi-agent orchestrator.

This document describes intended behavior. It does not claim that the pipeline is implemented.

## 2. Non-negotiable guardrails

1. Agents must not push directly to `main`, force-push, or merge pull requests.
2. All generated code changes must be proposed on a task-specific branch and reviewed in a pull request.
3. CI results are evidence, not proof of correctness. A human remains responsible for reviewing the diff and approving the merge.
4. No model/API provider or paid service is mandatory for the deterministic pipeline.
5. Secrets must never be written to logs, task artifacts, prompts, or committed files.
6. Treat issue descriptions, repository files, test fixtures, command output, and generated content as untrusted input.
7. Run only allow-listed validation commands in an isolated environment. Do not execute arbitrary commands copied from issues or generated plans.
8. Start with one task at a time. Parallel agents and automatic retries are later optimizations, not MVP requirements.
9. Record what was requested, what changed, what checks ran, their outcomes, and any human decision.
10. If permissions, requirements, or validation results are ambiguous, stop and request human input.

## 3. Proposed task lifecycle

`BACKLOG → READY → PLANNED → IMPLEMENTING → VALIDATING → DRAFT_PR → HUMAN_REVIEW → MERGED`

Terminal or pause states: `BLOCKED`, `FAILED_VALIDATION`, `CANCELLED`.

- **BACKLOG:** A task exists but is not ready for automation.
- **READY:** The task has a clear goal, bounded scope, acceptance criteria, and risk classification.
- **PLANNED:** A plan lists expected files, implementation steps, tests, and risks. Human approval is required for high-risk tasks.
- **IMPLEMENTING:** A task-specific branch is used. Changes remain within the approved scope.
- **VALIDATING:** Deterministic checks run first; AI review, if enabled, is advisory and cannot override a failing required check.
- **DRAFT_PR:** A draft PR is created with a summary, scope, test evidence, limitations, and checklist.
- **HUMAN_REVIEW:** A person reviews the diff and CI results and decides whether to request changes or merge.
- **BLOCKED / FAILED_VALIDATION:** Preserve diagnostics, avoid creating a misleading success state, and report the next action.
- **MERGED:** Set only after GitHub confirms the merge; never infer it from a green check or a successful PR-creation call.

Every transition must be explicit and logged. Retries must be bounded and must not bypass failed checks.

## 4. Minimum task contract

Each automated task should provide:

- Unique task/issue reference
- User-visible goal and motivation
- In-scope and out-of-scope changes
- Testable acceptance criteria
- Allowed paths or components, where practical
- Risk level: low, medium, or high
- Required validation commands
- Required human approvals
- Current status, timestamps, branch, PR URL, and outcome

Reject or return tasks to BACKLOG when the goal is vague, scope is unbounded, acceptance criteria are not testable, or the request conflicts with repository policy.

## 5. Agent responsibilities

Keep responsibilities logically separate even if the first version uses a single model or a human for some stages.

- **Planner:** Reads the project rules and produces a bounded plan; cannot modify files.
- **Implementer:** Makes only approved changes on the task branch.
- **Validator:** Runs deterministic checks and reports raw results plus a concise summary; cannot waive failures.
- **Reviewer:** Checks the diff against requirements, regressions, security, maintainability, and test quality. AI feedback is advisory.
- **Orchestrator:** Tracks lifecycle and permissions, enforces time/retry limits, and records transitions.

Do not introduce separate deployed agents until the single-task pipeline is reliable and the separation provides a measurable benefit.

## 6. Validation and pull-request policy

Required checks should be selected from the actual project stack and must be documented before being enforced. At minimum, the pipeline should eventually support:

1. Formatting/lint checks where configured.
2. Unit tests.
3. API/contract tests where applicable.
4. Frontend build or type checks where applicable.
5. Dependency/security checks using supported tools.
6. Diff-scope and secret-scanning checks.

The PR body should include: task reference, summary, files/components changed, acceptance criteria mapping, exact checks run and their results, known limitations, and a rollback note when appropriate.

A failed or skipped required check must be visible. Do not report checks as passed if they were not run.

## 7. Security and permissions

- Prefer GitHub Actions' minimum required token permissions; use read-only permissions by default.
- Grant write permissions only to the narrowly scoped job that needs to create a branch or draft PR.
- Do not expose write-capable credentials to untrusted pull-request code.
- Do not run untrusted PR code in privileged workflows or workflows receiving repository secrets.
- Pin third-party actions to reviewed immutable commit SHAs when introducing them.
- Apply job timeouts, concurrency limits, and bounded retries.
- Avoid uploading full stdout/stderr, environment variables, tokens, or sensitive test data as artifacts.
- Keep local execution history and evidence access-controlled; define retention before storing larger artifacts.
- Never enable automatic merge or production deployment as part of the initial pipeline.

## 8. Cost policy

1. Deterministic scripts and existing CI checks come first.
2. AI use is optional and should be behind a provider-neutral interface.
3. Set configurable limits for tokens, retries, runtime, and tasks per run.
4. Avoid repeated model calls when repository state and validation evidence have not changed.
5. Report when AI is disabled, unavailable, rate-limited, or over budget; do not silently switch to a paid provider.
6. The baseline workflow must remain useful with AI disabled.

## 9. Incremental delivery

### Stage A — Task readiness and repository memory
- Keep product rules, decisions, current state, and next steps in versioned Markdown.
- Define a task template with acceptance criteria and risk classification.
- Add a lightweight checklist for readiness and completion.

### Stage B — Deterministic CI baseline
- Inspect the actual application branch and identify the existing backend/frontend test and build commands.
- Add or improve CI using those verified commands; do not invent project commands.
- Verify the workflow on a non-production branch and document limitations.

### Stage C — Draft PR workflow
- Create task branches and draft PRs only after successful required checks.
- Ensure the workflow has minimum permissions and cannot merge.
- Persist task status and validation evidence without storing secrets or unnecessary raw logs.

### Stage D — Optional AI assistance
- Add planning/review behind an optional provider interface.
- Keep model output untrusted; validate it against schemas and policy.
- Measure usefulness, failure rate, latency, and cost before enabling more autonomy.

### Stage E — Controlled scale
- Consider concurrency, specialized agents, and bounded recovery only after the single-task path is stable.
- Add explicit cancellation, idempotency, queue recovery, and auditability before running multiple tasks unattended.

## 10. Definition of done for the first pipeline milestone

- [ ] A task can be marked READY only when required fields are present.
- [ ] The pipeline reads repository governance documents before planning.
- [ ] A task runs on a dedicated branch and cannot write directly to `main`.
- [ ] Required checks use verified project commands and report truthful results.
- [ ] A successful run can open a draft PR with a reproducible evidence summary.
- [ ] Failed validation blocks draft-PR creation or clearly marks the PR as blocked.
- [ ] Secrets are excluded from logs and artifacts.
- [ ] No automatic merge, production deployment, or mandatory paid model provider exists.
- [ ] A human can cancel the task and review its complete status history.

## 11. Immediate next action

Before implementing automation, inspect the current application branches and open pull requests, identify the canonical base branch and dependency order, then confirm the actual backend and frontend commands. The current default branch is documentation-focused, while application work may be in stacked PRs; do not build CI against an assumed directory layout or merge order.
