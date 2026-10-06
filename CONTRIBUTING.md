# Contributing

## Before You Change Code

1. Read `PROJECT_VISION.md`.
2. Read `PRD.md`.
3. Read `ARCHITECTURE.md`.
4. Read `DEVELOPMENT_RULES.md`.
5. Check `IMPLEMENTATION_STATUS.md`.
6. Review relevant decisions in `DECISIONS.md`.

## Development Principles

- Keep the core framework-agnostic.
- Prefer adapters for framework-specific behavior.
- Reuse existing project utilities.
- Add tests for implementation changes.
- Do not mark work complete without validation.
- Update documentation when behavior or architecture changes.
- Update implementation status after meaningful milestones.
- Record material architectural changes in `DECISIONS.md`.

## Pull Requests

A PR should explain:

- problem
- approach
- affected components
- tests/validation
- security considerations
- documentation changes
- known limitations

## Definition of Done

A change is complete only when:

- implementation is complete
- relevant tests pass
- validation is documented
- security implications are considered
- required docs are updated
- implementation status is accurate

## Avoid

- framework-specific assumptions in core code
- duplicate utilities
- unnecessary abstraction
- unvalidated AI-generated behavior
- unrelated scope expansion
