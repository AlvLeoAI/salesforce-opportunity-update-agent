import { useState } from "react";
import AbstainReview from "./AbstainReview";
import AgentTrace from "./AgentTrace";
import DraftReview from "./DraftReview";
import WarningsBanner from "./WarningsBanner";
import type { AgentRunOutput } from "../types";

const API_BASE = (import.meta.env.VITE_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

const PLACEHOLDER = `Paste a sales call transcript here.

Format: [MM:SS] Speaker: Message

Example:
[00:02] AE: Thanks for the time, Sarah.
[00:10] Sarah: Happy to chat. We're evaluating two vendors and need to decide by end of quarter.`;

type Status =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "success"; output: AgentRunOutput };

export default function LiveAnalyze() {
  const [transcript, setTranscript] = useState("");
  const [status, setStatus] = useState<Status>({ kind: "idle" });

  const submit = async () => {
    if (!transcript.trim()) {
      setStatus({ kind: "error", message: "Paste a transcript before analyzing." });
      return;
    }
    setStatus({ kind: "loading" });
    try {
      const response = await fetch(`${API_BASE}/api/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ transcript })
      });
      if (!response.ok) {
        const detail = await safeDetail(response);
        setStatus({
          kind: "error",
          message: `Analysis failed (${response.status}): ${detail}`
        });
        return;
      }
      const output = (await response.json()) as AgentRunOutput;
      setStatus({ kind: "success", output });
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setStatus({
        kind: "error",
        message: `Could not reach the agent server at ${API_BASE}. Start it with: \`cd backend && uvicorn server:app --port 8000\` (${message})`
      });
    }
  };

  const reset = () => {
    setStatus({ kind: "idle" });
  };

  if (status.kind === "success") {
    const { output } = status;
    const result = output.result;
    return (
      <div className="review-stack">
        <div className="live-toolbar">
          <span className="eyebrow">Live result</span>
          <button type="button" onClick={reset} className="secondary">
            Analyze another
          </button>
        </div>
        <WarningsBanner warnings={result.warnings} />
        {result.result_type === "draft" ? (
          <DraftReview result={result} />
        ) : (
          <AbstainReview result={result} />
        )}
        <AgentTrace trace={output.trace} />
      </div>
    );
  }

  return (
    <section className="panel live-panel">
      <h3>Try your own transcript</h3>
      <p className="muted">
        The agent will extract MEDDPICC fields, identify next steps, and decide whether to propose a
        Salesforce update. If <code>OPENAI_API_KEY</code> is not set on the backend, the agent runs
        in simulator mode and the warning banner will say so.
      </p>
      <textarea
        className="live-textarea"
        rows={14}
        placeholder={PLACEHOLDER}
        value={transcript}
        onChange={(event) => setTranscript(event.target.value)}
        disabled={status.kind === "loading"}
      />
      <div className="live-actions">
        <button
          type="button"
          className="primary"
          onClick={submit}
          disabled={status.kind === "loading"}
        >
          {status.kind === "loading" ? "Analyzing…" : "Analyze"}
        </button>
        {status.kind === "loading" && (
          <span className="muted">Agent is processing the transcript. This can take 10–20s.</span>
        )}
      </div>
      {status.kind === "error" && (
        <div className="warnings-banner error" role="alert">
          <strong>Could not analyze transcript</strong>
          <p>{status.message}</p>
        </div>
      )}
    </section>
  );
}

async function safeDetail(response: Response): Promise<string> {
  try {
    const data = await response.json();
    if (typeof data?.detail === "string") return data.detail;
    return JSON.stringify(data);
  } catch {
    return response.statusText || "unknown error";
  }
}
