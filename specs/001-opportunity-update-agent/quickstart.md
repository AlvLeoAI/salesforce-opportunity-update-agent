# Quickstart: Salesforce Opportunity Update Agent

## Prerequisites

- Python 3.11+
- Node.js 20+ and npm
- Optional OpenAI API key for live structured-output extraction

## 1. Configure Backend

```bash
cd /home/alvaro/Projects/Portfolio/salesforce-opportunity-update-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
```

Add `OPENAI_API_KEY` to `backend/.env` for live model extraction. Without it, fixture-specific demo fallback logic is used and marked in output warnings.

## 2. Generate Demo Outputs

```bash
python3 backend/run_agent.py --all
```

Expected files:

```text
backend/outputs/rich_signal_output.json
backend/outputs/thin_signal_output.json
```

Expected behavior:

- Rich transcript writes a `draft` result with proposed field updates and
  timestamped evidence.
- Thin transcript writes an `abstain` result with "No meaningful update
  proposed", last-touch summary, and evidence for that summary.

## 3. Run Backend Validation

```bash
python3 -m pytest backend/tests
```

Required checks:

- Pydantic schema validation passes.
- Rich transcript produces a proposed update.
- Thin transcript abstains.
- Every populated draft field has timestamp, quote, and reasoning evidence.
- `--all` writes both output files.

## 4. Refresh Static UI Data

```bash
cp backend/outputs/rich_signal_output.json frontend/src/data/rich_signal_output.json
cp backend/outputs/thin_signal_output.json frontend/src/data/thin_signal_output.json
```

## 5. Run UI

```bash
cd frontend
npm install
npm run build
npm run dev
```

Open the Vite URL shown in the terminal. The UI should render both precomputed
JSON states without a backend API.

## 6. Demo Path Under 5 Minutes

1. Run `python3 backend/run_agent.py --scenario rich_signal --pretty`.
2. Show rich draft fields and evidence in JSON.
3. Run `python3 backend/run_agent.py --scenario thin_signal --pretty`.
4. Show abstain state and last-touch summary evidence in JSON.
5. Run `cd frontend && npm run dev`.
6. Show rich draft review, thin abstain review, evidence disclosures, and review buttons.
7. Point to README/WRITEUP sections for evaluation, failure modes, mitigations,
   production UI improvements, and intentionally cut scope.
