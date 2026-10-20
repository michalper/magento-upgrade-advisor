# ADR 0004: Use the SDK's own `ANTHROPIC_CUSTOM_HEADERS`, not a project-private env var

## Status

Accepted. Supersedes [ADR 0003](0003-support-user-scoped-key-workspace-header.md).

## Context

ADR 0003's `ANTHROPIC_WORKSPACE_ID` → `default_headers={"anthropic-workspace-id": ...}` fix worked,
but a review turned up that the installed `anthropic` SDK already does the same thing generically:
`Anthropic.__init__` (`anthropic/_client.py`) parses an `ANTHROPIC_CUSTOM_HEADERS` env var (one
`Header: value` per line) straight into `default_headers`, and `_CLIENT_LEVEL_HEADER_PARAMS`
explicitly protects `anthropic-workspace-id` (alongside `anthropic-user-profile-id`) from being
stripped as a client-level header — i.e. the SDK already treats "workspace id as an env-sourced
default header" as a first-class, supported case. ADR 0003 solved this one layer below where the
dependency already solved it, and as a direct consequence shipped a branch of `default_client()`
with no test covering it (missing/fabricated/duplicate indices are easy to test against a stub;
"did we build the right header dict" needed a test that was never added).

## Decision

`client.default_client()` goes back to a single `anthropic.Anthropic().messages` call with no
header logic of its own. Workspace scoping is documented (README) as something to set via the
SDK's own `ANTHROPIC_CUSTOM_HEADERS`, not a project-specific variable:

```bash
export ANTHROPIC_CUSTOM_HEADERS="anthropic-workspace-id: wrkspc_..."
```

Alternatives rejected:

- **Keep `ANTHROPIC_WORKSPACE_ID`, just add the missing test.** Rejected — the test would exist
  only to cover code that duplicates a mechanism the dependency already ships; removing the code
  removes the untested branch instead of patching around it.
- **Make `workspace_id` an explicit parameter of `default_client(workspace_id: str | None = None)`.**
  A real alternative, and still available later if a project-specific knob is ever needed (e.g. a
  `--workspace-id` CLI flag, or tests passing different ids without mutating env vars) — not adopted
  now because nothing in this project currently needs workspace id to vary within a single process,
  so there's no caller yet to justify a parameter over the SDK's own env var.

## Consequences

- One less environment variable to document and remember — `ANTHROPIC_CUSTOM_HEADERS` is the
  SDK's own name, so it's the same variable anyone would reach for with any other `anthropic`-SDK
  based tool, not something specific to `magento-upgrade-advisor`.
- If a future need arises to vary the workspace id *within* a single process (not just once via
  the environment), that's the point to revisit the "explicit parameter" alternative above — this
  ADR doesn't rule it out, it just wasn't needed yet.
