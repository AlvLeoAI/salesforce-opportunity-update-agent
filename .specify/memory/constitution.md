<!--
Sync Impact Report
Version change: template -> 1.0.0
Modified principles:
- PRINCIPLE_1_NAME placeholder -> I. Reliability Over Complexity
- PRINCIPLE_2_NAME placeholder -> II. Typed Outputs Over Free-Form Text
- PRINCIPLE_3_NAME placeholder -> III. Grounded Evidence for Every Field
- PRINCIPLE_4_NAME placeholder -> IV. Abstention Over Hallucination
- PRINCIPLE_5_NAME placeholder -> V. Human-in-the-Loop Review
- Added VI. Separation of Agent Responsibilities
- Added VII. Local-First Execution
- Added VIII. Minimal AE-Focused UI
- Added IX. Evaluation and Failure-Mode Visibility
- Added X. Clean End-to-End Delivery
Added sections:
- Technical Scope and Intentional Exclusions
- Delivery Workflow and Quality Gates
Removed sections: None
Templates requiring updates:
- .specify/templates/plan-template.md: updated
- .specify/templates/spec-template.md: updated
- .specify/templates/tasks-template.md: updated
- .specify/templates/agent-file-template.md: reviewed, no changes required
- .specify/templates/checklist-template.md: reviewed, no changes required
- .specify/templates/commands/*.md: not present
Follow-up TODOs: None
-->
# Salesforce Opportunity Update Agent Constitution

## Core Principles

### I. Reliability Over Complexity
The system MUST favor explicit, deterministic behavior over clever abstractions.
The local agent MUST use simple tool orchestration that can be followed in code,
with each step visible in module boundaries or logs. No component may add an
external service, framework, database, vector index, RAG pipeline, fine-tuning
path, or real Salesforce/Gong integration unless this constitution is amended
first.

Rationale: The take-home is judged on end-to-end correctness and trust, not
infrastructure breadth.

### II. Typed Outputs Over Free-Form Text
All agent outputs that drive UI state or Salesforce draft fields MUST be
represented by Pydantic models and generated through OpenAI structured outputs.
Free-form LLM prose may only appear as user-facing explanatory text after typed
validation succeeds. Invalid structured output MUST fail closed and surface a
reviewable error state rather than being coerced silently.

Rationale: Salesforce updates require predictable fields, validation, and
deterministic failure handling.

### III. Grounded Evidence for Every Field
Every proposed opportunity field update MUST include transcript evidence with
both a quote and timestamp. Field values MUST be traceable to that evidence, and
the UI MUST expose the evidence and reasoning to the AE. The agent MUST NOT
infer updates from generic sales patterns when transcript support is absent.

Rationale: AE trust depends on being able to audit why a draft was produced.

### IV. Abstention Over Hallucination
The agent MUST abstain when a transcript lacks meaningful opportunity-update
signal. The thin transcript fixture MUST produce an abstain/no meaningful update
state, while the rich transcript fixture MUST produce a meaningful Salesforce
opportunity update draft. Abstention MUST be a first-class typed state, not an
error or empty draft.

Rationale: A trustworthy revenue workflow must prefer no update over a
fabricated one.

### V. Human-in-the-Loop Review
The system MUST produce drafts for human review, never autonomous CRM writeback.
The UI MUST make Approve, Edit, and Reject available as review affordances, and
those controls may be non-functional for the take-home. The UI MUST render both
rich-update and abstain states clearly enough to demo in under five minutes.

Rationale: The project simulates AE workflow support without claiming production
Salesforce integration.

### VI. Separation of Agent Responsibilities
Agent logic, schema validation, transcript parsing, uncertainty/abstention
checks, tool orchestration, and UI rendering MUST live in distinct small modules
or clearly separated functions. A single monolithic prompt or hidden chain of
ad hoc transformations is not acceptable. Names MUST describe the business role
of each module.

Rationale: Small boundaries make failures easier to inspect, test, and explain
in the write-up.

### VII. Local-First Execution
The agent MUST run locally against mock Gong-style transcripts and local fixture
data. The UI MAY be deployed separately, including to Vercel, only if local
execution remains the canonical demo path. The system MUST NOT require a
database, auth service, real Salesforce tenant, real Gong data, vector database,
or background infrastructure.

Rationale: Local-first delivery makes the take-home reproducible for reviewers.

### VIII. Minimal AE-Focused UI
The UI MUST prioritize review clarity over visual polish. It MUST show the
proposed field updates, abstain state, transcript evidence, confidence or
uncertainty indicators where available, and review affordances without hiding
reasoning behind decorative layout. React or single-file HTML are both
acceptable.

Rationale: The UI exists to help an AE decide whether the draft is trustworthy.

### IX. Evaluation and Failure-Mode Visibility
The project MUST include a lightweight evaluation harness or smoke checks that
verify the rich transcript, thin transcript, Pydantic validation, and evidence
requirements. The write-up MUST document expected failure modes, mitigations,
observability signals, and intentionally cut scope.

Rationale: Production thinking is demonstrated through known risks and
validation strategy, not added infrastructure.

### X. Clean End-to-End Delivery
Implementation MUST keep dependencies minimal, commands reproducible, README
instructions simple, and the demo path short. Code generation, no-code
frameworks, broad abstractions, and hidden magic MUST be avoided unless they
directly reduce risk for the required behavior. Complete thin/rich behavior
outranks over-engineered partial features.

Rationale: The scoring surface is a working, understandable system under time
constraints.

## Technical Scope and Intentional Exclusions

The project is a Python local agent with Pydantic schemas, OpenAI structured
outputs, explicit tool orchestration, mock transcript fixtures, and a minimal
human-review UI. The canonical data path is transcript fixture to parser/tool
orchestration to structured draft or abstain state to Pydantic validation to
UI-ready JSON to AE review UI.

The following are out of scope unless this constitution is amended: real
Salesforce writes, real Gong ingestion, databases, authentication, RAG, vector
search, fine-tuning, background queues, multi-agent frameworks, enterprise
deployment hardening, and broad CRM configuration systems. Any plan that
introduces one of these exclusions MUST document the violation and justify why
the take-home requirement cannot be met without it.

## Delivery Workflow and Quality Gates

All implementation plans MUST pass these gates before development continues:
rich transcript produces a meaningful validated draft; thin transcript produces
a typed abstention; every proposed field update has quote and timestamp
evidence; UI renders both states; local run commands are reproducible; README
explains the five-minute demo path; evaluation or smoke checks cover the
required fixtures; write-up covers failure modes, mitigations, observability,
and cut scope.

Code MUST be organized into small modules with clear names and minimal
dependencies. Changes that affect schema, parsing, tool orchestration,
abstention, or UI rendering MUST include a focused validation step. Tests may
be lightweight, but the required rich/thin/evidence/Pydantic checks are
mandatory for delivery.

## Governance

This constitution supersedes conflicting project guidance for the Salesforce
Opportunity Update Agent. Amendments MUST be documented in
`.specify/memory/constitution.md`, include a Sync Impact Report, and propagate
any changed gates into Spec Kit templates before feature planning or
implementation proceeds.

Versioning follows semantic versioning: MAJOR for removing or redefining core
principles or intentional exclusions; MINOR for adding principles, delivery
gates, or materially expanding required behavior; PATCH for clarifications that
preserve existing obligations. Compliance review is required during
`/speckit.plan`, `/speckit.tasks`, and before final delivery, with any
unresolved violations recorded in the plan's Complexity Tracking section.

**Version**: 1.0.0 | **Ratified**: 2026-04-28 | **Last Amended**: 2026-04-28
