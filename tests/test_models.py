from __future__ import annotations

from types import SimpleNamespace

from mcp_magento_audit.upgrade_plan import Blocker

from magento_upgrade_advisor.models import from_upgrade_plan


def test_from_upgrade_plan_keeps_only_the_fields_the_advisor_needs():
    blockers = (Blocker(source="composer", description="pkg", detail="d"),)
    # Duck-typed stand-in for a real `UpgradePlan` — only the five attributes
    # `from_upgrade_plan` reads matter here; the other fields a real
    # `build_upgrade_plan()` call fills in (release_notes, update_check, ...)
    # are irrelevant to this conversion and deliberately left out.
    fake_plan = SimpleNamespace(
        target_php="8.3",
        target_magento="2.4.7",
        ready=False,
        blockers=blockers,
        unverified=("phpstan: not installed",),
    )

    view = from_upgrade_plan(fake_plan)

    assert view.target_php == "8.3"
    assert view.target_magento == "2.4.7"
    assert view.ready is False
    assert view.blockers == blockers
    assert view.unverified == ("phpstan: not installed",)
