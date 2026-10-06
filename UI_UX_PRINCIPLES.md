# UI / UX Principles

## Product Mental Model

AI Automation Command Center should feel like:

> IDE + Control Center for QA automation.

It is not a generic analytics dashboard and not primarily a chatbot.

## Principles

### 1. Framework-aware by default

The interface is generated/adapted from discovered project capabilities.

### 2. Evidence before intelligence

Show source data, execution results, logs, and artifacts before AI conclusions.

### 3. Actionable over decorative

Every important visualization should help the user inspect, filter, compare, execute, troubleshoot, or decide.

### 4. Progressive disclosure

Do not expose enterprise complexity until it is relevant. Basic users see simple controls; advanced capabilities appear when supported.

### 5. Explainability

AI output should show:

- conclusion
- evidence
- confidence
- assumptions
- recommended next action

### 6. Safe actions

Actions with side effects require clear confirmation and permission boundaries.

### 7. Traceability

Users should be able to move from:

```
Dashboard
 → Test
 → Execution
 → Failure
 → Evidence
 → Source code
```

### 8. Consistent state

Execution state, skill state, framework state, and AI analysis state must be distinguishable.

### 9. Accessible enterprise UI

Support keyboard navigation, readable contrast, meaningful status indicators, responsive layouts, and non-color-only status communication.

### 10. Avoid AI theater

Do not add AI UI where deterministic information or normal framework controls are better.

## Core Interaction Patterns

- search-first exploration
- filters with clear active-state indicators
- drill-down from summary to evidence
- persistent execution context
- explicit action confirmation
- clear loading/running/succeeded/failed states
- empty states explaining how to proceed

## Design System Direction

The implementation should establish reusable tokens and components before building many screens. Exact visual styling should be decided during implementation and documented as a design decision.
