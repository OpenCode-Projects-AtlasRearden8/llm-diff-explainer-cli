"""End-to-end tests for the lldiff command line interface."""

import json
import urllib.request

import pytest

from llm_diff_explainer.cli import main

from .test_explain import FakeResponse, call_body, completion  # noqa: F401


@pytest.fixture
def run_cli(tmp_path, fixture_dir, monkeypatch):
    state = {"contacted": False}

    def fake_urlopen(request, timeout=None):
        state["contacted"] = True
        state["url"] = request.full_url
        state["data"] = request.data
        return FakeResponse(completion("A friendly explanation."))

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    monkeypatch.chdir(tmp_path)
    return {"fixture_dir": fixture_dir, "tmp_path": tmp_path, "state": state}


def test_cli_exit_codes_on_missing_file(run_cli, capsys):
    code = main(["missing-one.txt", "missing-two.txt"])
    assert code == 2
    assert "error reading input files" in capsys.readouterr().err


def test_cli_diff_only(run_cli, capsys):
    fixture_dir = run_cli["fixture_dir"]
    code = main(
        [
            str(fixture_dir / "config-v1.ini"),
            str(fixture_dir / "config-v2.ini"),
            "--diff-text-only",
            "--mode",
            "lines",
        ]
    )
    out = capsys.readouterr().out
    assert code == 0
    assert "1 line added, 1 line removed" in out
    assert "host = 127.0.0.1" in out
    assert "added" in out and "removed" in out


def test_cli_terminal_diff(run_cli, capsys):
    fixture_dir = run_cli["fixture_dir"]
    code = main(
        [
            str(fixture_dir / "contract-v1.txt"),
            str(fixture_dir / "contract-v2.txt"),
            "--no-color",
        ]
    )
    out = capsys.readouterr().out
    assert code == 0
    assert "PAYMENT TERMS" in out
    assert "LATE FEES" in out


def test_cli_html_output(run_cli, capsys):
    fixture_dir = run_cli["fixture_dir"]
    target = run_cli["tmp_path"] / "report.html"
    code = main(
        [
            str(fixture_dir / "contract-v1.txt"),
            str(fixture_dir / "contract-v2.txt"),
            "--no-color",
            "--html",
            str(target),
        ]
    )
    out = capsys.readouterr().out
    assert code == 0
    assert "HTML report saved" in out
    text = target.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in text
    assert 'class="added"' in text
    assert "llm-diff-explainer (Asdale Dynamics, LLC)" in text


def test_cli_explain_calls_endpoint(run_cli, capsys):
    fixture_dir = run_cli["fixture_dir"]
    code = main(
        [
            str(fixture_dir / "contract-v1.txt"),
            str(fixture_dir / "contract-v2.txt"),
            "--no-color",
            "--explain",
            "--model",
            "mistral",
        ]
    )
    out = capsys.readouterr().out
    assert code == 0
    assert "A friendly explanation." in out
    payload = json.loads(call_body(run_cli["state"]))
    assert payload["model"] == "mistral"


def test_cli_explain_identical_documents_says_nothing_to_explain(
    run_cli, capsys, fixture_dir
):
    code = main(
        [
            str(fixture_dir / "identical.txt"),
            str(fixture_dir / "identical.txt"),
            "--no-color",
            "--explain",
        ]
    )
    out = capsys.readouterr().out
    assert code == 0
    assert "Nothing to explain" in out
    assert not run_cli["state"]["contacted"]


def test_cli_html_write_error_is_reported(run_cli, capsys, fixture_dir):
    code = main(
        [
            str(fixture_dir / "identical.txt"),
            str(fixture_dir / "identical.txt"),
            "--no-color",
            "--html",
            "/proc/cannot/write/here.html",
        ]
    )
    err = capsys.readouterr().err
    assert code == 0
    assert "error writing HTML file" in err
