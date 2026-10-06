# Architecture Decisions

This file records decisions that materially affect product architecture. New implementation choices that contradict these decisions must add or update a decision rather than silently changing direction.

## ADR-001: Dashboard is the primary product

**Decision:** The Command Center is an interactive dashboard/control plane around an existing automation framework.

**Reason:** Users need visibility, execution control, debugging, framework understanding, and observability; AI is an intelligence layer rather than the entire product.

## ADR-002: Framework-agnostic architecture

**Decision:** The core system must not depend on a single automation framework.

**Reason:** Enterprise QA environments commonly use Selenium, Playwright, Cypress, Pytest, TestNG, and custom frameworks.

## ADR-003: Adapter boundary

**Decision:** Framework-specific behavior is isolated behind adapters.

**Reason:** This prevents the dashboard and AI layers from becoming coupled to runner-specific commands.

## ADR-004: Discover before generating

**Decision:** The system discovers project architecture, utilities, and conventions before generating project-specific skills or automation.

**Reason:** Generated abstractions should complement, not compete with, existing framework design.

## ADR-005: Read-only repository access by default

**Decision:** Discovery starts with minimum read permissions.

**Reason:** Understanding a framework should not require write or destructive access.

## ADR-006: Validate AI-generated behavior

**Decision:** AI-generated code, skills, and recommendations are not considered trusted until validated.

**Reason:** AI can produce syntactically valid but functionally incorrect or unsafe behavior.

## ADR-007: Control autonomy

**Decision:** Side-effecting and destructive operations require explicit authorization according to policy.

**Reason:** The system operates against real repositories and test environments.

## ADR-008: Build control plane before autonomy

**Decision:** MVP prioritizes discovery, execution, observability, evidence, and failure analysis before advanced autonomous behavior.

**Reason:** Reliable control and visibility are prerequisites for safe automation intelligence.
