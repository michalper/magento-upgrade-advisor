"""Runs `advisor.explain` for every (fixture, model) pair and scores each
result for faithfulness — the thing this harness actually exists to measure,
not response "quality" in some subjective sense."""

from __future__ import annotations

import time
from dataclasses import dataclass

from .. import faithfulness
from ..advisor import MessagesClient, explain
from ..faithfulness import FaithfulnessResult
from ..models import PlanView


@dataclass(frozen=True)
class EvalResult:
    fixture_name: str
    model: str
    faithfulness: FaithfulnessResult
    input_tokens: int
    output_tokens: int
    latency_seconds: float
    error: str | None


def run(
    fixtures: dict[str, PlanView],
    models: list[str],
    client: MessagesClient,
) -> list[EvalResult]:
    results = []
    for name, plan_view in fixtures.items():
        for model in models:
            start = time.monotonic()
            faith = FaithfulnessResult(
                ok=False, missing_indices=(), fabricated_indices=(), duplicate_indices=()
            )
            input_tokens, output_tokens, error = 0, 0, None
            try:
                remediation = explain(plan_view, client=client, model=model)
                faith = faithfulness.check(plan_view, remediation)
                input_tokens = remediation.input_tokens
                output_tokens = remediation.output_tokens
            except Exception as exc:
                error = str(exc)
            results.append(
                EvalResult(
                    fixture_name=name,
                    model=model,
                    faithfulness=faith,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    latency_seconds=time.monotonic() - start,
                    error=error,
                )
            )
    return results
