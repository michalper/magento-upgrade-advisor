from __future__ import annotations

from collections.abc import Callable
from types import SimpleNamespace
from typing import Any


def make_response(tool_input: dict[str, Any], *, input_tokens: int = 10, output_tokens: int = 20):
    """A stand-in for `anthropic.types.Message` — only the attributes
    `advisor.explain()` actually reads."""
    tool_use_block = SimpleNamespace(
        type="tool_use", name="emit_remediation_plan", input=tool_input
    )
    return SimpleNamespace(
        content=[tool_use_block],
        usage=SimpleNamespace(input_tokens=input_tokens, output_tokens=output_tokens),
    )


def faithful_response(**kwargs: Any) -> Any:
    """A `StubMessagesClient(faithful_response)` always cites every blocker in the
    prompt exactly once, in order — so any fixture/model pair passed through it
    passes `faithfulness.check()`. Used by tests that only care about exercising
    the rest of a code path (CLI wiring, the eval runner/report) and don't want to
    hand-write a per-test response for every blocker count."""
    prompt = kwargs["messages"][0]["content"]
    n_blockers = prompt.count("\n[")  # one "[<i>] source=..." line per blocker
    steps = [
        {"blocker_index": i, "priority": i + 1, "rationale": f"fix #{i}"} for i in range(n_blockers)
    ]
    return make_response({"summary": "ok", "steps": steps})


class StubMessagesClient:
    """Implements the narrow `MessagesClient` protocol. `respond_with` is
    either a fixed response, or a callable `(**kwargs) -> response` for tests
    that need the response to depend on which model/fixture was requested."""

    def __init__(self, respond_with: Any | Callable[..., Any]):
        self._respond_with = respond_with
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        if callable(self._respond_with):
            return self._respond_with(**kwargs)
        return self._respond_with
