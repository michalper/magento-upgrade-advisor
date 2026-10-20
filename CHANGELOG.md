# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/) (pre-1.0:
a minor bump means new features, a patch means fixes only).

## [Unreleased]

### Fixed
- A user-scoped API key gets a 400 from the real API ("not scoped to a workspace") unless the
  request carries an `anthropic-workspace-id` header — found via a live run, not by the stubbed
  test suite. Initially handled with a project-private `ANTHROPIC_WORKSPACE_ID` env var (ADR
  0003), then replaced with the `anthropic` SDK's own `ANTHROPIC_CUSTOM_HEADERS` mechanism, which
  already supported this with no project code needed (ADR 0004, superseding 0003) — see the
  README's install section for the env var to set.
- `cli.py`'s `explain` rendering loop indexed `plan_view.blockers[step.blocker_index]` directly,
  before the faithfulness check that flags exactly this as a fabricated index ever ran — a model
  citing an out-of-range index crashed with a raw `IndexError` instead of reaching the "faithfulness
  check FAILED" reporting path. Now renders `[unknown blocker #N]` for an invalid index and lets
  the faithfulness check below report it properly.

### Changed
- Deduplicated the scripted "cite every blocker, in order" stub response (previously copy-pasted
  across `tests/test_eval.py` and twice in `tests/test_cli.py`) into one `faithful_response()`
  helper in `tests/conftest.py`.
- `eval/runner.py`'s `run()` no longer constructs `EvalResult` twice (once per try/except branch)
  for a cosmetic difference — the four values that vary are set in the try/except, `EvalResult` is
  built once after it.

## [0.1.0] - 2026-10-20

### Added
- `advisor.explain()`: turns an `mcp-magento-audit` `UpgradePlan` into a prioritized remediation
  narrative via a forced Claude tool call (`emit_remediation_plan`).
- `faithfulness.check()`: deterministic missing/fabricated/duplicate check on the blocker indices
  the model cited, no second model call involved.
- `eval` package: synthetic `PlanView` fixtures, a runner comparing models, and a markdown report
  with a per-model pass-rate summary.
- `magento-upgrade-advisor explain`/`magento-upgrade-advisor eval` CLI commands.
- 98% test coverage against a stubbed Anthropic client; `ruff`, `mypy --strict`, `bandit`,
  `pip-audit` all clean. No live run against the real API recorded yet — see
  `docs/eval-report.md`.
