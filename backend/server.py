"""FastAPI server exposing the agent for live transcript analysis.

This is a thin HTTP wrapper around ``orchestrator.run_live_transcript``. It
reuses the same agent loop, tools, and schema validation as the static CLI
demo (``run_agent.py``); the only difference is that the transcript is
supplied in the request body and the result is returned as JSON instead of
being written to disk.

Run locally (from the ``backend/`` directory so ``agent`` resolves)::

    cd backend && uvicorn server:app --reload --port 8000

The frontend (Vite dev server on :5173) calls ``POST /api/analyze`` with
``{"transcript": "..."}``.
"""
from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agent.agent_loop import AgentLoopError
from agent.models import AgentRunOutput
from agent.orchestrator import OrchestrationError, run_live_transcript
from agent.tools.schema_validator import EvidenceCoverageError, SchemaValidationError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env", override=False)

logger = logging.getLogger(__name__)

ANALYZE_TIMEOUT_SECONDS = 60.0

DEFAULT_DEV_ORIGINS = ["http://localhost:5173", "http://localhost:3000"]


def _cors_config() -> dict[str, object]:
    """Resolve CORS settings from FRONTEND_URL.

    - Unset: dev defaults (localhost:5173, localhost:3000).
    - "*": allow any origin (no credentials).
    - Comma-separated list: explicit origins (e.g. the Vercel URL).
    """
    raw = os.getenv("FRONTEND_URL", "").strip()
    if not raw:
        return {"allow_origins": DEFAULT_DEV_ORIGINS}
    if raw == "*":
        return {"allow_origin_regex": ".*"}
    origins = [item.strip() for item in raw.split(",") if item.strip()]
    return {"allow_origins": origins or DEFAULT_DEV_ORIGINS}


app = FastAPI(title="Salesforce Opportunity Update Agent")

app.add_middleware(
    CORSMiddleware,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
    **_cors_config(),
)


class AnalyzeRequest(BaseModel):
    transcript: str = Field(min_length=1)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/analyze", response_model=AgentRunOutput)
async def analyze_transcript(request: AnalyzeRequest) -> AgentRunOutput:
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(run_live_transcript, request.transcript, load_env=False),
            timeout=ANALYZE_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError as exc:
        raise HTTPException(
            status_code=504,
            detail=f"agent did not return within {int(ANALYZE_TIMEOUT_SECONDS)}s",
        ) from exc
    except OrchestrationError as exc:
        raise HTTPException(status_code=422, detail=f"orchestration error: {exc}") from exc
    except AgentLoopError as exc:
        raise HTTPException(status_code=502, detail=f"agent loop error: {exc}") from exc
    except EvidenceCoverageError as exc:
        raise HTTPException(status_code=422, detail=f"evidence coverage error: {exc}") from exc
    except SchemaValidationError as exc:
        raise HTTPException(status_code=422, detail=f"validation error: {exc}") from exc
    except Exception as exc:
        logger.exception("unexpected error during analyze")
        raise HTTPException(status_code=500, detail=f"unexpected error: {exc}") from exc
