# ADR 0001: Depend on `mcp-magento-audit` as a library, don't duplicate its schema

## Status

Accepted.

## Context

This project's input is the `UpgradePlan` (and its `Blocker` items) that
[`mcp-magento-audit`](https://github.com/michalper/mcp-magento-audit)'s `build_upgrade_plan`
already computes. That project is published to PyPI and its dataclasses
(`mcp_magento_audit.upgrade_plan.UpgradePlan`, `Blocker`) are plain, importable Python — there's
no serialization boundary (REST, MCP transport) forcing this project to re-declare the shape of
that data as its own types.

## Decision

`magento-upgrade-advisor` depends on `mcp-magento-audit>=0.4` directly and imports its dataclasses.
`models.PlanView` is not a reimplementation of `UpgradePlan` — it's a narrower *view* exposing only
the five fields the reasoning layer actually reads (`target_php`, `target_magento`, `ready`,
`blockers`, `unverified`), built by `from_upgrade_plan()`. Eval fixtures construct `PlanView`
directly (via real `mcp_magento_audit.upgrade_plan.Blocker` instances) without needing to fabricate
the full `UpgradePlan` graph (`release_notes`, `update_check`, `module_risk`, `security_audit`,
`outdated_packages`), none of which this project's reasoning depends on.

Alternatives rejected:

- **Reimplement `Blocker`/`UpgradePlan` as this project's own types.** Rejected — it's the same
  author's own package, on PyPI, with no reason to fork the schema and risk the two drifting apart
  silently (a field rename in `mcp-magento-audit` would need to be mirrored by hand instead of
  failing a type check here immediately).
- **Consume `mcp-magento-audit` only via its MCP tool interface (stdio/JSON), not as a library.**
  Rejected for this use case — that's the right boundary when the caller is an LLM client (Claude
  Code, an agent) that only understands MCP tool calls, but this project's own code is calling
  `build_upgrade_plan()` directly as a Python function, so going through a process boundary and
  JSON (de)serialization would add latency and failure modes with no benefit.

## Consequences

- `mcp-magento-audit`'s current lack of a `py.typed` marker (PEP 561) means `mypy` can't verify
  types across the import boundary — worked around locally with a `[[tool.mypy.overrides]]` entry
  ignoring missing imports for `mcp_magento_audit.*`, not fixed upstream in this repo.
- A breaking change to `UpgradePlan`/`Blocker` in a future `mcp-magento-audit` release surfaces here
  as an import or type error at `from_upgrade_plan()`'s call site, not as a silent schema mismatch.
