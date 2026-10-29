"""Offline diff engine built on the Python standard library (difflib).

No third-party dependencies and no network access: everything here works
with a plain Python install.  Text is compared paragraph by paragraph (or
line by line with --mode lines), and structured operations are returned so
the terminal renderer and HTML renderer can share one model.
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field

ADDED = "added"
REMOVED = "removed"
UNCHANGED = "unchanged"


@dataclass
class Block:
    """One paragraph or line from one of the two documents."""

    side: str  # "old" or "new"
    number: int  # 1-based index within its side
    text: str
    status: str  # ADDED / REMOVED / UNCHANGED


@dataclass
class DiffResult:
    blocks: list[Block] = field(default_factory=list)
    added: int = 0
    removed: int = 0
    unit: str = "paragraph"

    @property
    def summary(self) -> str:
        def plural(n: int) -> str:
            return self.unit + ("" if n == 1 else "s")

        return "%d %s added, %d %s removed" % (
            self.added,
            plural(self.added),
            self.removed,
            plural(self.removed),
        )

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed)


def split_paragraphs(text: str) -> list[str]:
    """Split text into paragraphs on blank lines, trimming outer whitespace.

    Consecutive blank lines collapse into one paragraph break so documents
    formatted with unusually wide gaps still compare cleanly.
    """
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text)]
    return [p for p in paragraphs if p]


def split_lines(text: str) -> list[str]:
    return text.splitlines()


def compute_diff(old_text: str, new_text: str, mode: str = "paragraphs") -> DiffResult:
    """Diff two documents and annotate every block with its change status.

    mode: "paragraphs" (default) compares blank-line-separated paragraphs;
          "lines" compares individual lines.
    """
    used_mode = mode if mode in ("paragraphs", "lines") else "paragraphs"
    splitter = split_paragraphs if used_mode == "paragraphs" else split_lines
    unit = "paragraph" if used_mode == "paragraphs" else "line"

    old_parts = splitter(old_text)
    new_parts = splitter(new_text)

    matcher = difflib.SequenceMatcher(a=old_parts, b=new_parts, autojunk=False)
    result = DiffResult(unit=unit)

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        old_chunk = old_parts[i1:i2]
        new_chunk = new_parts[j1:j2]

        if tag == "equal":
            for idx, text in enumerate(old_chunk, start=i1 + 1):
                result.blocks.append(Block("old", idx, text, UNCHANGED))
                result.blocks.append(Block("new", idx, text, UNCHANGED))
            continue

        for idx, text in enumerate(old_chunk, start=i1 + 1):
            result.blocks.append(Block("old", idx, text, REMOVED))
            result.removed += 1
        for idx, text in enumerate(new_chunk, start=j1 + 1):
            result.blocks.append(Block("new", idx, text, ADDED))
            result.added += 1

    return result
