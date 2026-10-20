from __future__ import annotations

from mcp_magento_audit.upgrade_plan import Blocker

from magento_upgrade_advisor import faithfulness
from magento_upgrade_advisor.advisor import RemediationPlan, Step
from magento_upgrade_advisor.models import PlanView

_BLOCKERS = (
    Blocker(source="composer", description="pkg-a", detail="d1"),
    Blocker(source="security", description="pkg-b", detail="d2"),
    Blocker(source="phpstan", description="file.php:1", detail="d3"),
)
_PLAN_VIEW = PlanView(
    target_php="8.3", target_magento="2.4.7", ready=False, blockers=_BLOCKERS, unverified=()
)


def _remediation(steps: list[Step]) -> RemediationPlan:
    return RemediationPlan(
        summary="s", steps=tuple(steps), model="m", input_tokens=1, output_tokens=1
    )


def test_perfect_match_is_faithful():
    remediation = _remediation(
        [Step(0, 1, "r0"), Step(1, 2, "r1"), Step(2, 3, "r2")]
    )
    result = faithfulness.check(_PLAN_VIEW, remediation)
    assert result.ok
    assert result.missing_indices == ()
    assert result.fabricated_indices == ()
    assert result.duplicate_indices == ()


def test_missing_blocker_is_caught():
    remediation = _remediation([Step(0, 1, "r0"), Step(1, 2, "r1")])  # drops index 2
    result = faithfulness.check(_PLAN_VIEW, remediation)
    assert not result.ok
    assert result.missing_indices == (2,)


def test_fabricated_index_is_caught():
    remediation = _remediation(
        [Step(0, 1, "r0"), Step(1, 2, "r1"), Step(2, 3, "r2"), Step(99, 4, "invented")]
    )
    result = faithfulness.check(_PLAN_VIEW, remediation)
    assert not result.ok
    assert result.fabricated_indices == (99,)


def test_duplicate_citation_is_caught():
    remediation = _remediation(
        [Step(0, 1, "r0"), Step(0, 2, "r0 again"), Step(1, 3, "r1"), Step(2, 4, "r2")]
    )
    result = faithfulness.check(_PLAN_VIEW, remediation)
    assert not result.ok
    assert result.duplicate_indices == (0,)
    # a duplicated-but-real index is not also reported as missing
    assert result.missing_indices == ()


def test_empty_blockers_and_empty_steps_is_faithful():
    plan_view = PlanView(
        target_php="8.3", target_magento="2.4.7", ready=True, blockers=(), unverified=()
    )
    remediation = _remediation([])
    result = faithfulness.check(plan_view, remediation)
    assert result.ok
