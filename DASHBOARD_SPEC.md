# Dashboard Specification

## Product Role

The dashboard is the primary product surface. It is an interactive control plane for an existing QA automation framework.

## Navigation

Initial modules:

1. Overview
2. Test Explorer
3. Test Execution
4. Automation
5. Failures & Debugging
6. Reports & Analytics
7. Framework
8. AI Assistant

## Overview

Answers: "What is happening with my automation framework?"

Display:

- project
- environment
- branch
- test count
- automated count
- pass rate
- failures
- skipped
- flaky tests
- latest execution
- execution trends

## Test Explorer

Capabilities:

- hierarchical suite/module/test browsing
- search
- filtering
- tags/markers
- priority
- status
- browser/environment
- test count
- source navigation

## Test Detail

Display:

- status
- framework
- automation technology
- tags
- duration
- pass history

Tabs:

- Overview
- Steps
- Code
- History
- Evidence
- Logs
- AI Analysis

## Execution

Expose framework-supported controls such as:

- suite/test selection
- environment
- browser
- tags
- workers
- retry failed
- screenshot/video/trace options

The UI sends an intent to the backend; the adapter translates it into native execution.

## Live Execution

Display:

- run ID
- environment
- start time
- progress
- total/passed/failed/skipped/running/retrying
- live test activity
- clickable test execution details

## Failures & Debugging

Classify failures into categories such as:

- automation issue
- application/product issue
- flaky test
- environment/infrastructure issue
- unknown

Show evidence:

- expected/actual
- screenshot
- video
- trace
- console
- network
- API
- database evidence
- logs

AI actions should be controlled and auditable.

## Automation

Display:

- total tests
- automated tests
- manual tests
- automation coverage
- candidates for automation

AI recommendations are advisory unless explicitly approved.

## Framework

Display discovered Framework DNA:

- language
- runner
- UI/API technology
- patterns
- reporting
- CI
- capabilities
- integrations
- skills

## AI Assistant

The assistant should be project-aware and context-aware.

Examples:

- explain a failure
- inspect a test
- summarize a run
- identify likely root cause
- recommend a retry
- identify capability gaps
- propose automation changes

The assistant must distinguish facts, evidence, inference, and recommendation.

## UX Principle

The dashboard should expose real framework capability rather than presenting controls that the connected framework cannot support.

Unsupported controls should be visibly marked rather than silently failing.
