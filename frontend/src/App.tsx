import { useMemo, useState } from "react";
import AbstainReview from "./components/AbstainReview";
import AgentTrace from "./components/AgentTrace";
import DraftReview from "./components/DraftReview";
import LiveAnalyze from "./components/LiveAnalyze";
import ReviewActions from "./components/ReviewActions";
import WarningsBanner from "./components/WarningsBanner";
import { scenarios } from "./data/results";
import type { ScenarioId } from "./types";

export default function App() {
  const [selectedScenario, setSelectedScenario] = useState<ScenarioId>("rich_signal");
  const activeScenario = useMemo(
    () => scenarios.find((scenario) => scenario.id === selectedScenario) ?? scenarios[0],
    [selectedScenario]
  );

  return (
    <main className="app-shell">
      <section className="top-bar">
        <div>
          <span className="eyebrow">Revenue AI review</span>
          <h1>Opportunity update review</h1>
        </div>
        <ReviewActions />
      </section>

      <nav className="scenario-tabs" aria-label="Transcript scenarios">
        {scenarios.map((scenario) => (
          <button
            key={scenario.id}
            type="button"
            className={`${scenario.id === selectedScenario ? "active" : ""}${
              scenario.mode === "live" ? " interactive" : ""
            }`}
            onClick={() => setSelectedScenario(scenario.id)}
          >
            <span>{scenario.label}</span>
            <small>{scenario.summary}</small>
          </button>
        ))}
      </nav>

      {activeScenario.mode === "live" ? (
        <LiveAnalyze />
      ) : (
        <StaticReview output={activeScenario.output} />
      )}
    </main>
  );
}

function StaticReview({ output }: { output: import("./types").AgentRunOutput }) {
  const result = output.result;
  return (
    <>
      <WarningsBanner warnings={result.warnings} />
      {result.result_type === "draft" ? (
        <DraftReview result={result} />
      ) : (
        <AbstainReview result={result} />
      )}
      <AgentTrace trace={output.trace} />
    </>
  );
}
