from __future__ import annotations

import argparse
import sys
from pathlib import Path

from mcp_magento_audit.composer import ProjectError, load_project
from mcp_magento_audit.upgrade_plan import build as build_upgrade_plan

from . import faithfulness
from .advisor import explain
from .client import default_client
from .eval.fixtures import FIXTURES
from .eval.report import render_markdown
from .eval.runner import run as run_eval
from .models import from_upgrade_plan

DEFAULT_MODELS = ["claude-haiku-5-5", "claude-sonnet-5-5"]


def _cmd_explain(args: argparse.Namespace) -> int:
    try:
        project = load_project(args.path)
    except ProjectError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    plan = build_upgrade_plan(
        project, target_php=args.target_php, target_magento=args.target_magento
    )
    plan_view = from_upgrade_plan(plan)

    remediation = explain(plan_view, client=default_client(), model=args.model)
    result = faithfulness.check(plan_view, remediation)

    print(f"# {remediation.summary}\n")
    for step in sorted(remediation.steps, key=lambda s: s.priority):
        blocker = plan_view.blockers[step.blocker_index]
        print(f"{step.priority}. [{blocker.source}] {blocker.description} — {step.rationale}")

    if not result.ok:
        print("\n!! faithfulness check FAILED", file=sys.stderr)
        if result.missing_indices:
            print(f"   missing: {list(result.missing_indices)}", file=sys.stderr)
        if result.fabricated_indices:
            print(f"   fabricated: {list(result.fabricated_indices)}", file=sys.stderr)
        if result.duplicate_indices:
            print(f"   duplicate: {list(result.duplicate_indices)}", file=sys.stderr)
        return 2
    return 0


def _cmd_eval(args: argparse.Namespace) -> int:
    models = args.models.split(",") if args.models else DEFAULT_MODELS
    results = run_eval(FIXTURES, models, default_client())
    report = render_markdown(results)
    if args.out:
        args.out.write_text(report + "\n")
        print(f"wrote {args.out}")
    else:
        print(report)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="magento-upgrade-advisor")
    sub = parser.add_subparsers(dest="command", required=True)

    explain_p = sub.add_parser("explain", help="Explain one project's upgrade plan")
    explain_p.add_argument("path", help="Path to the Magento project root")
    explain_p.add_argument("--target-php", required=True)
    explain_p.add_argument("--target-magento", required=True)
    explain_p.add_argument("--model", default=DEFAULT_MODELS[-1])
    explain_p.set_defaults(func=_cmd_explain)

    eval_p = sub.add_parser("eval", help="Run the faithfulness/latency/cost eval harness")
    eval_p.add_argument("--models", help="Comma-separated model ids (default: haiku + sonnet)")
    eval_p.add_argument("--out", type=Path, default=None)
    eval_p.set_defaults(func=_cmd_eval)

    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
