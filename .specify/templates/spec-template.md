# Feature Specification: [FEATURE NAME]

**Feature Branch**: `[###-feature-name]`  
**Created**: [DATE]  
**Status**: Draft  
**Input**: User description: "$ARGUMENTS"

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.
  
  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - [Brief Title] (Priority: P1)

[Describe this user journey in plain language]

**Why this priority**: [Explain the value and why it has this priority level]

**Independent Test**: [Describe how this can be tested independently - e.g., "Can be fully tested by [specific action] and delivers [specific value]"]

**Acceptance Scenarios**:

1. **Given** [initial state], **When** [action], **Then** [expected outcome]
2. **Given** [initial state], **When** [action], **Then** [expected outcome]

---

### User Story 2 - [Brief Title] (Priority: P2)

[Describe this user journey in plain language]

**Why this priority**: [Explain the value and why it has this priority level]

**Independent Test**: [Describe how this can be tested independently]

**Acceptance Scenarios**:

1. **Given** [initial state], **When** [action], **Then** [expected outcome]

---

### User Story 3 - [Brief Title] (Priority: P3)

[Describe this user journey in plain language]

**Why this priority**: [Explain the value and why it has this priority level]

**Independent Test**: [Describe how this can be tested independently]

**Acceptance Scenarios**:

1. **Given** [initial state], **When** [action], **Then** [expected outcome]

---

[Add more user stories as needed, each with an assigned priority]

### Edge Cases

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right edge cases.
-->

- What happens when transcript turns have missing or malformed timestamps?
- How does the system handle contradictory opportunity signals in the same call?
- How does the system handle a transcript with polite conversation but no meaningful sales signal?
- How does the system handle invalid or incomplete structured output from the model?
- How does the system behave when local OpenAI configuration is missing for a demo?

## Requirements *(mandatory)*

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right functional requirements.
-->

### Functional Requirements

- **FR-001**: System MUST load mock Gong-style transcript fixtures.
- **FR-002**: System MUST parse timestamped speaker turns from each transcript.
- **FR-003**: Users MUST be able to review either a generated update draft or an abstain state.
- **FR-004**: System MUST expose evidence for every proposed opportunity field update.
- **FR-005**: System MUST expose validation, model-call, and abstention outcomes in a demo-friendly way.

*Example of marking unclear requirements:*

- **FR-006**: System MUST map transcript signals to Salesforce opportunity fields [NEEDS CLARIFICATION: exact field list not specified].
- **FR-007**: System MUST render the review UI using [NEEDS CLARIFICATION: React or single-file HTML not selected].

### Constitution-Driven Requirements

- **CDR-001**: System MUST process mock Gong-style transcript fixtures locally.
- **CDR-002**: System MUST produce either a validated Salesforce opportunity update draft or a typed abstain/no meaningful update state.
- **CDR-003**: The rich transcript fixture MUST produce a meaningful opportunity update draft.
- **CDR-004**: The thin transcript fixture MUST produce an abstain/no meaningful update state.
- **CDR-005**: Every proposed field update MUST include supporting transcript evidence with quote and timestamp.
- **CDR-006**: Structured output MUST pass Pydantic validation before being rendered by the UI.
- **CDR-007**: UI MUST show evidence and reasoning to the AE and expose Approve, Edit, and Reject review affordances.
- **CDR-008**: System MUST NOT require real Salesforce, real Gong data, database, auth, RAG, vector database, or fine-tuning.
- **CDR-009**: README or write-up MUST document local demo commands, evaluation approach, expected failure modes, mitigations, observability, and intentionally cut scope.

### Key Entities *(include if feature involves data)*

- **Transcript**: Mock Gong-style call record with timestamped speaker turns.
- **Evidence**: Timestamped transcript quote that supports a proposed field update.
- **OpportunityUpdateDraft**: Structured Salesforce opportunity update proposal containing field changes, reasoning, and evidence.
- **AbstainResult**: Structured state explaining why no meaningful opportunity update is proposed.

## Success Criteria *(mandatory)*

<!--
  ACTION REQUIRED: Define measurable success criteria.
  These must be technology-agnostic and measurable.
-->

### Measurable Outcomes

- **SC-001**: Rich transcript demo produces at least one proposed field update with quote and timestamp evidence.
- **SC-002**: Thin transcript demo produces an abstain/no meaningful update state without fabricated field updates.
- **SC-003**: All demo outputs pass Pydantic validation.
- **SC-004**: Reviewer can run the local demo path in under 5 minutes from README instructions.
- **SC-005**: UI renders both rich-update and abstain states with visible reasoning/evidence.

## Assumptions

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right assumptions based on reasonable defaults
  chosen when the feature description did not specify certain details.
-->

- Target reviewer can run local Python commands and open the minimal UI locally.
- Mock transcripts are sufficient for the take-home; no real customer data is used.
- Salesforce writes, Gong ingestion, database storage, auth, RAG, vector search, and fine-tuning are out of scope.
- Approve, Edit, and Reject controls may be non-functional affordances for the demo.
