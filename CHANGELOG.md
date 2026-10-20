# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/) (pre-1.0:
a minor bump means new features, a patch means fixes only).

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
