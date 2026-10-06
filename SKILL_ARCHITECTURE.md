# Skill Architecture

## Purpose

The Skill System exposes project-aware automation capabilities to agents and the dashboard without replacing the connected automation framework.

## Core Model

```
Capability
    ↓
Skill
    ↓
Implementation
    ↓
Framework Adapter
```

A capability is an abstract action or ability. A skill is the reusable contract that fulfills it. The implementation uses the project's existing utilities and conventions. The adapter translates the skill into framework-native behavior where required.

## Principles

1. Discover existing project behavior before creating new implementations.
2. Prefer reuse over duplication.
3. Skills must be framework-aware but dashboard-facing contracts remain framework-neutral.
4. Skills must declare inputs, outputs, prerequisites, side effects, validation status, and version.
5. AI-generated skills require validation before activation.
6. A skill must not silently perform destructive actions.
7. Skill selection must be deterministic enough to audit.

## Skill Lifecycle

```
Discovered
  ↓
Defined
  ↓
Implemented
  ↓
Validated
  ↓
Approved
  ↓
Active
  ↓
Monitored
  ↓
Deprecated / Revalidated
```

## Skill States

- Available
- Available with configuration
- Missing
- Invalid
- Deprecated

## Skill Gap Analysis

The system compares required capabilities against discovered and active skills:

```
Required Capabilities
        ↓
Available Skills
        ↓
Gap Analysis
        ↓
Covered / Missing / Needs Configuration
```

Missing skills are recommendations first. Creation requires codebase understanding and validation.

## Skill Metadata

Each skill should be able to expose:

- stable skill ID
- name and description
- capability
- version
- supported framework/technology
- required inputs
- outputs
- prerequisites
- implementation reference
- confidence
- validation status
- permissions
- side effects
- owner/source
- last validated timestamp

## Validation

Validation should include, as applicable:

- schema/input validation
- static validation
- unit tests
- framework-level validation
- runtime validation
- security/permission validation
- regression impact

## Example

Capability: `CLICK_ELEMENT`

A Playwright project may already contain a custom page utility. The skill should call or adapt that utility rather than introducing an independent locator abstraction.

The dashboard and agents request `CLICK_ELEMENT`; the resolver chooses the appropriate project implementation.

## Non-goals

- A universal replacement for every framework utility.
- Autonomous skill activation without validation.
- Creating duplicate abstractions when equivalent project behavior exists.
