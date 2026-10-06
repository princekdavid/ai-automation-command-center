# Implementation Architecture

## Initial Stack Decision

The first implementation uses:

- Backend: Python + FastAPI
- Domain/discovery engine: Python
- Frontend: React + TypeScript
- API contract: REST initially
- Test framework for Command Center itself: pytest
- Packaging: backend uses pyproject.toml
- Repository structure: monorepo

This is an implementation choice for the Command Center, not a restriction on connected customer frameworks.

## Monorepo

~~~text
apps/
  api/
  web/

packages/
  core/
  discovery/
  adapters/
  execution/
  skills/
  ai/

tests/
  unit/
  integration/
  fixtures/

docs/
scripts/
~~~

## First Vertical Slice

~~~text
Project Path
    ↓
Discovery Service
    ↓
Framework DNA
    ↓
Capability Map
    ↓
Canonical API response
    ↓
Dashboard-ready data
~~~

The first production slice is intentionally backend-first and read-only. It will not execute tests yet.

## Why Discovery First

Execution before discovery would force assumptions about runner, language, command syntax, configuration, test layout, environment, and reporting.

Discovery creates the contract needed for the adapter and dashboard.

## Canonical Boundary

The core domain must not import Playwright, Selenium, Cypress, pytest, TestNG, or other customer-framework libraries.

Framework-specific detection belongs in discovery/adapters.

## Technology Decision Rule

Changing the initial stack requires an entry in DECISIONS.md explaining evidence, trade-offs, and migration impact.
