# Output JSON Contract

## Top-Level Artifact

Each generated file must match this shape:

```json
{
  "schema_version": "1.0",
  "scenario_id": "rich_signal",
  "generated_at": "2026-04-28T00:00:00Z",
  "transcript_path": "backend/data/transcripts/rich_signal.txt",
  "result": {},
  "trace": []
}
```

## Draft Result

```json
{
  "result_type": "draft",
  "opportunity_id": "OPP-2026-TASTEWISE-001",
  "stage": "negotiation",
  "amount_usd": 120000,
  "close_date": "2026-10-01",
  "next_step": {
    "description": "Send revised annual quote tonight and stage-gate one-pager by Friday; meeting next Tuesday with Ben, Priya, and CMO.",
    "owner": "AE",
    "due_date": "2026-05-05"
  },
  "meddpicc": {
    "metrics": null,
    "economic_buyer": "CMO (identified as the signer)",
    "decision_criteria": "Speed-to-insight is #1; stage-gate integration is #2.",
    "decision_process": "Ben (Procurement) validates pricing; CMO is the final signer.",
    "paper_process": "Annual billing required by procurement (not quarterly).",
    "identify_pain": null,
    "champion": "Priya — coordinating procurement and the CMO.",
    "competition": "Spoonshot — aggressive pricing, lightweight demo."
  },
  "risks": [
    "Timeline slipped from Q3 to early Q4 after the 2027 portfolio review moved.",
    "Competitive threat from Spoonshot on pricing."
  ],
  "last_touch_summary": "Priya confirmed $120k with annual billing. Close pushed to early Q4. Next Tuesday meeting with Ben, Priya, and CMO.",
  "confidence": 0.88,
  "evidence_by_field": {
    "stage": [
      {
        "timestamp": "00:18",
        "quote": "Yeah — Ben's in the next call. He's fine with the $120k range but wants annual not quarterly.",
        "reasoning": "Procurement engaged on pricing terms — characteristic of negotiation."
      }
    ]
  },
  "warnings": []
}
```

## Abstain Result

```json
{
  "result_type": "abstain",
  "opportunity_id": null,
  "message": "No meaningful update proposed",
  "last_touch_summary": "A brief touch occurred, but no deal details changed.",
  "reason": "Transcript did not contain concrete opportunity updates.",
  "confidence": 0.9,
  "signals_considered": ["relationship_touch"],
  "warnings": []
}
```

## Evidence Coverage Rule

For a draft result, every non-empty proposed update field must have at least one
entry in `evidence_by_field`. Field paths use dot notation:

- `stage`
- `amount_usd`
- `close_date`
- `next_step.description`
- `next_step.owner`
- `next_step.due_date`
- `meddpicc.metrics`
- `meddpicc.economic_buyer`
- `meddpicc.decision_criteria`
- `meddpicc.decision_process`
- `meddpicc.paper_process`
- `meddpicc.identify_pain`
- `meddpicc.champion`
- `meddpicc.competition`
- `risks[0]`

Each evidence item requires:

- `timestamp`: timestamp from the transcript
- `quote`: exact transcript quote
- `reasoning`: short reason the quote supports the field

## UI Consumption Rule

The UI must treat `result.result_type` as the rendering discriminator:

- `draft`: render opportunity update fields, confidence, risks, evidence, and
  review buttons.
- `abstain`: render "No meaningful update proposed", reason, last-touch
  summary, and review buttons.
