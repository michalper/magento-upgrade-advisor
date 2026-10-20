# ADR 0002: Check faithfulness via cited indices, not an LLM-as-judge pass

## Status

Accepted.

## Context

Turning a list of real blockers into a prioritized narrative is exactly the kind of task where an
LLM can silently drop an inconvenient blocker, merge two distinct ones, or invent a plausible-
sounding one that was never in the input — and a demo that "reads well" wouldn't reveal any of
that. This needs a check that something that happened actually matches what was given, not just
that the output looks competent.

## Decision

The model is asked (via the forced `emit_remediation_plan` tool call, see `advisor.py`) to cite
each blocker it addresses **by its 0-based index into the input `blockers` list**, not to restate
the blocker in its own words. `faithfulness.check()` then does a pure set-comparison on integers:
every real index must appear in the output exactly once (`missing` / `fabricated` / `duplicate`
otherwise). No second model call, no semantic similarity scoring, no fuzzy matching against a
paraphrase.

Alternatives rejected:

- **LLM-as-judge: ask a second model call "does this narrative account for every blocker below,
  faithfully?"** Rejected — it moves the hallucination risk one level up instead of removing it;
  the judge model can itself miss a dropped blocker or be convinced by a fabricated one, and now
  there are two non-deterministic calls to reason about instead of one deterministic check.
- **Fuzzy-match the narrative's free text against each blocker's `description`/`detail`.**
  Rejected — a faithful summary is expected to paraphrase ("the Guzzle SSRF advisory" instead of
  repeating `GHSA-abcd-1234: SSRF via redirect handling` verbatim), so this would need a similarity
  threshold tuned by hand, with no clean line between "faithfully summarized" and "conveniently
  vague enough to dodge the check."
- **A single faithfulness score (e.g. 0-1) instead of missing/fabricated/duplicate lists.**
  Rejected — same reasoning as `mcp-magento-audit`'s own `UpgradePlan.blockers` design (see that
  project's `upgrade_plan.py` docstring): a list of concrete problems is actionable ("index 2 was
  never cited"), a single number isn't, and it would hide *which* failure mode actually happened.

## Consequences

- This only verifies *coverage* (every real blocker cited once, nothing invented) — it says
  nothing about whether a given `rationale` is itself correct or useful. A model can pass this
  check while still giving a bad reason for a real blocker; that's out of scope for an automated
  check and would need a human or domain-expert review instead.
- Because citation is by index, the prompt's blocker list and the fixture/plan it was built from
  must stay in the same order the model saw them in — `advisor._prompt()` and
  `faithfulness.check()` both iterate `plan_view.blockers` directly, so this holds by construction,
  not by convention.
