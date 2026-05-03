import type { Evidence } from "../types";

type Props = {
  evidence?: Evidence[];
};

export default function EvidenceDisclosure({ evidence = [] }: Props) {
  if (evidence.length === 0) {
    return <span className="muted">No evidence attached</span>;
  }

  return (
    <details className="evidence">
      <summary>{evidence.length === 1 ? "Evidence" : `${evidence.length} evidence items`}</summary>
      <div className="evidence-list">
        {evidence.map((item, index) => (
          <article className="evidence-item" key={`${item.timestamp}-${index}`}>
            <div className="timestamp">{item.timestamp}</div>
            <blockquote>{item.quote}</blockquote>
            <p>{item.reasoning}</p>
          </article>
        ))}
      </div>
    </details>
  );
}
