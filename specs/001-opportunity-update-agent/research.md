# Research: Salesforce Opportunity Update Agent

## Decision: Use a local Python CLI agent instead of a web backend

**Rationale**: The system only needs to process local mock transcripts and write
JSON artifacts for a static UI. A CLI keeps the demo reproducible, avoids server
startup complexity, and aligns with the local-first constitution.

**Alternatives considered**: FastAPI backend was rejected because no runtime API
is required. A Streamlit app was rejected because the requested UI direction is
Vite React or single-file HTML, and the static UI can consume precomputed JSON.

## Decision: Use hand-rolled orchestration with explicit tools

**Rationale**: The required flow is short and auditable: read transcript,
extract grounded signals, decide whether signal is sufficient, validate schema,
write output. Small modules make failures easy to explain in the take-home
write-up.

**Alternatives considered**: LangGraph, CrewAI, AutoGen, and similar frameworks
were rejected as unnecessary for two fixture scenarios and likely to obscure the
control flow.

## Decision: Use Pydantic v2 as the source of truth for output models

**Rationale**: Pydantic gives strict enums, ISO date validation, confidence
bounds, discriminated output states, and custom validators for evidence coverage.
The same models can validate both model output and generated JSON files.

**Alternatives considered**: Dataclasses plus manual checks were rejected because
they invite ad hoc validation. JSON Schema alone was rejected because Python-side
validators are needed for evidence coverage and abstention rules.

## Decision: Use OpenAI structured outputs for extraction and drafting

**Rationale**: The feature requires reliable JSON generation. Structured outputs
constrain model responses to the typed schema and reduce parsing failure modes.
The implementation will still validate every result with Pydantic before writing
UI JSON.

**Alternatives considered**: A single free-form prompt was rejected by the
constitution. Regex-only extraction was rejected because sales-call language can
vary and the take-home is explicitly a Revenue AI task.

## Decision: Represent evidence with field paths

**Rationale**: The requested Salesforce draft schema includes nested fields and a
plain list of risk strings. A separate `evidence_by_field` map keyed by field
path, such as `stage`, `next_step.due_date`, or `risks[0]`, preserves the exact
draft shape while enforcing evidence on every populated field.

**Alternatives considered**: Wrapping every value in `{value, evidence}` was
rejected because it changes the requested output shape too aggressively. Keeping
evidence only in a global list was rejected because it weakens field-level
traceability.

## Decision: Make abstention a discriminated output state

**Rationale**: The thin transcript must abstain clearly while still logging the
touch. A separate abstain state prevents empty drafts from being mistaken for
valid updates and gives the UI a stable state to render.

**Alternatives considered**: Returning a draft with all fields null was rejected
because it hides the agent's decision. Throwing an error was rejected because
abstention is expected behavior, not a failure.

## Decision: Use Vite React TypeScript for the UI

**Rationale**: Vite React TypeScript keeps the UI static, easy to demo, and
compatible with optional Vercel deployment. TypeScript can mirror the output
contract and catch rendering drift while still keeping the UI modest.

**Alternatives considered**: A single HTML file was acceptable by the
constitution but rejected here because React components make evidence disclosure,
two-state rendering, and small UI tests easier. A backend-rendered UI was
rejected because no backend API is required.

## Decision: Save backend outputs under `backend/outputs/`

**Rationale**: JSON files provide a durable handoff from the local agent to the
static UI and make the five-minute demo simple: run the agent, then open the UI.

**Alternatives considered**: In-memory handoff was rejected because it would
require a server. Browser-side model calls were rejected because the agent must
run locally and avoid exposing secrets in the UI.

## Decision: Keep evaluation lightweight but production-oriented

**Rationale**: The take-home needs production thinking without extra
infrastructure. A golden transcript set, field-level precision/recall, evidence
citation accuracy, abstention accuracy, and prompt/model regression checks
demonstrate the right evaluation posture.

**Alternatives considered**: Manual-only review was rejected because it does not
guard against prompt/model regressions. Full observability infrastructure was
rejected as out of scope for a local demo.
