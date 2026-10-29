"""Tests for the offline diff engine."""

import pytest

from llm_diff_explainer.diffcore import (
    ADDED,
    REMOVED,
    UNCHANGED,
    compute_diff,
    split_paragraphs,
    split_lines,
)


def test_identical_documents_report_no_changes(identical):
    result = compute_diff(identical, identical)
    assert result.added == 0
    assert result.removed == 0
    assert not result.has_changes
    assert all(b.status == UNCHANGED for b in result.blocks)


def test_paragraph_add_and_remove_counts(contract_v1, contract_v2):
    result = compute_diff(contract_v1, contract_v2)
    # v1 has PAYMENT TERMS and old termination notice and 180 pages;
    # v2 adds LATE FEES, changes 180->200 and 30->60.
    assert result.added >= 2
    assert result.removed >= 2
    assert result.has_changes


def test_statuses_are_stamped_on_both_sides(contract_v1, contract_v2):
    result = compute_diff(contract_v1, contract_v2)
    old_blocks = [b for b in result.blocks if b.side == "old"]
    new_blocks = [b for b in result.blocks if b.side == "new"]
    statuses = {b.status for b in old_blocks + new_blocks}
    assert statuses == {ADDED, REMOVED, UNCHANGED}
    assert all(b.number >= 1 for b in old_blocks + new_blocks)


def test_added_paragraphs_contain_new_text(contract_v1, contract_v2):
    result = compute_diff(contract_v1, contract_v2)
    added_text = "\n".join(
        b.text for b in result.blocks if b.status == ADDED
    )
    assert "LATE FEES" in added_text
    assert "5% late fee" in added_text


def test_removed_paragraphs_contain_old_text(contract_v1, contract_v2):
    result = compute_diff(contract_v1, contract_v2)
    removed_text = "\n".join(
        b.text for b in result.blocks if b.status == REMOVED
    )
    assert "PAYMENT TERMS" in removed_text


def test_unchanged_paragraphs_survive(contract_v1, contract_v2):
    result = compute_diff(contract_v1, contract_v2)
    unchanged_text = "\n".join(
        b.text for b in result.blocks if b.status == UNCHANGED
    )
    assert "SCOPE OF WORK" in unchanged_text
    assert "REVISIONS" in unchanged_text


def test_line_mode_runs(config_v1, config_v2):
    result = compute_diff(config_v1, config_v2, mode="lines")
    assert result.unit == "line"
    removed = "\n".join(b.text for b in result.blocks if b.status == REMOVED)
    added = "\n".join(b.text for b in result.blocks if b.status == ADDED)
    assert "port = 8080" in removed
    assert "port = 8443" in added


def test_invalid_mode_falls_back_to_paragraphs(contract_v1, contract_v2):
    result = compute_diff(contract_v1, contract_v2, mode="nonsense")
    assert result.unit == "paragraph"


def test_summary_singular_and_plural():
    one = compute_diff("Alpha", "Alpha\n\nBeta")
    assert "1 paragraph added, 0 paragraphs removed" in one.summary
    two = compute_diff("Alpha\n\nBeta\n\nGamma", "Alpha\n\nDelta")
    assert "1 paragraph added, 2 paragraphs removed" in two.summary


def test_split_paragraphs_collapses_blank_runs():
    assert split_paragraphs("a\n\n\n\nb\n   \n\nc") == ["a", "b", "c"]
    assert split_paragraphs("   \n\nreal text") == ["real text"]
    assert split_paragraphs("") == []


def test_split_lines():
    assert split_lines("one\ntwo") == ["one", "two"]
    assert split_lines("one") == ["one"]


def test_block_order_interleaves_old_then_new_not_required():
    result = compute_diff("Alpha\n\nBeta", "Gamma\n\nBeta")
    olds = [b for b in result.blocks if b.side == "old"]
    news = [b for b in result.blocks if b.side == "new"]
    assert len(olds) == 2 and len(news) == 2
    assert any(b.status == REMOVED for b in olds)
    assert any(b.status == ADDED for b in news)
    assert any(b.status == UNCHANGED for b in olds + news)


@pytest.mark.parametrize("mode", ["paragraphs", "lines"])
def test_mode_change_changes_unit(mode):
    result = compute_diff("a\n\nb", "a\n\nc", mode=mode)
    assert result.unit == ("paragraph" if mode == "paragraphs" else "line")
