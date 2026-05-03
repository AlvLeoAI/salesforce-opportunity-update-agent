# Tasks: Salesforce Opportunity Update Agent

**Input**: Design documents from `/home/alvaro/Projects/Portfolio/salesforce-opportunity-update-agent/specs/001-opportunity-update-agent/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/cli-contract.md`, `contracts/output-json-contract.md`
**Tests**: Required by the feature spec and constitution. Write story-level backend tests before implementation, and use TypeScript build as the lightweight UI smoke check.
**Organization**: Tasks are grouped by user story so each story can be implemented and verified independently after shared setup/foundation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel after its prerequisite phase is complete because it touches different files and does not depend on incomplete tasks.
- **[Story]**: User story label for story-phase tasks only.
- Every task includes an exact file path.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the repo skeleton, dependency manifests, fixtures, and documentation shells required before feature work.

- [X] T001 Create backend package markers in `backend/agent/__init__.py` and `backend/agent/tools/__init__.py`
- [X] T002 [P] Create backend dependency manifest with Pydantic v2, OpenAI SDK, python-dotenv, and pytest in `backend/requirements.txt`
- [X] T003 [P] Create local configuration example with `OPENAI_API_KEY` and fallback-mode notes in `backend/.env.example`
- [X] T004 [P] Create the rich mock Gong-style transcript fixture in `backend/data/transcripts/rich_signal.txt`
- [X] T005 [P] Create the thin mock Gong-style transcript fixture in `backend/data/transcripts/thin_signal.txt`
- [X] T006 [P] Create output/data placeholder files in `backend/outputs/.gitkeep` and `frontend/src/data/.gitkeep`
- [X] T007 [P] Create Vite React TypeScript package manifest and npm scripts in `frontend/package.json`
- [X] T008 [P] Create Vite and TypeScript config files in `frontend/vite.config.ts`, `frontend/tsconfig.json`, and `frontend/tsconfig.node.json`
- [X] T009 [P] Create frontend entry shell files in `frontend/index.html`, `frontend/src/main.tsx`, `frontend/src/App.tsx`, and `frontend/src/styles.css`
- [X] T010 [P] Create README skeleton with local setup, run, test, UI, and scope-boundary headings in `README.md`
- [X] T011 [P] Create WRITEUP skeleton with required take-home sections in `WRITEUP.md`
- [X] T012 [P] Create short demo script skeleton for a sub-five-minute Loom walkthrough in `docs/demo-script.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Define shared contracts and tool boundaries that all user stories rely on.

**Critical**: Do not start user story implementation until this phase is complete.

- [X] T013 Define scenario, stage, transcript, and transcript turn models in `backend/agent/models.py`
- [X] T014 Define evidence, next step, and MEDDPICC models in `backend/agent/models.py`
- [X] T015 Define opportunity update draft, abstain result, and top-level agent run output models in `backend/agent/models.py`
- [X] T016 Implement Pydantic validation for confidence bounds, ISO dates, discriminated result types, and UI-safe JSON serialization in `backend/agent/models.py`
- [X] T017 [P] Create structured-output prompt templates and fallback prompt notes in `backend/agent/prompts.py`
- [X] T018 Implement transcript loading, timestamp parsing, and malformed timestamp warnings in `backend/agent/tools/transcript_reader.py`
- [X] T019 [P] Create the OpenAI structured-output signal extractor interface and missing-API-key fallback boundary in `backend/agent/tools/signal_extractor.py`
- [X] T020 [P] Create the signal sufficiency and abstention decision interface in `backend/agent/tools/uncertainty_check.py`
- [X] T021 Implement schema validation and evidence coverage checks for `AgentRunOutput` in `backend/agent/tools/schema_validator.py`
- [X] T022 Create orchestration skeleton with explicit transcript_reader, signal_extractor, uncertainty_check, and schema_validator steps in `backend/agent/orchestrator.py`
- [X] T023 Create argparse CLI skeleton for `--all`, `--scenario`, `--input`, `--output`, and `--pretty` in `backend/run_agent.py`

**Checkpoint**: Foundation ready; story work can proceed in priority order or in parallel by separate implementers.

---

## Phase 3: User Story 1 - Review Rich Call Update Draft (Priority: P1) MVP

**Goal**: A rich transcript produces a validated Salesforce opportunity update draft with proposed fields, confidence, risks, next step, MEDDPICC notes, last-touch summary, and evidence for every populated field.

**Independent Test**: Run `python backend/run_agent.py --scenario rich_signal --pretty` and `pytest backend/tests/test_rich_signal.py backend/tests/test_evidence_coverage.py backend/tests/test_schema_validation.py`; confirm `backend/outputs/rich_signal_output.json` is a valid `draft` result with quote/timestamp evidence.

### Tests for User Story 1

Write these tests first and confirm they fail before implementation.

- [X] T024 [P] [US1] Add rich transcript draft behavior test in `backend/tests/test_rich_signal.py`
- [X] T025 [P] [US1] Add field-level quote, timestamp, and reasoning coverage test for all populated draft fields in `backend/tests/test_evidence_coverage.py`
- [X] T026 [P] [US1] Add Pydantic validation test for draft output JSON in `backend/tests/test_schema_validation.py`

### Implementation for User Story 1

- [X] T027 [US1] Implement rich transcript parsing integration and parser warning propagation in `backend/agent/tools/transcript_reader.py`
- [X] T028 [US1] Implement OpenAI structured-output extraction for supported rich transcript fields in `backend/agent/tools/signal_extractor.py`
- [X] T029 [US1] Implement deterministic rich-scenario fallback output for missing `OPENAI_API_KEY` in `backend/agent/tools/signal_extractor.py`
- [X] T030 [US1] Implement rich-signal sufficiency rules that allow a draft only when grounded field evidence exists in `backend/agent/tools/uncertainty_check.py`
- [X] T031 [US1] Enforce draft evidence coverage for `stage`, amount, close date, next step, MEDDPICC, and risks in `backend/agent/tools/schema_validator.py`
- [X] T032 [US1] Implement draft orchestration, trace recording, validation, and JSON writing in `backend/agent/orchestrator.py`
- [X] T033 [US1] Implement `--scenario rich_signal` CLI execution and summary output in `backend/run_agent.py`
- [X] T034 [US1] Verify rich draft generation with `pytest backend/tests/test_rich_signal.py backend/tests/test_evidence_coverage.py backend/tests/test_schema_validation.py`

**Checkpoint**: User Story 1 is independently demoable as the backend MVP.

---

## Phase 4: User Story 2 - Abstain on Thin Call Signal (Priority: P2)

**Goal**: A thin transcript produces a validated typed abstain state with "No meaningful update proposed", no opportunity field updates, a last-touch summary, and a clear abstention reason.

**Independent Test**: Run `python backend/run_agent.py --scenario thin_signal --pretty`, then `python backend/run_agent.py --all`, and confirm `pytest backend/tests/test_thin_signal.py backend/tests/test_cli_outputs.py backend/tests/test_schema_validation.py` passes.

### Tests for User Story 2

Write these tests first and confirm they fail before implementation.

- [X] T035 [P] [US2] Add thin transcript abstention behavior test in `backend/tests/test_thin_signal.py`
- [X] T036 [P] [US2] Add CLI output-file test for `backend/outputs/rich_signal_output.json` and `backend/outputs/thin_signal_output.json` in `backend/tests/test_cli_outputs.py`
- [X] T037 [US2] Add Pydantic validation test for abstain output JSON in `backend/tests/test_schema_validation.py`

### Implementation for User Story 2

- [X] T038 [US2] Implement thin transcript signal extraction and deterministic thin-scenario fallback in `backend/agent/tools/signal_extractor.py`
- [X] T039 [US2] Implement abstention thresholds and weak-signal checks that fail closed in `backend/agent/tools/uncertainty_check.py`
- [X] T040 [US2] Implement typed `AbstainResult` construction with last-touch summary and signals considered in `backend/agent/orchestrator.py`
- [X] T041 [US2] Extend orchestration so thin transcripts bypass draft field generation and still pass schema validation in `backend/agent/orchestrator.py`
- [X] T042 [US2] Implement `--scenario thin_signal` and `--all` CLI paths with documented exit codes in `backend/run_agent.py`
- [X] T043 [US2] Verify thin abstention and output writing with `pytest backend/tests/test_thin_signal.py backend/tests/test_cli_outputs.py backend/tests/test_schema_validation.py`

**Checkpoint**: User Stories 1 and 2 both work through the CLI and write validated JSON artifacts.

---

## Phase 5: User Story 3 - Complete Five-Minute Demo Review (Priority: P3)

**Goal**: A reviewer can open the static UI, switch between rich and thin scenarios, inspect evidence, see confidence/risk information, and see Approve/Edit/Reject affordances without any real CRM integration.

**Independent Test**: Run `cd frontend && npm run build`, then `cd frontend && npm run dev`; verify rich draft rendering, thin abstain rendering, evidence disclosure, confidence/risk display, and review buttons.

### Tests for User Story 3

- [X] T044 [P] [US3] Add TypeScript result contract types matching backend JSON in `frontend/src/types.ts`
- [X] T045 [P] [US3] Add UI smoke checklist covering rich, thin, evidence, confidence/risk, and review controls in `docs/demo-script.md`

### Implementation for User Story 3

- [X] T046 [US3] Copy validated backend outputs into static UI fixture files in `frontend/src/data/rich_signal_output.json` and `frontend/src/data/thin_signal_output.json`
- [X] T047 [US3] Add frontend data loader and scenario metadata in `frontend/src/data/results.ts`
- [X] T048 [P] [US3] Implement Approve, Edit, and Reject affordance buttons in `frontend/src/components/ReviewActions.tsx`
- [X] T049 [P] [US3] Implement field evidence expand or hover disclosure in `frontend/src/components/EvidenceDisclosure.tsx`
- [X] T050 [P] [US3] Implement confidence and risk display in `frontend/src/components/ConfidenceRisk.tsx`
- [X] T051 [US3] Implement rich opportunity draft review view in `frontend/src/components/DraftReview.tsx`
- [X] T052 [US3] Implement thin abstain review view with "No meaningful update proposed" in `frontend/src/components/AbstainReview.tsx`
- [X] T053 [US3] Compose scenario selector, rich view, thin view, and review actions in `frontend/src/App.tsx`
- [X] T054 [US3] Style the static review UI for compact AE review without decorative scope creep in `frontend/src/styles.css`
- [X] T055 [US3] Ensure JSON imports and React build settings are configured in `frontend/tsconfig.json` and `frontend/vite.config.ts`
- [X] T056 [US3] Verify UI compilation with `cd frontend && npm run build` using `frontend/package.json`

**Checkpoint**: All three user stories are independently functional and ready for local demo review.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Tighten documentation, delivery validation, and scope boundaries across the full take-home.

- [X] T057 [P] Update local setup, agent run, backend test, frontend build, frontend dev, and generated-output handoff commands in `README.md`
- [X] T058 [P] Document framework choice, rejected FastAPI/Streamlit/heavy-framework alternatives, and model selection in `WRITEUP.md`
- [X] T059 [P] Document production evaluation harness, golden transcript strategy, field precision/recall, evidence accuracy, and abstention accuracy in `WRITEUP.md`
- [X] T060 [P] Document expected failure modes, mitigations, observability signals, production UI improvements, and intentionally cut scope in `WRITEUP.md`
- [X] T061 [P] Complete the sub-five-minute Loom walkthrough script with exact commands and talking points in `docs/demo-script.md`
- [X] T062 Run full backend validation with `pytest backend/tests` and address failures in `backend/tests/`
- [X] T063 Run full frontend validation with `cd frontend && npm run build` and address failures in `frontend/src/`
- [X] T064 Validate the documented quickstart end-to-end and reconcile any drift in `specs/001-opportunity-update-agent/quickstart.md` and `README.md`
- [X] T065 Audit excluded scope remains absent and record the result in `WRITEUP.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 Setup**: No dependencies; start immediately.
- **Phase 2 Foundational**: Depends on Phase 1; blocks all user stories.
- **Phase 3 US1**: Depends on Phase 2; recommended MVP.
- **Phase 4 US2**: Depends on Phase 2 and can run after or beside US1, but final `--all` verification expects US1 output behavior.
- **Phase 5 US3**: Depends on validated backend JSON outputs from US1 and US2.
- **Phase 6 Polish**: Depends on whichever stories are intended for final delivery; full delivery depends on all user stories.

### User Story Dependencies

- **US1 Rich Draft (P1)**: No dependency on other user stories after foundation. Delivers the backend MVP.
- **US2 Thin Abstain (P2)**: No dependency on UI after foundation. Shares orchestrator and CLI files with US1, so coordinate if implemented in parallel.
- **US3 Five-Minute Review UI (P3)**: Depends on JSON contract and validated rich/thin output artifacts.

### Within Each User Story

- Write tests before implementation for backend stories.
- Keep schema changes in `backend/agent/models.py` before tool or orchestrator changes.
- Keep transcript reader, signal extractor, uncertainty check, and schema validator boundaries explicit.
- Validate each story independently before starting polish.

---

## Parallel Opportunities

- **Setup**: T002-T012 can run in parallel after T001 if separate files are owned by separate implementers.
- **Foundation**: T017, T019, and T020 can run in parallel once T013-T016 define model names; T018, T021, T022, and T023 should coordinate imports.
- **US1**: T024-T026 can run in parallel as tests; T028 and T030 can run in parallel after the signal shape is agreed.
- **US2**: T035-T036 can run in parallel; T038 and T039 can run in parallel after the abstain contract is stable.
- **US3**: T048-T050 can run in parallel as independent UI components after T044 and T047 are complete.
- **Polish**: T057-T061 can run in parallel with separate documentation ownership.

## Parallel Example: User Story 1

```bash
# After Phase 2, assign these test tasks together:
Task: "T024 Add rich transcript draft behavior test in backend/tests/test_rich_signal.py"
Task: "T025 Add field-level quote, timestamp, and reasoning coverage test in backend/tests/test_evidence_coverage.py"
Task: "T026 Add Pydantic validation test for draft output JSON in backend/tests/test_schema_validation.py"

# After test shape is agreed, split implementation:
Task: "T028 Implement OpenAI structured-output extraction for supported rich transcript fields in backend/agent/tools/signal_extractor.py"
Task: "T030 Implement rich-signal sufficiency rules that allow a draft only when grounded field evidence exists in backend/agent/tools/uncertainty_check.py"
```

## Parallel Example: User Story 3

```bash
# After data loading is in place, split component work:
Task: "T048 Implement Approve, Edit, and Reject affordance buttons in frontend/src/components/ReviewActions.tsx"
Task: "T049 Implement field evidence expand or hover disclosure in frontend/src/components/EvidenceDisclosure.tsx"
Task: "T050 Implement confidence and risk display in frontend/src/components/ConfidenceRisk.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Complete Phase 1 setup.
2. Complete Phase 2 foundation.
3. Complete Phase 3 rich transcript draft.
4. Stop and validate with `pytest backend/tests/test_rich_signal.py backend/tests/test_evidence_coverage.py backend/tests/test_schema_validation.py`.
5. Demo the generated `backend/outputs/rich_signal_output.json` before adding thin abstention or UI polish.

### Incremental Delivery

1. Add **US1** to prove grounded draft generation.
2. Add **US2** to prove abstention and no-hallucination behavior.
3. Add **US3** to prove reviewer-facing clarity and five-minute demo usability.
4. Finish Phase 6 only after the three acceptance paths are working.

### Scope Control

- Do not add real Salesforce integration, real Gong integration, database storage, auth, RAG, vector database, fine-tuning, autonomous writeback, background queues, or heavy agent frameworks.
- Keep fallback behavior fixture-based and transparent; do not present fallback output as live model reasoning.
- Keep review buttons as non-functional affordances for the take-home unless the spec changes.
