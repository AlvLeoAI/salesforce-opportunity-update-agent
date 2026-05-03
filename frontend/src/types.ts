export type ScenarioId = "rich_signal" | "thin_signal" | "live";

export type Evidence = {
  timestamp: string;
  quote: string;
  reasoning: string;
};

export type EvidenceByField = Record<string, Evidence[]>;

export type NextStep = {
  description: string | null;
  owner: string | null;
  due_date: string | null;
};

export type Meddpicc = {
  metrics: string | null;
  economic_buyer: string | null;
  decision_criteria: string | null;
  decision_process: string | null;
  paper_process: string | null;
  identify_pain: string | null;
  champion: string | null;
  competition: string | null;
};

export type OpportunityUpdateDraft = {
  result_type: "draft";
  opportunity_id: string;
  stage: string;
  amount_usd: number | null;
  close_date: string | null;
  next_step: NextStep;
  meddpicc: Meddpicc;
  risks: string[];
  last_touch_summary: string;
  confidence: number;
  evidence_by_field: EvidenceByField;
  warnings: string[];
};

export type AbstainResult = {
  result_type: "abstain";
  opportunity_id: string | null;
  message: string;
  last_touch_summary: string;
  reason: string;
  confidence: number;
  signals_considered: string[];
  evidence_by_field?: EvidenceByField;
  warnings: string[];
};

export type AgentResult = OpportunityUpdateDraft | AbstainResult;

export type AgentRunOutput = {
  schema_version: string;
  scenario_id: ScenarioId;
  generated_at: string;
  transcript_path: string;
  result: AgentResult;
  trace: string[];
};

export type ScenarioOption =
  | {
      id: "rich_signal" | "thin_signal";
      label: string;
      summary: string;
      mode: "static";
      output: AgentRunOutput;
    }
  | {
      id: "live";
      label: string;
      summary: string;
      mode: "live";
    };
