"""Calls Claude to turn a `PlanView` into a prioritized remediation narrative.

Structured output is forced via a tool call (`tool_choice`), not parsed out of
free text — the model either returns something matching the schema or the
API call itself fails validation, so there's no "the model wrapped the JSON
in a sentence" class of bug to handle.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from pydantic import BaseModel, Field

from .models import PlanView

_TOOL_NAME = "emit_remediation_plan"

_TOOL_SCHEMA: dict[str, Any] = {
    "name": _TOOL_NAME,
    "description": "Emit a prioritized, cited remediation plan for the given upgrade blockers.",
    "input_schema": {
        "type": "object",
        "properties": {
            "summary": {
                "type": "string",
                "description": "1-3 plain-language sentences on overall upgrade readiness.",
            },
            "steps": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "blocker_index": {
                            "type": "integer",
                            "description": "0-based index into the blockers list this step "
                            "addresses.",
                        },
                        "priority": {
                            "type": "integer",
                            "description": "1 = do first. Every blocker must get a distinct step.",
                        },
                        "rationale": {
                            "type": "string",
                            "description": "Why this blocker matters and roughly how to fix it.",
                        },
                    },
                    "required": ["blocker_index", "priority", "rationale"],
                },
            },
        },
        "required": ["summary", "steps"],
    },
}


class _StepModel(BaseModel):
    blocker_index: int
    priority: int
    rationale: str


class _RemediationPlanModel(BaseModel):
    summary: str
    steps: list[_StepModel] = Field(default_factory=list)


@dataclass(frozen=True)
class Step:
    blocker_index: int
    priority: int
    rationale: str


@dataclass(frozen=True)
class RemediationPlan:
    summary: str
    steps: tuple[Step, ...]
    model: str
    input_tokens: int
    output_tokens: int


class MessagesClient(Protocol):
    """The slice of `anthropic.Anthropic().messages` this module calls —
    narrow on purpose so tests can pass a stub instead of a real SDK client."""

    def create(self, **kwargs: Any) -> Any: ...


def _prompt(plan_view: PlanView) -> str:
    lines = [
        f"Target PHP: {plan_view.target_php}",
        f"Target Magento: {plan_view.target_magento}",
        f"ready: {plan_view.ready}",
    ]
    if plan_view.blockers:
        lines.append("\nBlockers (cite each exactly once by its index):")
        for i, b in enumerate(plan_view.blockers):
            lines.append(f"[{i}] source={b.source} description={b.description} detail={b.detail}")
    else:
        lines.append("\nNo blockers.")
    if plan_view.unverified:
        lines.append("\nSignals that could not be checked (do not treat as blockers):")
        lines.extend(f"- {signal}" for signal in plan_view.unverified)
    return "\n".join(lines)


_SYSTEM_PROMPT = (
    "You advise on Magento 2 / Adobe Commerce upgrade readiness from a structured "
    "upgrade-plan report. Call emit_remediation_plan exactly once. Cite every blocker "
    "in the input by its index, each exactly once, in the order it should be fixed. "
    "Never invent a blocker index that wasn't given to you, and never fix only some "
    "of them. If there are no blockers, return an empty steps list and say so in the "
    "summary. Treat 'unverified' signals as caveats to mention in the summary, not as "
    "blockers to cite."
)


def explain(
    plan_view: PlanView,
    *,
    client: MessagesClient,
    model: str,
    max_tokens: int = 1024,
) -> RemediationPlan:
    response = client.create(
        model=model,
        max_tokens=max_tokens,
        system=_SYSTEM_PROMPT,
        tools=[_TOOL_SCHEMA],
        tool_choice={"type": "tool", "name": _TOOL_NAME},
        messages=[{"role": "user", "content": _prompt(plan_view)}],
    )

    tool_use = next(block for block in response.content if block.type == "tool_use")
    parsed = _RemediationPlanModel.model_validate(tool_use.input)

    return RemediationPlan(
        summary=parsed.summary,
        steps=tuple(Step(s.blocker_index, s.priority, s.rationale) for s in parsed.steps),
        model=model,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
    )
