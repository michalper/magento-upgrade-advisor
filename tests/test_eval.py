from __future__ import annotations

from magento_upgrade_advisor.eval.fixtures import FIXTURES
from magento_upgrade_advisor.eval.report import render_markdown
from magento_upgrade_advisor.eval.runner import run

from .conftest import StubMessagesClient, make_response


def _faithful_response(**kwargs):
    """Scripted stub: cites every blocker in the prompt's plan exactly once,
    in order — so every fixture/model pair in this test passes faithfulness,
    proving the harness's plumbing (not real model behavior)."""
    prompt = kwargs["messages"][0]["content"]
    n_blockers = prompt.count("\n[")  # one "[<i>] source=..." line per blocker
    steps = [
        {"blocker_index": i, "priority": i + 1, "rationale": f"fix #{i}"} for i in range(n_blockers)
    ]
    return make_response({"summary": "ok", "steps": steps})


def test_run_covers_every_fixture_model_pair():
    client = StubMessagesClient(_faithful_response)
    models = ["claude-haiku-5-5", "claude-sonnet-5-5"]

    results = run(FIXTURES, models, client)

    assert len(results) == len(FIXTURES) * len(models)
    assert all(r.faithfulness.ok for r in results)
    assert all(r.error is None for r in results)


def test_run_records_error_instead_of_raising():
    def _broken(**kwargs):
        raise RuntimeError("rate limited")

    client = StubMessagesClient(_broken)
    fixtures = {"ready_no_blockers": FIXTURES["ready_no_blockers"]}
    results = run(fixtures, ["claude-haiku-5-5"], client)

    assert len(results) == 1
    assert results[0].error == "rate limited"
    assert not results[0].faithfulness.ok


def test_render_markdown_includes_pass_rate_summary():
    client = StubMessagesClient(_faithful_response)
    results = run(FIXTURES, ["claude-haiku-5-5"], client)

    report = render_markdown(results)

    assert "Pass rate by model" in report
    assert f"claude-haiku-5-5 | {len(FIXTURES)} / {len(FIXTURES)}" in report
