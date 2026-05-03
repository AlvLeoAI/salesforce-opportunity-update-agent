type Props = {
  trace: string[];
};

export default function AgentTrace({ trace }: Props) {
  if (trace.length === 0) return null;

  return (
    <details className="agent-trace">
      <summary>
        <span className="eyebrow">Agent reasoning</span>
        <strong>{trace.length} steps</strong>
      </summary>
      <ol className="trace-list">
        {trace.map((step, index) => (
          <li key={`${step}-${index}`}>
            <span className="trace-index">{String(index + 1).padStart(2, "0")}</span>
            <code>{step}</code>
          </li>
        ))}
      </ol>
    </details>
  );
}
