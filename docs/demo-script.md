# Loom Demo Script: Under 5 Minutes

## 0:00-0:30 Context

- "This is a local-first Revenue AI demo for Salesforce opportunity updates."
- "It processes two mock Gong-style transcripts: one rich signal call and one thin signal call."
- "The agent never writes to Salesforce. It produces review artifacts for an AE."

## 0:30-1:20 Backend Rich Transcript Run

```bash
python3 backend/run_agent.py --scenario rich_signal --pretty
```

Show:

- `result_type: "draft"`
- `opportunity_id`
- `stage`, `amount_usd`, `close_date`
- `next_step`
- `meddpicc`
- `risks`
- `confidence`
- `evidence_by_field` with timestamp, quote, and reasoning

Talk track: "The rich call has enough grounded signal, so the agent proposes a structured update. Every populated field must have evidence."

## 1:20-2:00 Backend Thin Transcript Abstain Run

```bash
python3 backend/run_agent.py --scenario thin_signal --pretty
```

Show:

- `result_type: "abstain"`
- `"No meaningful update proposed"`
- `last_touch_summary`
- evidence for `last_touch_summary`
- absence of `stage`, `amount_usd`, `next_step`, `meddpicc`, and `risks`

Talk track: "The thin call is preserved as a customer touch, but it does not fabricate opportunity fields."

## 2:00-2:30 JSON Outputs

```bash
python3 backend/run_agent.py --all
sed -n '1,120p' backend/outputs/rich_signal_output.json
sed -n '1,120p' backend/outputs/thin_signal_output.json
```

Show that both files exist:

- `backend/outputs/rich_signal_output.json`
- `backend/outputs/thin_signal_output.json`

Talk track: "The static UI consumes copied versions of these precomputed outputs from `frontend/src/data/`."

## 2:30-3:45 Frontend Rich Review State

```bash
cd frontend
npm run dev
```

Open the Vite URL. Select `Rich signal update draft`.

Show:

- opportunity ID in the header
- confidence and risk indicators
- opportunity fields
- next step
- MEDDPICC fields
- risks
- last-touch summary
- expandable evidence disclosures
- Approve, Edit, Reject buttons

Talk track: "The UI is optimized for quick AE review. Evidence is visible before any review action."

## 3:45-4:25 Frontend Thin Abstain State

Select `Thin signal abstain state`.

Show:

- "No meaningful update proposed"
- last-touch summary
- evidence disclosure for the summary
- confidence
- signals considered
- no proposed opportunity update fields
- the same review affordances

Talk track: "This is the trust behavior: no update is better than an unsupported CRM change."

## 4:25-5:00 Scope Cuts and Production Thinking

Mention:

- "No real Salesforce, no real Gong, no database, no auth, no RAG, no vector DB, no fine-tuning, no heavy agent framework."
- "Production would add a golden transcript evaluation harness, field precision and recall, evidence citation accuracy, abstention accuracy, observability per tool step, and a real human approval workflow."
- "This demo keeps the core decision path inspectable: transcript to tools to validated JSON to review UI."
