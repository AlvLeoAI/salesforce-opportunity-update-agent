import ConfidenceRisk from "./ConfidenceRisk";
import EvidenceDisclosure from "./EvidenceDisclosure";
import type { AbstainResult } from "../types";

type Props = {
  result: AbstainResult;
};

export default function AbstainReview({ result }: Props) {
  return (
    <div className="review-stack">
      <header className="review-header">
        <div>
          <span className="eyebrow">Abstain result</span>
          <h2>{result.message}</h2>
        </div>
        <span className="result-pill neutral">No update</span>
      </header>

      <ConfidenceRisk confidence={result.confidence} />

      <section className="panel abstain-panel">
        <h3>Last touch summary</h3>
        <p>{result.last_touch_summary}</p>
        <EvidenceDisclosure evidence={result.evidence_by_field?.last_touch_summary} />
      </section>

      <section className="panel">
        <h3>Reason</h3>
        <p>{result.reason}</p>
      </section>

      <section className="panel">
        <h3>Signals considered</h3>
        <div className="chips">
          {result.signals_considered.map((signal) => (
            <span key={signal}>{signal.replaceAll("_", " ")}</span>
          ))}
        </div>
      </section>
    </div>
  );
}
