# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python [version] for local agent; [React or single-file HTML] for UI  
**Primary Dependencies**: Pydantic, OpenAI SDK structured outputs, [minimal UI dependencies]  
**Storage**: N/A - no database; local mock transcript fixtures only  
**Testing**: pytest or lightweight smoke/evaluation harness  
**Target Platform**: Local developer machine; optional static UI deployment only  
**Project Type**: Local agent plus human-review UI  
**Performance Goals**: Demo rich and thin transcript flows in under 5 minutes  
**Constraints**: No real Salesforce, real Gong data, database, auth, RAG, vector database, or fine-tuning  
**Scale/Scope**: Two required transcript states: rich update draft and thin abstention

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [ ] Explicit tool orchestration is planned; no single monolithic prompt owns the flow.
- [ ] Pydantic schemas define all UI-facing and Salesforce draft output states.
- [ ] OpenAI structured outputs are used for schema-constrained JSON generation.
- [ ] Rich transcript path produces a meaningful validated opportunity update draft.
- [ ] Thin transcript path produces a typed abstain/no meaningful update state.
- [ ] Every proposed field update includes supporting quote and timestamp evidence.
- [ ] UI renders rich and abstain states with evidence and AE review affordances.
- [ ] Agent logic, schema validation, transcript parsing, uncertainty checking, and UI rendering are separated.
- [ ] No excluded scope is introduced: real Salesforce, real Gong data, database, auth, RAG, vector DB, or fine-tuning.
- [ ] Evaluation/smoke checks and write-up coverage are planned for required fixtures, failure modes, mitigations, observability, and cut scope.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
