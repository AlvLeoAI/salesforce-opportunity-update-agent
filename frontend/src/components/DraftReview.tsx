import ConfidenceRisk from "./ConfidenceRisk";
import EvidenceDisclosure from "./EvidenceDisclosure";
import type { EvidenceByField, Meddpicc, NextStep, OpportunityUpdateDraft } from "../types";

type Props = {
  result: OpportunityUpdateDraft;
};

type FieldRow = {
  label: string;
  value: string | number | null | undefined;
  evidencePath: string;
};

const currency = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0
});

const meddpiccLabels: Array<[keyof Meddpicc, string]> = [
  ["metrics", "Metrics"],
  ["economic_buyer", "Economic buyer"],
  ["decision_criteria", "Decision criteria"],
  ["decision_process", "Decision process"],
  ["paper_process", "Paper process"],
  ["identify_pain", "Identified pain"],
  ["champion", "Champion"],
  ["competition", "Competition"]
];

export default function DraftReview({ result }: Props) {
  const topFields: FieldRow[] = [
    { label: "Stage", value: result.stage, evidencePath: "stage" },
    {
      label: "Amount",
      value: result.amount_usd == null ? null : currency.format(result.amount_usd),
      evidencePath: "amount_usd"
    },
    { label: "Close date", value: result.close_date, evidencePath: "close_date" }
  ];

  const nextStepFields = nextStepRows(result.next_step);
  const meddpiccFields = meddpiccRows(result.meddpicc);

  return (
    <div className="review-stack">
      <header className="review-header">
        <div>
          <span className="eyebrow">Salesforce draft</span>
          <h2>{result.opportunity_id}</h2>
        </div>
        <span className="result-pill">Draft</span>
      </header>

      <ConfidenceRisk confidence={result.confidence} risks={result.risks} />

      <section className="panel">
        <h3>Opportunity fields</h3>
        <FieldTable rows={topFields} evidence={result.evidence_by_field} />
      </section>

      <section className="panel">
        <h3>Next step</h3>
        <FieldTable rows={nextStepFields} evidence={result.evidence_by_field} />
      </section>

      <section className="panel">
        <h3>MEDDPICC</h3>
        <FieldTable rows={meddpiccFields} evidence={result.evidence_by_field} />
      </section>

      <section className="panel">
        <h3>Risks</h3>
        {result.risks.length > 0 ? (
          <div className="risk-list">
            {result.risks.map((risk, index) => (
              <div className="field-row" key={`${risk}-${index}`}>
                <div>
                  <span className="field-label">Risk {index + 1}</span>
                  <strong>{risk}</strong>
                </div>
                <EvidenceDisclosure evidence={result.evidence_by_field[`risks[${index}]`]} />
              </div>
            ))}
          </div>
        ) : (
          <p className="muted">No cited deal risk</p>
        )}
      </section>

      <section className="panel">
        <h3>Last touch summary</h3>
        <p>{result.last_touch_summary}</p>
      </section>
    </div>
  );
}

function nextStepRows(nextStep: NextStep): FieldRow[] {
  return [
    {
      label: "Description",
      value: nextStep.description,
      evidencePath: "next_step.description"
    },
    { label: "Owner", value: nextStep.owner, evidencePath: "next_step.owner" },
    { label: "Due date", value: nextStep.due_date, evidencePath: "next_step.due_date" }
  ];
}

function meddpiccRows(meddpicc: Meddpicc): FieldRow[] {
  return meddpiccLabels.map(([field, label]) => ({
    label,
    value: meddpicc[field],
    evidencePath: `meddpicc.${field}`
  }));
}

function FieldTable({
  rows,
  evidence
}: {
  rows: FieldRow[];
  evidence: EvidenceByField;
}) {
  return (
    <div className="field-table">
      {rows.map((row) => (
        <div className="field-row" key={row.evidencePath}>
          <div>
            <span className="field-label">{row.label}</span>
            <strong>{row.value ?? "Not proposed"}</strong>
          </div>
          <EvidenceDisclosure evidence={evidence[row.evidencePath]} />
        </div>
      ))}
    </div>
  );
}
