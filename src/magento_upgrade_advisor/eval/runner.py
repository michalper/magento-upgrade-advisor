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

_EMPTY_FAITHFULNESS = FaithfulnessResult(
    ok=False, missing_indices=(), fabricated_indices=(), duplicate_indices=()
)


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
            try:
                remediation = explain(plan_view, client=client, model=model)
                elapsed = time.monotonic() - start
                faith = faithfulness.check(plan_view, remediation)
                results.append(
                    EvalResult(
                        fixture_name=name,
                        model=model,
                        faithfulness=faith,
                        input_tokens=remediation.input_tokens,
                        output_tokens=remediation.output_tokens,
                        latency_seconds=elapsed,
                        error=None,
                    )
                )
            except Exception as exc:
                elapsed = time.monotonic() - start
                results.append(
                    EvalResult(
                        fixture_name=name,
                        model=model,
                        faithfulness=_EMPTY_FAITHFULNESS,
                        input_tokens=0,
                        output_tokens=0,
                        latency_seconds=elapsed,
                        error=str(exc),
                    )
                )
    return results
