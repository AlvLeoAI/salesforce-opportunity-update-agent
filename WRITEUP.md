# Salesforce Opportunity Update Agent — Write-up

## Framework choice

I built the agent as a hand-rolled tool-calling loop on the OpenAI SDK (`backend/agent/agent_loop.py`). The model owns three tools: `read_transcript(query)`, `check_signal_coverage(extracted_signals)`, and `validate_draft(draft)`. The loop runs until the model returns a final assistant message with no tool calls; that message is the final JSON, parsed back into Pydantic.

**Rejected alternative: LangGraph.** The whole decision graph is `extract → coverage check → (draft|abstain) → validate`. Wrapping that in a graph runtime adds state machine vocabulary without solving anything I don't already solve in 70 lines of Python. The only branching point — draft vs. abstain — is owned by the `check_signal_coverage` tool's recommendation, which the model honors. A framework would push this decision into graph edges and obscure where the agent actually decides. For a 4-step workflow with one fork, the loop *is* the agent.

## Model selection

Single model (`gpt-4o`, override via `OPENAI_MODEL`) for the whole loop. Two reasons against splitting: (1) the work is one decision (draft vs. abstain) plus structured composition — a smaller extractor model would still need the larger model to judge coverage, so I'd be paying two round-trips for one judgment. (2) `gpt-4o` already handles the function-calling structure reliably; I haven't seen a failure mode that a separate "judge" call would have caught. I'd revisit this only if production cost forced it — at which point I'd cache the read_transcript outputs (transcripts are static within a run) before splitting models.

## Eval harness

I'd run a golden set of four transcript classes — rich, thin, ambiguous (some signal, contradictory close dates), and contradictory (champion says one thing, AE says another). Per-run metrics:

- **Field-level extraction accuracy** — for each rich transcript, did it find the right champion / economic buyer / amount / close date / competition?
- **Abstain precision/recall** — does it abstain on thin calls and *not* abstain on rich ones?
- **Evidence grounding** — does every cited quote literally appear in the transcript? (`schema_validator.validate_evidence_coverage` already enforces this at runtime — in the harness I'd run it as a hard gate.)
- **Schema compliance rate** — does `validate_draft` pass first try, or how many iterations did the model need?
- **Confidence calibration** — for runs the human reviewer rejects, what was the agent's confidence? Should track downward.

The 9 tests under `backend/tests/` cover the fixed-mode equivalents today: rich produces a draft with the expected fields, thin abstains, every populated field has evidence, the trace contains the right tool calls. Production would extend this to the four-class golden set and run on every model bump or prompt change.

## Failure modes and mitigations

| Failure mode | Mitigation |
|---|---|
| Hallucinated quote — model invents a timestamp/quote that isn't in the transcript | `schema_validator.validate_evidence_coverage` does a substring check of every cited quote against the raw transcript text. The orchestrator raises `EvidenceCoverageError` and the run fails. |
| Over-extraction from thin calls — model reads pricing into "let's catch up next week" | `check_signal_coverage` enforces a coverage threshold (≥0.4 for draft, <0.2 for abstain). The model is explicitly told to honor the recommendation. |
| Schema drift — Salesforce shape changes | Pydantic models in `agent/models.py` are the single source of truth. The `validate_draft` tool surfaces errors back into the loop so the model can self-correct, rather than producing a malformed final answer. |
| Confidence theater — model says 0.95 on weak evidence | In simulator mode, confidence is derived from `coverage_ratio`, not asserted. In production I'd post-process the model's confidence the same way (clamp to coverage ratio + small bonus for full validation pass). |
| Model returns prose around JSON | `orchestrator._strip_markdown_fences` handles ```json fences; non-JSON output raises `OrchestrationError` rather than silently corrupting the run. |

## Production UI

The static demo intentionally skips most of what a production AE surface would need. The next set of additions:

- **Diff view against current Salesforce values** — show old → new side by side so the AE sees what's actually changing, not the proposed end state in isolation.
- **Per-field confidence indicators** — overall confidence is too coarse; AEs care which specific fields to question.
- **Inline transcript player** — clicking a timestamp scrolls a side-panel transcript and (eventually) seeks the call recording.
- **Audit log** — who approved, when, what they edited before approval; needed for any real CRM writeback.
- **Batch mode** — process the day's calls and surface only the ones below a confidence floor or with risk flags. The 95% case should not require human review.

## What I cut

Real Salesforce write-back, real Gong ingestion, auth, persistence, RAG/cross-call context, multi-model routing, streaming agent updates, and any heavy framework. The frame I worked to: a forward-deploy engineer should be able to read the four files in `agent/` and understand exactly where every decision is made and where every value comes from. Adding any of the above before that bar is met would have hidden the decision-making, not extended it.

## Beyond the spec: live mode

The spec only required two static scenarios rendered from precomputed JSON, and my original write-up rejected adding a backend API. After the static UI was working I reversed that one decision and added a thin FastAPI server (`backend/server.py`) plus a "Try your own transcript" tab so the demo is exercisable on arbitrary input — paste any `[MM:SS] Speaker: text` transcript and the same agent loop runs end-to-end.

Two things made me comfortable doing this without breaking the original framing:

1. **No new agent logic.** The server exposes one endpoint that calls `orchestrator.run_live_transcript`, which is a fifteen-line wrapper around the same `_run_agent_for_transcript` private function that `run_scenario` uses. Same loop, same tools, same schema validator. The transport changed; the agent did not. If the FastAPI layer were deleted tomorrow, no agent behavior would be lost.
2. **The static demo still stands alone.** The two original tabs read static JSON and need no backend. The third tab degrades to a friendly error when the API is not running. Reviewers grading against the original spec see exactly the artifact the spec asked for; reviewers who want to poke at it can.

The cost was small (one new module, one new component, an enum value, a parser refactor) because the original code already separated parsing from orchestration from validation. The benefit, for a take-home, is that "does the agent actually work on input it hasn't seen?" stops being a question I have to answer in writing.
