from __future__ import annotations

from mcp_magento_audit.upgrade_plan import Blocker

from magento_upgrade_advisor.advisor import explain
from magento_upgrade_advisor.models import PlanView

from .conftest import StubMessagesClient, make_response


def test_explain_parses_tool_use_response_into_remediation_plan():
    plan_view = PlanView(
        target_php="8.3",
        target_magento="2.4.7",
        ready=False,
        blockers=(Blocker(source="security", description="pkg", detail="CVE-1"),),
        unverified=(),
    )
    response = make_response(
        {
            "summary": "One security blocker to fix before upgrading.",
            "steps": [{"blocker_index": 0, "priority": 1, "rationale": "patch the CVE"}],
        },
        input_tokens=42,
        output_tokens=17,
    )
    client = StubMessagesClient(response)

    remediation = explain(plan_view, client=client, model="claude-sonnet-5-5")

    assert remediation.summary == "One security blocker to fix before upgrading."
    assert len(remediation.steps) == 1
    assert remediation.steps[0].blocker_index == 0
    assert remediation.steps[0].rationale == "patch the CVE"
    assert remediation.model == "claude-sonnet-5-5"
    assert remediation.input_tokens == 42
    assert remediation.output_tokens == 17


def test_explain_forces_tool_choice_and_includes_blockers_in_prompt():
    plan_view = PlanView(
        target_php="8.4",
        target_magento="2.4.8",
        ready=False,
        blockers=(Blocker(source="composer", description="vendor/x", detail="needs php <8"),),
        unverified=("phpstan: no config",),
    )
    response = make_response(
        {"summary": "s", "steps": [{"blocker_index": 0, "priority": 1, "rationale": "r"}]}
    )
    client = StubMessagesClient(response)

    explain(plan_view, client=client, model="claude-haiku-5-5")

    assert len(client.calls) == 1
    call = client.calls[0]
    assert call["tool_choice"] == {"type": "tool", "name": "emit_remediation_plan"}
    assert call["model"] == "claude-haiku-5-5"
    prompt = call["messages"][0]["content"]
    assert "vendor/x" in prompt
    assert "needs php <8" in prompt
    assert "phpstan: no config" in prompt


def test_explain_handles_no_blockers():
    plan_view = PlanView(
        target_php="8.3", target_magento="2.4.7", ready=True, blockers=(), unverified=()
    )
    response = make_response({"summary": "Ready to upgrade, nothing blocks it.", "steps": []})
    client = StubMessagesClient(response)

    remediation = explain(plan_view, client=client, model="claude-sonnet-5-5")

    assert remediation.steps == ()
