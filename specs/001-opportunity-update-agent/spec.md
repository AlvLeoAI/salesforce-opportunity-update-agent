# Feature Specification: Salesforce Opportunity Update Agent

**Feature Branch**: `001-opportunity-update-agent`  
**Created**: 2026-04-28  
**Status**: Draft  
**Input**: User description: "Build a local-first Revenue AI take-home task solution that converts mock Gong-style sales call transcripts into structured Salesforce opportunity update drafts with explicit evidence and abstention behavior."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review Rich Call Update Draft (Priority: P1)

An Account Executive reviews the result of a rich sales call transcript and sees
a structured Salesforce opportunity update draft with proposed field values,
confidence, risks, next step, MEDDPICC notes, and supporting transcript evidence.

**Why this priority**: This is the primary value of the take-home: converting a
meaningful customer conversation into a reviewable CRM update without hiding the
evidence behind the recommendation.

**Independent Test**: Run the rich transcript scenario and confirm the result is
a validated opportunity update draft with at least one proposed field update and
visible quote/timestamp evidence for every non-empty proposed field.

**Acceptance Scenarios**:

1. **Given** a rich signal transcript with concrete deal details, **When** the
   transcript is processed, **Then** the user sees a structured opportunity
   update draft containing grounded proposed updates.
2. **Given** the user opens any proposed field in the rich update, **When** they
   inspect the evidence, **Then** they see the transcript timestamp, exact quote,
   and short reasoning note that supports that field.
3. **Given** the rich update includes risks or a next step, **When** the user
   reviews the draft, **Then** confidence and risk indicators are visible before
   any review action is taken.

---

### User Story 2 - Abstain on Thin Call Signal (Priority: P2)

An Account Executive reviews the result of a thin sales call transcript and sees
a clear "No meaningful update proposed" state instead of fabricated opportunity
fields, while still seeing a concise last-touch summary.

**Why this priority**: Trust depends on the system refusing to invent CRM updates
when the call does not contain enough signal.

**Independent Test**: Run the thin transcript scenario and confirm the result is
a validated abstain state with no proposed opportunity field updates and a
last-touch summary that records the interaction.

**Acceptance Scenarios**:

1. **Given** a thin signal transcript with no meaningful opportunity update
   details, **When** the transcript is processed, **Then** the user sees "No
   meaningful update proposed."
2. **Given** the thin result is displayed, **When** the user reviews the page,
   **Then** the last-touch summary explains that the call occurred without
   proposing unsupported Salesforce changes.
3. **Given** the thin result lacks evidence for a field, **When** output is
   generated, **Then** that field is empty, null, or omitted according to the
   documented output contract.

---

### User Story 3 - Complete Five-Minute Demo Review (Priority: P3)

A take-home reviewer can run the local demo, view both transcript scenarios in a
minimal review UI, and understand the system's decisions, evidence, abstention
logic, and intentional scope boundaries in under five minutes.

**Why this priority**: The deliverable must be easy to assess quickly while
still demonstrating production thinking through validation, failure modes, and
explicit cuts.

**Independent Test**: Follow the local run instructions from a clean checkout and
confirm the reviewer can view the rich draft and thin abstain states, including
Approve, Edit, and Reject review affordances, in under five minutes.

**Acceptance Scenarios**:

1. **Given** the reviewer follows the documented local run path, **When** the UI
   opens, **Then** both rich and thin transcript results are available for
   review.
2. **Given** the reviewer views the rich result, **When** they inspect proposed
   fields, **Then** supporting evidence is visible on expand or hover.
3. **Given** the reviewer views either result, **When** they look for review
   controls, **Then** Approve, Edit, and Reject buttons are visible as
   non-functional affordances.

### Edge Cases

- What happens when transcript turns have missing or malformed timestamps?
- How does the system handle contradictory opportunity signals in the same call?
- How does the system handle a transcript with polite conversation but no
  meaningful sales signal?
- How does the system handle a proposed field that has weak or indirect
  evidence?
- How does the system handle output that does not conform to the documented
  schema?
- How does the system behave when required local configuration for generating
  structured output is unavailable during a demo?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept a plain-text mock sales call transcript as the
  input for each scenario.
- **FR-002**: System MUST support exactly the two required demo transcript
  scenarios: rich signal and thin signal.
- **FR-003**: System MUST produce either a Salesforce opportunity update draft
  or an explicit abstain result for every processed transcript.
- **FR-004**: System MUST produce a meaningful opportunity update draft for the
  rich signal transcript.
- **FR-005**: System MUST produce an abstain result for the thin signal
  transcript and MUST NOT propose unsupported opportunity field updates.
- **FR-006**: System MUST preserve a last-touch summary for both scenarios,
  including the thin transcript abstain state.
- **FR-007**: System MUST record reviewable evidence for every non-empty
  proposed opportunity field value, including nested next-step, MEDDPICC, and
  risk fields.
- **FR-008**: Each evidence item MUST contain a transcript timestamp, exact
  quote, and short reasoning note.
- **FR-009**: System MUST leave unsupported field values empty, null, or omitted
  according to the documented output contract rather than inventing missing
  information.
- **FR-010**: System MUST validate generated outputs against the documented
  schema before those outputs are considered ready for UI review.
- **FR-011**: System MUST expose a confidence value from 0 to 1 for opportunity
  update drafts.
- **FR-012**: System MUST expose risk indicators when transcript evidence
  supports deal risks.
- **FR-013**: UI MUST render the rich transcript result as a Salesforce
  opportunity update draft.
- **FR-014**: UI MUST render the thin transcript result as a clear abstain state
  with the phrase "No meaningful update proposed."
- **FR-015**: UI MUST make field-level evidence visible on expand, hover, or an
  equivalent lightweight disclosure interaction.
- **FR-016**: UI MUST include Approve, Edit, and Reject buttons as
  non-functional review affordances.
- **FR-017**: UI MUST be understandable to an Account Executive in under five
  minutes without requiring knowledge of the underlying implementation.
- **FR-018**: README and write-up MUST explain local run instructions, framework
  choice, rejected alternative, model selection, evaluation approach, expected
  failure modes, mitigations, production UI improvements, and intentionally cut
  scope.

### Constitution-Driven Requirements

- **CDR-001**: System MUST process mock Gong-style transcript fixtures locally.
- **CDR-002**: System MUST produce either a validated Salesforce opportunity
  update draft or a typed abstain/no meaningful update state.
- **CDR-003**: The rich transcript fixture MUST produce a meaningful opportunity
  update draft.
- **CDR-004**: The thin transcript fixture MUST produce an abstain/no meaningful
  update state.
- **CDR-005**: Every proposed field update MUST include supporting transcript
  evidence with quote and timestamp.
- **CDR-006**: Structured output MUST pass Pydantic validation before being
  rendered by the UI.
- **CDR-007**: UI MUST show evidence and reasoning to the Account Executive and
  expose Approve, Edit, and Reject review affordances.
- **CDR-008**: System MUST NOT require real Salesforce, real Gong data, database,
  auth, RAG, vector database, or fine-tuning.
- **CDR-009**: README or write-up MUST document local demo commands, evaluation
  approach, expected failure modes, mitigations, observability, and intentionally
  cut scope.

### Scope Boundaries

- **SB-001**: System MUST NOT write to Salesforce or claim autonomous CRM
  writeback.
- **SB-002**: System MUST NOT ingest real Gong data or real customer data.
- **SB-003**: System MUST NOT require a database, authentication, RAG, vector
  database, fine-tuning, or a broad agent framework.
- **SB-004**: Optional UI deployment MUST NOT replace the local demo path.

### Output Contract

- **Opportunity Update Draft** MUST include:
  - `opportunity_id`: string
  - `stage`: one of prospecting, discovery, solution_design, proposal,
    negotiation, closed_won, closed_lost
  - `amount_usd`: number when supported by evidence
  - `close_date`: ISO date string when supported by evidence
  - `next_step.description`: string when supported by evidence
  - `next_step.owner`: string when supported by evidence
  - `next_step.due_date`: ISO date string when supported by evidence
  - `meddpicc.metrics`: string when supported by evidence
  - `meddpicc.economic_buyer`: string when supported by evidence
  - `meddpicc.decision_criteria`: string when supported by evidence
  - `meddpicc.decision_process`: string when supported by evidence
  - `meddpicc.paper_process`: string when supported by evidence
  - `meddpicc.identify_pain`: string when supported by evidence
  - `meddpicc.champion`: string when supported by evidence
  - `meddpicc.competition`: string when supported by evidence
  - `risks`: list of strings when supported by evidence
  - `last_touch_summary`: string
  - `confidence`: float from 0 to 1
- **Evidence** MUST be attached to every non-empty proposed field and MUST
  include timestamp, exact quote, and reasoning note.
- **Abstain Result** MUST clearly state that no meaningful update is proposed
  and MUST include a last-touch summary.

### Key Entities *(include if feature involves data)*

- **Transcript**: Mock Gong-style sales call text with timestamped speaker turns
  used as the source of opportunity-update evidence.
- **Evidence**: Field-level support containing the transcript timestamp, exact
  quote, and reasoning note for a proposed value.
- **OpportunityUpdateDraft**: Structured Salesforce opportunity update proposal
  containing opportunity identifiers, stage, amount, close date, next step,
  MEDDPICC fields, risks, last-touch summary, confidence, and evidence.
- **NextStep**: Proposed follow-up action with description, owner, and due date
  when each value is supported by transcript evidence.
- **MEDDPICC**: Deal qualification fields covering metrics, economic buyer,
  decision criteria, decision process, paper process, identified pain, champion,
  and competition.
- **AbstainResult**: Structured state explaining why no meaningful opportunity
  update is proposed while preserving the last-touch summary.
- **ReviewAction**: Human review affordance representing Approve, Edit, or
  Reject without performing real CRM writeback.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Rich transcript scenario produces a validated structured
  opportunity update draft with at least one grounded proposed field update.
- **SC-002**: Thin transcript scenario produces an abstain result with zero
  proposed opportunity field updates.
- **SC-003**: 100% of non-empty proposed opportunity fields include timestamped
  quote evidence and a reasoning note.
- **SC-004**: 100% of demo outputs conform to the documented output contract
  before UI review.
- **SC-005**: UI displays both rich draft and thin abstain states in a way that a
  reviewer can understand in under five minutes.
- **SC-006**: Approve, Edit, and Reject review affordances are visible for the
  human review flow without performing real CRM writeback.
- **SC-007**: Local run instructions enable a reviewer to start the demo and
  inspect both transcript scenarios in under five minutes.
- **SC-008**: README or write-up covers framework choice, rejected alternative,
  model selection, production evaluation harness, expected failure modes,
  mitigations, production UI improvements, and intentionally cut scope.

## Assumptions

- The Account Executive is the primary user for reviewing the generated draft or
  abstain state.
- The take-home reviewer is the secondary user for running and assessing the
  local demo.
- The two transcript fixtures are sufficient for the required demo behavior.
- Missing or weak transcript evidence means the corresponding opportunity field
  remains unset rather than inferred.
- The thin transcript still represents a customer touch and therefore needs a
  last-touch summary even when no opportunity update is proposed.
- Review affordances do not need to persist changes or call external systems for
  this take-home.
- Optional hosted UI deployment is acceptable only as a supplement to the local
  demo.
