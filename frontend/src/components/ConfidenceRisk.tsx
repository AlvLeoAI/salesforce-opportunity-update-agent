type Props = {
  confidence: number;
  risks?: string[];
};

export default function ConfidenceRisk({ confidence, risks = [] }: Props) {
  const percent = Math.round(confidence * 100);
  const confidenceClass =
    confidence >= 0.8 ? "good" : confidence >= 0.55 ? "watch" : "low";

  return (
    <section className="status-grid" aria-label="Confidence and risks">
      <div className={`status-panel ${confidenceClass}`}>
        <span className="eyebrow">Confidence</span>
        <strong>{percent}%</strong>
        <div className="meter" aria-hidden="true">
          <span style={{ width: `${percent}%` }} />
        </div>
      </div>
      <div className={risks.length > 0 ? "status-panel risk" : "status-panel neutral"}>
        <span className="eyebrow">Risk</span>
        {risks.length > 0 ? (
          <ul>
            {risks.map((risk, index) => (
              <li key={`${risk}-${index}`}>{risk}</li>
            ))}
          </ul>
        ) : (
          <strong>No cited deal risk</strong>
        )}
      </div>
    </section>
  );
}
