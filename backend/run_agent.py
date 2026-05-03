from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pydantic import ValidationError

from agent.agent_loop import AgentLoopError
from agent.models import ScenarioId
from agent.orchestrator import (
    IMPLEMENTED_SCENARIOS,
    OrchestrationError,
    default_output_path,
    run_scenario,
)
from agent.tools.schema_validator import EvidenceCoverageError, SchemaValidationError


EXIT_INPUT_ERROR = 1
EXIT_GENERATION_ERROR = 2
EXIT_VALIDATION_ERROR = 3
EXIT_EVIDENCE_ERROR = 4
EXIT_UNEXPECTED_ERROR = 5


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the local Salesforce opportunity update agent."
    )
    parser.add_argument("--all", action="store_true", help="Run all MVP scenarios.")
    parser.add_argument(
        "--scenario",
        choices=[scenario.value for scenario in IMPLEMENTED_SCENARIOS],
        help="Scenario to run.",
    )
    parser.add_argument("--input", help="Optional transcript path override.")
    parser.add_argument("--output", help="Optional output JSON path override.")
    parser.add_argument(
        "--pretty", action="store_true", help="Write and print pretty JSON output."
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.all and not args.scenario:
        parser.error("provide --scenario rich_signal or --all")
    if args.all and (args.input or args.output):
        parser.error("--input and --output are only supported with --scenario")

    scenarios = IMPLEMENTED_SCENARIOS if args.all else [ScenarioId(args.scenario)]

    try:
        for scenario in scenarios:
            output_path = Path(args.output) if args.output else default_output_path(scenario)
            output = run_scenario(
                scenario,
                input_path=args.input,
                output_path=output_path,
                pretty=args.pretty,
            )
            print(f"{scenario.value}: {output.result.result_type} written to {output_path}")
            if args.pretty:
                print(output.model_dump_json(indent=2))
        print("validation: passed")
    except FileNotFoundError as exc:
        print(f"input error: {exc}", file=sys.stderr)
        return EXIT_INPUT_ERROR
    except AgentLoopError as exc:
        print(f"agent loop error: {exc}", file=sys.stderr)
        return EXIT_GENERATION_ERROR
    except EvidenceCoverageError as exc:
        print(f"evidence coverage error: {exc}", file=sys.stderr)
        return EXIT_EVIDENCE_ERROR
    except (SchemaValidationError, ValidationError) as exc:
        print(f"validation error: {exc}", file=sys.stderr)
        return EXIT_VALIDATION_ERROR
    except (NotImplementedError, OrchestrationError) as exc:
        print(f"orchestration error: {exc}", file=sys.stderr)
        return EXIT_UNEXPECTED_ERROR
    except Exception as exc:
        print(f"unexpected orchestration error: {exc}", file=sys.stderr)
        return EXIT_UNEXPECTED_ERROR

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
