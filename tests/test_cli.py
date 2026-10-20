from __future__ import annotations

import argparse
from types import SimpleNamespace

import pytest
from mcp_magento_audit.composer import ProjectError
from mcp_magento_audit.upgrade_plan import Blocker

from magento_upgrade_advisor import cli

from .conftest import StubMessagesClient, make_response


def _plan(blockers: tuple[Blocker, ...] = ()) -> SimpleNamespace:
    return SimpleNamespace(
        target_php="8.3",
        target_magento="2.4.7",
        ready=not blockers,
        blockers=blockers,
        unverified=(),
    )


def _build_plan(blockers: tuple[Blocker, ...]):
    return lambda project, target_php, target_magento: _plan(blockers)


def _explain_args(**overrides) -> argparse.Namespace:
    defaults = dict(
        path="/tmp/project",
        target_php="8.3",
        target_magento="2.4.7",
        model="claude-sonnet-5-5",
    )
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


def test_cmd_explain_success(monkeypatch, capsys):
    blockers = (Blocker(source="security", description="pkg", detail="CVE-1"),)
    monkeypatch.setattr(cli, "load_project", lambda path: object())
    monkeypatch.setattr(cli, "build_upgrade_plan", _build_plan(blockers))
    response = make_response(
        {
            "summary": "Fix the one security issue.",
            "steps": [{"blocker_index": 0, "priority": 1, "rationale": "patch it"}],
        }
    )
    monkeypatch.setattr(cli, "default_client", lambda: StubMessagesClient(response))

    exit_code = cli._cmd_explain(_explain_args())

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Fix the one security issue." in out
    assert "[security] pkg — patch it" in out


def test_cmd_explain_project_error(monkeypatch, capsys):
    def _raise(path):
        raise ProjectError(f"{path} is not a directory")

    monkeypatch.setattr(cli, "load_project", _raise)

    exit_code = cli._cmd_explain(_explain_args())

    assert exit_code == 1
    assert "error:" in capsys.readouterr().err


def test_cmd_explain_faithfulness_failure_is_reported_and_nonzero(monkeypatch, capsys):
    blockers = (Blocker(source="security", description="pkg", detail="CVE-1"),)
    monkeypatch.setattr(cli, "load_project", lambda path: object())
    monkeypatch.setattr(cli, "build_upgrade_plan", _build_plan(blockers))
    # model drops the only blocker instead of citing it
    response = make_response({"summary": "All good.", "steps": []})
    monkeypatch.setattr(cli, "default_client", lambda: StubMessagesClient(response))

    exit_code = cli._cmd_explain(_explain_args())

    assert exit_code == 2
    err = capsys.readouterr().err
    assert "faithfulness check FAILED" in err
    assert "missing: [0]" in err


def test_cmd_eval_prints_report_to_stdout(monkeypatch, capsys):
    def _faithful(**kwargs):
        prompt = kwargs["messages"][0]["content"]
        n = prompt.count("\n[")
        steps = [{"blocker_index": i, "priority": i + 1, "rationale": "r"} for i in range(n)]
        return make_response({"summary": "ok", "steps": steps})

    monkeypatch.setattr(cli, "default_client", lambda: StubMessagesClient(_faithful))

    exit_code = cli._cmd_eval(argparse.Namespace(models="claude-haiku-5-5", out=None))

    assert exit_code == 0
    assert "Pass rate by model" in capsys.readouterr().out


def test_cmd_eval_writes_report_to_file(monkeypatch, tmp_path, capsys):
    def _faithful(**kwargs):
        prompt = kwargs["messages"][0]["content"]
        n = prompt.count("\n[")
        steps = [{"blocker_index": i, "priority": i + 1, "rationale": "r"} for i in range(n)]
        return make_response({"summary": "ok", "steps": steps})

    monkeypatch.setattr(cli, "default_client", lambda: StubMessagesClient(_faithful))
    out_path = tmp_path / "report.md"

    exit_code = cli._cmd_eval(argparse.Namespace(models=None, out=out_path))

    assert exit_code == 0
    assert out_path.exists()
    assert "Pass rate by model" in out_path.read_text()


def test_main_dispatches_to_explain(monkeypatch):
    called = {}

    def _fake_explain(args):
        called["args"] = args
        return 0

    monkeypatch.setattr(cli, "_cmd_explain", _fake_explain)
    argv = [
        "magento-upgrade-advisor",
        "explain",
        "/tmp/x",
        "--target-php",
        "8.3",
        "--target-magento",
        "2.4.7",
    ]
    monkeypatch.setattr("sys.argv", argv)

    assert cli.main() == 0
    assert called["args"].path == "/tmp/x"


def test_main_requires_a_subcommand(monkeypatch):
    monkeypatch.setattr("sys.argv", ["magento-upgrade-advisor"])
    with pytest.raises(SystemExit):
        cli.main()
