"""Programmatic faithfulness check for a `RemediationPlan`.

The model cites blockers by index into the `PlanView.blockers` tuple it was
given, not by re-describing them in free text — that makes faithfulness a
set-equality check on integers, not fuzzy string matching against a
paraphrase. Checkable without a second model call, and without guessing
whether a reworded description still "means" the same blocker.
"""

from __future__ import annotations

from dataclasses import dataclass

from .advisor import RemediationPlan
from .models import PlanView


@dataclass(frozen=True)
class FaithfulnessResult:
    ok: bool
    missing_indices: tuple[int, ...]  # real blockers the plan never cited
    fabricated_indices: tuple[int, ...]  # cited indices that don't exist
    duplicate_indices: tuple[int, ...]  # real blockers cited more than once


def check(plan_view: PlanView, remediation: RemediationPlan) -> FaithfulnessResult:
    expected = set(range(len(plan_view.blockers)))
    cited = [step.blocker_index for step in remediation.steps]
    cited_set = set(cited)

    missing = tuple(sorted(expected - cited_set))
    fabricated = tuple(sorted(cited_set - expected))
    duplicates = tuple(sorted({i for i in cited if cited.count(i) > 1} & expected))

    ok = not missing and not fabricated and not duplicates
    return FaithfulnessResult(
        ok=ok,
        missing_indices=missing,
        fabricated_indices=fabricated,
        duplicate_indices=duplicates,
    )
