# Framework Adapter Contract

## Purpose

The Framework Adapter is the boundary between the framework-agnostic Command Center and a connected project's native automation framework.

> The dashboard adapts to the automation framework; the automation framework does not adapt to the dashboard.

## Responsibilities

An adapter may provide:

- project/framework discovery
- test discovery
- capability discovery
- command generation
- test execution
- execution status/result normalization
- evidence collection
- logs and artifacts
- framework-specific metadata

## Adapter Boundary

```
Command Center
     ↓
Canonical Command / Query
     ↓
Framework Adapter
     ↓
Existing Framework
     ↓
Native Runner / Utilities
```

The adapter must not require the customer's framework to be rewritten.

## Canonical Operations

The initial contract should support concepts such as:

- `discover_project`
- `discover_tests`
- `discover_capabilities`
- `validate_configuration`
- `build_execution_command`
- `start_execution`
- `get_execution_status`
- `collect_results`
- `collect_evidence`
- `cancel_execution` where safely supported

Not every framework must implement every operation. Unsupported capabilities must be reported explicitly.

## Framework Discovery

Discovery should identify, where possible:

- language
- package/dependency manager
- test runner
- UI automation technology
- API tooling
- database tooling
- project structure
- configuration
- tags/markers/groups
- reporting
- screenshots/video/tracing
- retry/parallel support
- CI integration
- existing utility layers
- custom commands

## Normalization

Framework-specific data is normalized into canonical models for the dashboard.

Example:

```
Pytest marker / TestNG group / Playwright project
                  ↓
             Canonical Tag
```

Normalization must preserve original framework metadata so users can trace dashboard behavior back to source.

## Execution Safety

Execution requests must be explicit and auditable.

The adapter must:

- validate requested options
- avoid shell injection
- constrain working directories
- avoid arbitrary command construction from untrusted values
- record the resolved command/configuration
- expose unsupported options instead of silently ignoring them

## Reference Strategy

The first production adapter should be selected based on actual repository/framework evidence. A reference implementation may use a Python test framework because it is practical for initial development, but the canonical contract must remain framework-neutral.

## Non-goals

- Replacing test runners.
- Rewriting project configuration.
- Imposing a universal POM or locator strategy.
- Hiding unsupported framework behavior.
