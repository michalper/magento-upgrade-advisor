"""Renders `EvalResult`s as a markdown table plus a per-model pass-rate
summary — the thing that actually goes in `docs/eval-report.md`."""

from __future__ import annotations

from collections import defaultdict

from .runner import EvalResult


def render_markdown(results: list[EvalResult]) -> str:
    lines = [
        "| fixture | model | faithful | missing | fabricated | duplicate "
        "| in_tok | out_tok | latency_s | error |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        faithful = "yes" if r.faithfulness.ok else "no"
        lines.append(
            f"| {r.fixture_name} | {r.model} | {faithful} "
            f"| {list(r.faithfulness.missing_indices)} "
            f"| {list(r.faithfulness.fabricated_indices)} "
            f"| {list(r.faithfulness.duplicate_indices)} "
            f"| {r.input_tokens} | {r.output_tokens} | {r.latency_seconds:.2f} "
            f"| {r.error or ''} |"
        )

    lines.append("")
    lines.append("## Pass rate by model")
    lines.append("")
    lines.append("| model | faithful / total |")
    lines.append("|---|---|")
    totals: dict[str, int] = defaultdict(int)
    passed: dict[str, int] = defaultdict(int)
    for r in results:
        totals[r.model] += 1
        if r.faithfulness.ok:
            passed[r.model] += 1
    lines.extend(f"| {model} | {passed[model]} / {totals[model]} |" for model in sorted(totals))

    return "\n".join(lines)
