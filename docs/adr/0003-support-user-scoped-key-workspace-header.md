# ADR 0003: Support `ANTHROPIC_WORKSPACE_ID` for user-scoped API keys

## Status

Superseded by [ADR 0004](0004-use-sdk-native-anthropic-custom-headers.md) — the `anthropic` SDK
already reads the same header from its own `ANTHROPIC_CUSTOM_HEADERS` env var, so the bespoke
`ANTHROPIC_WORKSPACE_ID` handling this ADR introduced was removed rather than kept or tested.

## Context

A live run against the real Anthropic API failed with a 400 the stubbed tests never exercise:
`"This API key is not scoped to a workspace, so this request must include the
anthropic-workspace-id header..."`. The key in question was created with `Scope: Organization` in
the Anthropic Console (acts as the user who created it) rather than scoped to one specific
workspace — the Console's own copy explains the distinction: *"A key acts as the user or service
account it was created for. A workspace key belongs to a workspace and stays active after its
creator leaves."* Nothing in this project's code or tests had a reason to know this distinction
existed until a real key surfaced it.

## Decision

`client.default_client()` reads an optional `ANTHROPIC_WORKSPACE_ID` environment variable and, if
set, passes it as the `anthropic-workspace-id` header via the SDK's own `default_headers`
parameter. Unset (the common case — a key already scoped to a workspace doesn't need it), nothing
changes: `anthropic.Anthropic(default_headers=None)` behaves exactly as before this ADR.

Alternatives rejected:

- **Tell the user to create a workspace-scoped key instead and leave the client unchanged.**
  Rejected — that's real advice (see the README note this ADR also added), but it doesn't help
  someone who already has a user-scoped key and no reason yet to know the difference matters;
  supporting the header costs four lines and a docstring, handling it on the client's side
  wherever this happens is cheaper than a support announcement.
- **Hardcode a workspace ID.** Never considered — a workspace ID is per-account, so hardcoding one
  would break for anyone except the original author's own account.

## Consequences

- This was only found because a real API call was made with a real key — the stubbed test suite
  (by design, see the README's own philosophy on faithfulness) has no way to catch an API-shape
  issue like this one, since the stub never had an opinion about headers. A live `eval` run,
  not just green CI, is still worth doing before trusting this project end to end.
