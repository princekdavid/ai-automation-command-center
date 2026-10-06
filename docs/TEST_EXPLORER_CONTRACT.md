# Test Explorer Contract

## Purpose

The Test Explorer is a dashboard view over normalized tests discovered from an existing automation framework.

## Rules

- The dashboard consumes the normalized test model; it does not parse framework-specific source code.
- Framework adapters own framework-specific discovery.
- A discovered test must retain a stable identifier and source reference.
- Discovery is read-only.
- Unsupported framework capabilities must be explicit.
- Execution is a separate concern and is not implied by discovery.

## Normalized test fields

- id
- name
- source_path
- framework
- runner
- suite
- tags
- metadata

## Planned UI

The first Test Explorer slice will provide:

1. Project/framework context.
2. Search.
3. Suite/test hierarchy.
4. Test count.
5. Framework and runner metadata.
6. Source location.
7. Test detail navigation.

Execution controls will only appear after the execution adapter contract is implemented and validated.

## Security boundary

The Test Explorer must never turn a test source path into an arbitrary shell command. Execution must go through the adapter/execution boundary with validated options and authorization.
