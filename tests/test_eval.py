from __future__ import annotations

from magento_upgrade_advisor.eval.fixtures import FIXTURES
from magento_upgrade_advisor.eval.report import render_markdown
from magento_upgrade_advisor.eval.runner import run

from .conftest import StubMessagesClient, faithful_response


def test_run_covers_every_fixture_model_pair():
    client = StubMessagesClient(faithful_response)
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
    client = StubMessagesClient(faithful_response)
    results = run(FIXTURES, ["claude-haiku-5-5"], client)

    report = render_markdown(results)

    assert "Pass rate by model" in report
    assert f"claude-haiku-5-5 | {len(FIXTURES)} / {len(FIXTURES)}" in report
