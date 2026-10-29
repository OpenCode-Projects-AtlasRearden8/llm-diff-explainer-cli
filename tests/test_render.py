"""Tests for the terminal and HTML renderers."""

import re
import html as htmlmod

from llm_diff_explainer.diffcore import compute_diff
from llm_diff_explainer.render import render_html, render_terminal

ANSI_RE = re.compile(r"\033\[[0-9;]*m")


def _strip_ansi(text):
    return ANSI_RE.sub("", text)


def test_terminal_colored_output_has_ansi_codes(contract_v1, contract_v2):
    result = compute_diff(contract_v1, contract_v2)
    out = render_terminal(result, "v1", "v2", colors=True)
    assert ANSI_RE.search(out)


def test_terminal_plain_output_has_no_ansi_codes(contract_v1, contract_v2):
    result = compute_diff(contract_v1, contract_v2)
    out = render_terminal(result, "v1", "v2", colors=False)
    assert not ANSI_RE.search(out)


def test_terminal_shows_summary_and_names(contract_v1, contract_v2):
    result = compute_diff(contract_v1, contract_v2)
    out = _strip_ansi(render_terminal(result, "contract-v1.txt", "contract-v2.txt"))
    assert "Diff: contract-v1.txt  vs  contract-v2.txt" in out
    assert "added" in out and "removed" in out
    assert "PAYMENT TERMS" in out
    assert "LATE FEES" in out


def test_terminal_identical_documents(contract_v1, contract_v2, identical):
    result = compute_diff(contract_v1, contract_v2)
    assert result.has_changes
    same = compute_diff(identical, identical)
    out = render_terminal(same, "same", "same", colors=False)
    assert "No changes found." in out


def test_terminal_wraps_long_paragraphs(contract_v1, contract_v2):
    result = compute_diff(contract_v1, contract_v2)
    out = _strip_ansi(render_terminal(result, "v1", "v2", colors=False, wrap=40))
    lines = out.splitlines()
    assert all(len(line) <= 2 * (40 + 16) + 3 for line in lines)


def test_html_is_standalone(contract_v1, contract_v2):
    result = compute_diff(contract_v1, contract_v2)
    out = render_html(result, "v1.txt", "v2.txt")
    assert out.startswith("<!DOCTYPE html>")
    assert 'charset="utf-8"' in out
    assert out.count("<style>") == 1
    assert "llm-diff-explainer (Asdale Dynamics, LLC)" in out


def test_html_marks_added_and_removed(contract_v1, contract_v2):
    result = compute_diff(contract_v1, contract_v2)
    out = render_html(result, "contract-v1.txt", "contract-v2.txt")
    assert 'class="added"' in out
    assert 'class="removed"' in out
    assert 'class="unchanged"' in out
    assert "LATE FEES" in out
    assert "PAYMENT TERMS" in out


def test_html_escapes_html_in_content():
    result = compute_diff("<script>alert(1)</script>", "safe text")
    out = render_html(result, "a", "b")
    assert "<script>" not in out.replace("</script>", "")
    assert "&lt;script&gt;" in out


def test_html_identical_documents(contract_v1, contract_v2, identical):
    same = compute_diff(identical, identical)
    out = render_html(same, "a", "b")
    assert "No changes found." in out


def test_html_escapes_names():
    result = compute_diff("a", "b")
    out = render_html(result, 'a"&b', "c")
    assert 'a"&b' not in out
    assert htmlmod.escape('a"&b') in out
