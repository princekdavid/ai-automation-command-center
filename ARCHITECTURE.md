# Architecture

## System Model
```
Existing Automation Framework
        ↓
Framework Adapter / Discovery
        ↓
Framework Understanding / Capability Map
        ↓
Interactive Automation Dashboard
        ↓
AI Layer
        ↓
Agents / Execution / Analysis / Skill System
```

## Major Components
- Dashboard frontend
- Backend/API
- Framework discovery
- Framework adapters
- Execution service
- Skill system
- Agent orchestration
- AI analysis
- Storage
- Reporting/evidence
- Integrations

## Framework DNA
Discovery builds a project-specific model containing language, dependencies, test runner, UI/API/DB technologies, architecture patterns, utilities, commands, CI/CD, reporting and supported capabilities.

## Adapter Principle
Dashboard intent is translated into framework-native operations. The dashboard must not assume a universal command structure.

## Agent Layer
Initial agents may include Orchestrator, Framework, Execution, Analysis and Skill agents. Agents operate through validated capabilities and project-aware skills.

## Security Boundary
Repository access is read-only by default. Write, merge, delete and destructive execution actions require explicit authorization and appropriate controls.
