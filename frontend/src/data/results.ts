import richSignalOutput from "./rich_signal_output.json";
import thinSignalOutput from "./thin_signal_output.json";
import type { AgentRunOutput, ScenarioOption } from "../types";

export const scenarios: ScenarioOption[] = [
  {
    id: "rich_signal",
    label: "Rich signal update draft",
    summary: "Draft update with grounded Salesforce fields",
    mode: "static",
    output: richSignalOutput as AgentRunOutput
  },
  {
    id: "thin_signal",
    label: "Thin signal abstain state",
    summary: "No proposed update with last-touch summary",
    mode: "static",
    output: thinSignalOutput as AgentRunOutput
  },
  {
    id: "live",
    label: "Try your own transcript",
    summary: "Paste a sales call transcript and run the agent live",
    mode: "live"
  }
];
