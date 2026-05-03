# Implementation Plan: Salesforce Opportunity Update Agent

**Branch**: `001-opportunity-update-agent` | **Date**: 2026-04-28 | **Spec**: `/home/alvaro/Projects/Portfolio/salesforce-opportunity-update-agent/specs/001-opportunity-update-agent/spec.md`  
**Input**: Feature specification from `/home/alvaro/Projects/Portfolio/salesforce-opportunity-update-agent/specs/001-opportunity-update-agent/spec.md`

## Summary

Build a local-first Revenue AI demo that converts two mock Gong-style sales call
transcripts into precomputed review outputs: a grounded Salesforce opportunity
update draft for the rich transcript and an explicit abstain state for the thin
transcript. The implementation uses a small Python CLI agent with Pydantic
schemas, OpenAI structured outputs, explicit hand-rolled tool orchestration, and
a Vite React TypeScript UI that reads generated JSON from local files. No backend
API, database, auth, Salesforce, Gong, RAG, vector database, fine-tuning, or
heavy agent framework is included.

## Technical Context

**Language/Version**: Python 3.11+ for local agent; TypeScript with Vite React for UI  
**Primary Dependencies**: Pydantic v2, OpenAI Python SDK, python-dotenv; Vite, React, TypeScript  
**Storage**: Local fixture files and generated JSON only; no database  
**Testing**: pytest for backend validation/evaluation; TypeScript build or lightweight UI smoke check  
**Target Platform**: Local developer machine; optional Vercel deployment for static UI  
**Project Type**: web app: local Python CLI agent plus Vite React static UI  
**Performance Goals**: Generate both transcript outputs and review both UI states in under 5 minutes  
**Constraints**: No real Salesforce, real Gong data, real customer data, backend API, auth, database, RAG, vector database, fine-tuning, autonomous CRM writeback, or heavy agent framework  
**Scale/Scope**: Two required transcripts, two output states, field-level evidence coverage, README/WRITEUP production-thinking narrative

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] Explicit tool orchestration is planned; no single monolithic prompt owns the flow.
- [x] Pydantic schemas define all UI-facing and Salesforce draft output states.
- [x] OpenAI structured outputs are used for schema-constrained JSON generation.
- [x] Rich transcript path produces a meaningful validated opportunity update draft.
- [x] Thin transcript path produces a typed abstain/no meaningful update state.
- [x] Every proposed field update includes supporting quote and timestamp evidence.
- [x] UI renders rich and abstain states with evidence and AE review affordances.
- [x] Agent logic, schema validation, transcript parsing, uncertainty checking, and UI rendering are separated.
- [x] No excluded scope is introduced: real Salesforce, real Gong data, database, auth, RAG, vector DB, or fine-tuning.
- [x] Evaluation/smoke checks and write-up coverage are planned for required fixtures, failure modes, mitigations, observability, and cut scope.

**Gate result**: PASS. The plan stays within the constitution and records no
complexity violations.

## Project Structure

### Documentation (this feature)

```text
/home/alvaro/Projects/Portfolio/salesforce-opportunity-update-agent/specs/001-opportunity-update-agent/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── cli-contract.md
│   └── output-json-contract.md
└── tasks.md             # Created later by /speckit.tasks
```

### Source Code (repository root)

```text
/home/alvaro/Projects/Portfolio/salesforce-opportunity-update-agent/
├── backend/
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── orchestrator.py
│   │   ├── prompts.py
│   │   └── tools/
│   │       ├── __init__.py
│   │       ├── transcript_reader.py
│   │       ├── signal_extractor.py
│   │       ├── schema_validator.py
│   │       └── uncertainty_check.py
│   ├── data/
│   │   └── transcripts/
│   │       ├── rich_signal.txt
│   │       └── thin_signal.txt
│   ├── outputs/
│   │   ├── rich_signal_output.json
│   │   └── thin_signal_output.json
│   ├── tests/
│   │   ├── test_evidence_coverage.py
│   │   ├── test_rich_signal.py
│   │   ├── test_schema_validation.py
│   │   └── test_thin_signal.py
│   ├── run_agent.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── data/
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── README.md
└── WRITEUP.md
```

**Structure Decision**: Use the requested backend/frontend split. The backend is
a local CLI agent, not a service. The frontend is static and consumes generated
JSON copied or imported into `frontend/src/data/`, avoiding a backend API.

## Phase 0 Research Summary

Research decisions are captured in `/home/alvaro/Projects/Portfolio/salesforce-opportunity-update-agent/specs/001-opportunity-update-agent/research.md`.
No unresolved technical clarifications remain.

## Phase 1 Design Summary

Data model is captured in `/home/alvaro/Projects/Portfolio/salesforce-opportunity-update-agent/specs/001-opportunity-update-agent/data-model.md`.
CLI and output contracts are captured in `/home/alvaro/Projects/Portfolio/salesforce-opportunity-update-agent/specs/001-opportunity-update-agent/contracts/`.
Quickstart is captured in `/home/alvaro/Projects/Portfolio/salesforce-opportunity-update-agent/specs/001-opportunity-update-agent/quickstart.md`.

## Testing Strategy

- Pydantic schema validation tests verify draft, abstain, evidence, and UI-ready
  output models.
- Rich transcript test verifies a draft result, non-empty proposed updates,
  confidence in range, risks when supported, and evidence for every populated
  proposed field.
- Thin transcript test verifies an abstain result, zero proposed updates, clear
  "No meaningful update proposed" state, and last-touch summary.
- Evidence coverage test walks all non-empty update field paths and fails if any
  field lacks timestamp, exact quote, and reasoning note.
- UI smoke check verifies both JSON fixtures render, rich evidence disclosures
  are available, and Approve/Edit/Reject affordances are visible.

## Production Evaluation Strategy

- Maintain a golden transcript set with expected field updates, abstentions, and
  evidence citations.
- Track field-level precision and recall for opportunity fields and MEDDPICC
  entries.
- Track evidence citation accuracy by checking whether cited quote/timestamp
  directly supports each proposed field.
- Track abstention accuracy with thin, ambiguous, contradictory, and rich
  transcript categories.
- Run regression tests before prompt, schema, or model changes; block changes
  that reduce evidence coverage or increase hallucinated updates.

## Post-Design Constitution Check

- [x] Tool orchestration remains explicit across transcript reader, signal extractor, uncertainty check, schema validator, and orchestrator.
- [x] All output states are typed and validated before UI consumption.
- [x] Evidence coverage is modeled and tested for every proposed field.
- [x] Abstention is a first-class output state with last-touch summary.
- [x] UI remains static, local-demo friendly, and review-focused.
- [x] No excluded infrastructure or integrations are introduced.
- [x] README/WRITEUP coverage is planned for demo, model choice, rejected alternatives, evaluation, failure modes, mitigations, production UI improvements, and intentional cuts.

**Post-design gate result**: PASS.

## Complexity Tracking

No constitution violations or justified complexity exceptions.
