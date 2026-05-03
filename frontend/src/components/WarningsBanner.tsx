type Props = {
  warnings: string[];
};

export default function WarningsBanner({ warnings }: Props) {
  if (warnings.length === 0) return null;

  const isDemo = warnings.some((w) => w.toLowerCase().includes("simulator_demo"));

  return (
    <aside className={`warnings-banner ${isDemo ? "demo" : ""}`} role="alert">
      <strong>{isDemo ? "Demo mode" : "Notice"}</strong>
      <ul>
        {warnings.map((w, i) => (
          <li key={i}>{w}</li>
        ))}
      </ul>
    </aside>
  );
}
