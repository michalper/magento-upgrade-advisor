"""Synthetic `PlanView` fixtures, shaped like real `build_upgrade_plan` output
but handwritten — covers edge cases a single real project is unlikely to hit
all at once (zero blockers, many blockers, mixed sources, unverified signals)."""

from __future__ import annotations

from mcp_magento_audit.upgrade_plan import Blocker

from ..models import PlanView

FIXTURES: dict[str, PlanView] = {
    "ready_no_blockers": PlanView(
        target_php="8.3",
        target_magento="2.4.7",
        ready=True,
        blockers=(),
        unverified=(),
    ),
    "single_security_blocker": PlanView(
        target_php="8.3",
        target_magento="2.4.7",
        ready=False,
        blockers=(
            Blocker(
                source="security",
                description="monolog/monolog",
                detail="CVE-2022-12345: remote log injection in formatter",
            ),
        ),
        unverified=(),
    ),
    "mixed_blockers": PlanView(
        target_php="8.4",
        target_magento="2.4.8",
        ready=False,
        blockers=(
            Blocker(source="composer", description="vendor/old-module", detail="requires php <8.0"),
            Blocker(
                source="code_compatibility",
                description="app/code/Vendor/Module/Model/Thing.php",
                detail="CreateFunctionToArrowFunctionRector, NullToStrictStringFuncCallArgRector",
            ),
            Blocker(
                source="phpstan",
                description="app/code/Vendor/Module/Helper/Data.php:42",
                detail="Call to an undefined method Vendor\\Module\\Helper\\Data::getLegacyFlag().",
            ),
            Blocker(
                source="security",
                description="guzzlehttp/guzzle",
                detail="GHSA-abcd-1234: SSRF via redirect handling",
            ),
        ),
        unverified=(),
    ),
    "blockers_with_unverified": PlanView(
        target_php="8.3",
        target_magento="2.4.7",
        ready=False,
        blockers=(
            Blocker(
                source="composer",
                description="vendor/payment-extension",
                detail="requires php ^7.4",
            ),
        ),
        unverified=(
            "phpstan: no phpstan.neon(.dist) in project",
            "rector: no rector.php in project",
            "security_audit: composer not found on PATH",
        ),
    ),
    "many_blockers": PlanView(
        target_php="8.4",
        target_magento="2.4.8",
        ready=False,
        blockers=tuple(
            Blocker(
                source="phpcs",
                description=f"app/code/Vendor/Module/Model/Item{i}.php:{10 + i}",
                detail=f"Magento2.Functions.StaticFunction: avoid static method issue #{i}",
            )
            for i in range(8)
        ),
        unverified=(),
    ),
}
