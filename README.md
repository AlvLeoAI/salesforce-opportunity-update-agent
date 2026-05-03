# Salesforce Opportunity Update Agent

Local-first Revenue AI demo that converts mock Gong-style sales call transcripts into reviewable Salesforce opportunity update artifacts. It covers two scenarios:

- `rich_signal`: produces a structured opportunity update draft with field-level evidence.
- `thin_signal`: produces a typed abstain result with "No meaningful update proposed" and a last-touch summary.

The UI is an Account Executive review surface with two static demo tabs (the rubric scenarios) and a third "Try your own transcript" tab that runs the full agent loop against pasted input.

The static tabs work without any backend. The third tab calls the deployed API to run the agent on arbitrary transcripts; if the backend is cold or unreachable it shows a friendly error and the static demo keeps working.

## Architecture

```text
backend/data/transcripts/*.txt
  -> transcript_reader (parses turns)
  -> agent_loop (LLM tool-calling: read_transcript, check_signal_coverage, validate_draft)
  -> schema_validator (evidence-in-transcript check, trace anchors)
  -> backend/outputs/*.json
  -> frontend/src/data/*.json
  -> Vite React review UI
```

- `backend/agent/models.py`: Pydantic models for transcript turns, evidence, drafts, abstain states, and top-level run outputs.
- `backend/agent/agent_loop.py`: tool-calling loop. The model decides which tools to call and whether to draft or abstain based on `check_signal_coverage`'s recommendation.
- `backend/agent/tools/agent_tools.py`: the three LLM-callable tools and their OpenAI function schemas.
- `backend/agent/clients.py`: real OpenAI client and a deterministic simulator for runs without an API key.
- `backend/agent/tools/schema_validator.py`: post-loop validation — every cited evidence quote must exist in the transcript.
- `backend/run_agent.py`: local CLI entrypoint.
- `frontend/`: Vite React TypeScript static UI that imports copied demo JSON fixtures and renders the agent trace.

## Local Setup

Prerequisites: Python 3.11+, Node.js 20+, npm.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp .env.example .env       # then add your OPENAI_API_KEY in .env
cd frontend && npm install && cd ..
```

`.env` is loaded automatically by `backend/run_agent.py` via `python-dotenv`. Without an `OPENAI_API_KEY`, the backend runs a deterministic simulator that drives the same tool functions through a scripted plan — useful for tests and offline review. Simulator outputs carry a prominent `simulator_demo: NO LLM CALLS were made` warning and the UI renders a Demo-mode banner. Set `OPENAI_MODEL` to override the default `gpt-4o`.

## Backend Commands

Run both scenarios:

```bash
python3 backend/run_agent.py --all
```

Run one scenario:

```bash
python3 backend/run_agent.py --scenario rich_signal --pretty
python3 backend/run_agent.py --scenario thin_signal --pretty
```

Run backend validation:

```bash
python3 -m pytest backend/tests
```

Generated JSON outputs:

```text
backend/outputs/rich_signal_output.json
backend/outputs/thin_signal_output.json
```

Inspect them directly:

```bash
sed -n '1,220p' backend/outputs/rich_signal_output.json
sed -n '1,220p' backend/outputs/thin_signal_output.json
```

## Frontend Commands

The frontend reads static copies of the generated backend outputs:

```text
frontend/src/data/rich_signal_output.json
frontend/src/data/thin_signal_output.json
```

If backend outputs are regenerated, refresh the UI fixtures:

```bash
cp backend/outputs/rich_signal_output.json frontend/src/data/rich_signal_output.json
cp backend/outputs/thin_signal_output.json frontend/src/data/thin_signal_output.json
```

Build and run the review UI:

```bash
cd frontend
npm run build
npm run dev
```

The UI shows scenario tabs for the rich draft, thin abstain result, and a "Try your own transcript" tab for live runs (see below). Each tab includes expandable evidence, confidence/risk indicators, and non-functional Approve, Edit, and Reject review affordances.

## Live Mode

The two static tabs cover the rubric scenarios, but a third interactive tab lets a reviewer paste an arbitrary transcript and run the same agent loop end-to-end. This is a thin FastAPI wrapper around the existing orchestrator — no new agent logic, just a transport.

Start the backend API server (run from `backend/` so the `agent` package resolves):

```bash
cd backend && uvicorn server:app --reload --port 8000
```

Start the frontend dev server in another terminal:

```bash
cd frontend && npm run dev
```

Open the "Try your own transcript" tab, paste a transcript in the `[MM:SS] Speaker: text` format, and click Analyze. The result renders through the same `DraftReview` / `AbstainReview` / `AgentTrace` / `WarningsBanner` components as the static tabs — same JSON schema, same validation, same evidence-in-transcript guarantee. Without an `OPENAI_API_KEY`, the request runs through the deterministic simulator and the result includes the `simulator_demo` warning.

The static tabs continue to work without the backend running. The live tab will show a friendly error if it cannot reach `http://localhost:8000`.

## Deployment

The repo is structured so the backend deploys to Railway and the frontend to Vercel as independent services.

### Backend → Railway

1. Push this repo to GitHub and create a new Railway service from it.
2. Railway auto-detects Python from the root `requirements.txt` (which delegates to `backend/requirements.txt`). The `Procfile` runs `cd backend && uvicorn server:app --host 0.0.0.0 --port $PORT`.
3. Set environment variables in the Railway dashboard:
   - `OPENAI_API_KEY` — required for live LLM calls. If unset, the API still responds, but every result carries the `simulator_demo` warning.
   - `FRONTEND_URL` — comma-separated list of allowed CORS origins (e.g. `https://your-app.vercel.app`). Use `*` while you're still wiring things up. Defaults to `http://localhost:5173,http://localhost:3000` if unset.
   - `OPENAI_MODEL` — optional override of the default `gpt-4o`.
4. Railway will expose a public URL like `https://opportunity-agent.up.railway.app`. Hit `/api/health` to verify; it should return `{"status":"ok"}`.

### Frontend → Vercel

1. Create a new Vercel project pointing at the same repo. The `vercel.json` at the root pins the build command to `cd frontend && npm install && npm run build` and the output to `frontend/dist`.
2. Set the project's environment variable:
   - `VITE_API_URL` — the Railway URL from the previous step (e.g. `https://opportunity-agent.up.railway.app`). With this set, the "Try your own transcript" tab POSTs to the deployed backend; without it, the tab points at `http://localhost:8000` and the static tabs still work.
3. After the first Vercel deploy, copy the `*.vercel.app` URL into Railway's `FRONTEND_URL` so CORS allows it (or leave `FRONTEND_URL=*` for an open demo).

`frontend/.env.example` documents the variable for local use.

## Scope Boundaries

This project intentionally does not include real Salesforce writeback, real Gong ingestion, real customer data, database storage, auth, RAG, vector search, fine-tuning, background jobs, LangGraph, CrewAI, or AutoGen. Review buttons are UI affordances only. The optional FastAPI server exists solely as a transport for the existing orchestrator — no business logic lives there.
