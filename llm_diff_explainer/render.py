"""Renderers that turn a DiffResult into terminal text or a standalone HTML page.

Both renderers are offline and dependency-free.  The HTML output embeds its
own CSS so a single .html file can be emailed or archived without assets.
"""

from __future__ import annotations

import html
import textwrap
from datetime import datetime, timezone

from .diffcore import ADDED, REMOVED, UNCHANGED, DiffResult


def render_terminal(
    result: DiffResult,
    old_name: str,
    new_name: str,
    colors: bool = True,
    wrap: int = 50,
) -> str:
    """Render a side-by-side, colored, paragraph-by-paragraph view.

    Removed paragraphs start with '-', added with '+', unchanged are dimmed.
    Long paragraphs wrap so nothing is lost to truncation.
    """
    left_cells = _wrap_side(result.blocks, "old", wrap)
    right_cells = _wrap_side(result.blocks, "new", wrap)

    def paint(text: str, kind: str) -> str:
        if not colors:
            return text
        template = {
            "red": "\033[31m%s\033[0m",
            "green": "\033[32m%s\033[0m",
            "dim": "\033[2m%s\033[0m",
        }.get(kind)
        return template % text if template else text

    header = ["Diff: %s  vs  %s" % (old_name, new_name)]
    if not result.has_changes:
        return "\n".join(header + [paint("No changes found.", "dim")])
    header.append(result.summary)
    header.append("")
    header.append("%s | %s" % ("(old)".ljust(wrap), "(new)"))

    lines = list(header)

    col_width = wrap + 16  # room for a marker like "- [old 1234] "
    header_line = ("(old)".ljust(col_width)) + "   (new)"
    header[2] = header_line
    pairs = max(len(left_cells), len(right_cells))
    for i in range(pairs):
        left_parts = left_cells[i] if i < len(left_cells) else []
        right_parts = right_cells[i] if i < len(right_cells) else []

        left_lines = [part[1] for part in left_parts] or [""]
        right_lines = [part[1] for part in right_parts] or [""]

        left_kind = left_parts[0][0] if left_parts else "plain"
        right_kind = right_parts[0][0] if right_parts else "plain"

        for j in range(max(len(left_lines), len(right_lines))):
            la = left_lines[j] if j < len(left_lines) else ""
            rb = right_lines[j] if j < len(right_lines) else ""
            a = paint(la, left_kind) if la else ""
            pad = " " * max(col_width - len(la), 0)
            b = paint(rb, right_kind) if rb else ""
            lines.append(a + pad + "   " + b)
        lines.append("")
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def _wrap_side(blocks, side: str, wrap: int) -> list[list[list[str]]]:
    """Wrap one side into cells: a cell is a list of wrapped line parts.

    Each part is (kind, text) where kind is 'red', 'green', 'dim' or 'plain'.
    """
    cells: list[list[list[str]]] = []
    for block in [b for b in blocks if b.side == side]:
        head = {
            REMOVED: "-",
            ADDED: "+",
            UNCHANGED: " ",
        }[block.status]
        kind = {REMOVED: "red", ADDED: "green", UNCHANGED: "dim"}[block.status]
        prefix = "%s [%s %s] " % (head, side, block.number)
        wrapped = textwrap.wrap(block.text, width=wrap)
        if not wrapped:
            wrapped = ["(blank)"]
        parts: list[list[str]] = []
        for i, chunk in enumerate(wrapped):
            pad = prefix if i == 0 else " " * len(prefix)
            parts.append([kind, pad + chunk])
        cells.append(parts)
    return cells


def render_html(result: DiffResult, old_name: str, new_name: str, title: str | None = None) -> str:
    """Render a standalone HTML page with add/remove highlighting."""
    pages = [
        {"page": old_name, "blocks": [b for b in result.blocks if b.side == "old"]},
        {"page": new_name, "blocks": [b for b in result.blocks if b.side == "new"]},
    ]
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    doc_title = html.escape(title or "Diff: %s vs %s" % (old_name, new_name))

    column_html: list[str] = []
    for page in pages:
        rows = []
        for block in page["blocks"]:
            if block.status == ADDED:
                css = "added"
                marker = "+"
            elif block.status == REMOVED:
                css = "removed"
                marker = "\u2212"
            else:
                css = "unchanged"
                marker = " "
            number = str(block.number)
            rows.append(
                '<li class="%s"><span class="num">%s</span>'
                '<span class="mark">%s</span><pre>%s</pre></li>'
                % (css, html.escape(number), marker, html.escape(block.text))
            )
        column_html.append(
            '<section class="column"><h2>%s</h2><ol>%s</ol></section>'
            % (html.escape(page["page"]), "\n".join(rows))
        )

    stat_line = html.escape(result.summary if result.has_changes else "No changes found.")
    return HTML_TEMPLATE.format(
        title=doc_title,
        generated=generated,
        stat_line=stat_line,
        columns="".join(column_html),
    )


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
  :root {{ color-scheme: light dark; }}
  body {{ font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
        margin: 2rem auto; max-width: 72rem; padding: 0 1rem;
        color: #1c1c1e; background: #fafafa; }}
  @media (prefers-color-scheme: dark) {{ body {{ background: #1e1e20; color: #e8e8ea; }} }}
  header p {{ color: #6b6b70; }}
  main {{ display: flex; gap: 1.5rem; align-items: flex-start; }}
  .column {{ flex: 1 1 0; min-width: 0; }}
  .column h2 {{ font-size: 1rem; border-bottom: 2px solid #b8b8bd; padding-bottom: .25rem; }}
  ol {{ list-style: none; margin: 0; padding: 0; }}
  li {{ display: flex; gap: .5rem; padding: .3rem .5rem; border-radius: 6px;
      align-items: flex-start; }}
  li pre {{ white-space: pre-wrap; margin: 0; font-size: .9rem;
          font-family: "Consolas", "Menlo", monospace; flex: 1; min-width: 0;
          overflow-wrap: anywhere; }}
  .num {{ min-width: 2.2rem; text-align: right; color: #8a8a90; font-size: .8rem; }}
  .mark {{ min-width: 1rem; font-weight: 700; }}
  li.added {{ background: rgba(40, 167, 69, .16); }}
  li.added .mark {{ color: #22883a; }}
  li.removed {{ background: rgba(220, 53, 69, .16); }}
  li.removed .mark {{ color: #b02a37; }}
  li.unchanged {{ opacity: .55; }}
</style>
</head>
<body>
<header>
  <h1>Document Diff</h1>
  <p>{stat_line} &middot; generated {generated} &middot;
     offline stdlib diff by llm-diff-explainer (Asdale Dynamics, LLC)</p>
</header>
<main>
{columns}
</main>
</body>
</html>
"""
