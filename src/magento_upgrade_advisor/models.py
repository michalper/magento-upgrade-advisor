"""The minimal view of an mcp-magento-audit `UpgradePlan` the reasoning layer
actually needs.

`PlanView` deliberately drops `release_notes`/`update_check`/`module_risk`/
`security_audit`/`outdated_packages` — the reasoning layer only ever cites
`blockers` and `unverified`, so an eval fixture only has to construct those,
not the full nested `UpgradePlan` graph. `from_upgrade_plan()` is the only
place real `UpgradePlan` objects (from a live `build_upgrade_plan()` call)
cross into this package.
"""

from __future__ import annotations

from dataclasses import dataclass

from mcp_magento_audit.upgrade_plan import Blocker, UpgradePlan


@dataclass(frozen=True)
class PlanView:
    target_php: str
    target_magento: str
    ready: bool
    blockers: tuple[Blocker, ...]
    unverified: tuple[str, ...]


def from_upgrade_plan(plan: UpgradePlan) -> PlanView:
    return PlanView(
        target_php=plan.target_php,
        target_magento=plan.target_magento,
        ready=plan.ready,
        blockers=plan.blockers,
        unverified=plan.unverified,
    )
