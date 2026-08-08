"""CLI entrypoint: `python -m eval_harness.cli run [options]`."""

import argparse
import sys
from pathlib import Path

from eval_harness.report import print_terminal_summary, write_html, write_json
from eval_harness.runner import run_eval


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="eval_harness", description="LLM output evaluation harness."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser(
        "run", help="Run the golden dataset against a provider."
    )
    run_parser.add_argument(
        "--dataset", default="data/golden_dataset.yaml", help="Path to the golden dataset YAML."
    )
    run_parser.add_argument(
        "--provider", default="mock", choices=["mock", "anthropic"], help="Which provider to run against."
    )
    run_parser.add_argument(
        "--out-dir", default="reports", help="Directory to write results.json / report.html into."
    )
    run_parser.add_argument(
        "--fail-under",
        type=float,
        default=None,
        help="Exit non-zero if pass rate is below this threshold (0-1). Omit to never gate.",
    )

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        try:
            summary = run_eval(args.dataset, args.provider)
        except Exception as exc:  # surface config/provider errors as a clean CLI failure
            print(f"Error: {exc}", file=sys.stderr)
            return 2

        out_dir = Path(args.out_dir)
        json_path = write_json(summary, out_dir)
        html_path = write_html(summary, out_dir)

        print_terminal_summary(summary)
        print(f"\nJSON report: {json_path}")
        print(f"HTML report: {html_path}")

        if args.fail_under is not None and summary.pass_rate < args.fail_under:
            print(
                f"\nFAIL: pass rate {summary.pass_rate:.1%} is below threshold "
                f"{args.fail_under:.1%}",
                file=sys.stderr,
            )
            return 1
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
