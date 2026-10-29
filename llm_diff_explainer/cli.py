"""Command-line entry point for llm-diff-explainer.

    lldiff old.txt new.txt

The diff itself is always offline and computed with the Python standard
library.  Providing --explain additionally asks a configurable
OpenAI-compatible endpoint (default: a local Ollama server) for a short,
friendly explanation.  Failure to reach the endpoint is a soft warning, not
an error, because the diff still works offline.
"""

from __future__ import annotations

import argparse
import sys

from .diffcore import compute_diff
from .explain import DEFAULT_BASE_URL, DEFAULT_MODEL, ExplainError, explain
from .render import render_html, render_terminal


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lldiff",
        description=(
            "Compare two documents (drafts, configs, contract versions...) "
            "paragraph by paragraph, offline. Optionally ask a local, "
            "OpenAI-compatible endpoint to explain the changes in plain English."
        ),
        epilog=(
            "Examples:\n"
            "  lldiff draft1.txt draft2.txt\n"
            "  lldiff v1.cnf v2.cnf --mode lines\n"
            "  lldiff old.md new.md --html diff.html --explain\n"
            "  lldiff old.md new.md --explain --base-url http://localhost:11434/v1"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("old_file", help="original document (first version)")
    parser.add_argument("new_file", help="revised document (second version)")
    parser.add_argument(
        "--mode",
        choices=("paragraphs", "lines"),
        default="paragraphs",
        help="compare units: blank-line-separated paragraphs (default) or lines",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="disable terminal colors",
    )
    parser.add_argument(
        "--html",
        metavar="FILE",
        help="also write a standalone HTML page with highlights to FILE",
    )
    parser.add_argument(
        "--explain",
        action="store_true",
        help="ask an OpenAI-compatible endpoint (default: Ollama) for a "
        "plain-English summary of the changes",
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        metavar="URL",
        help="OpenAI-compatible base URL (no API keys ever; default: %s)"
        % DEFAULT_BASE_URL,
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        metavar="NAME",
        help="model name at the endpoint (default: %s)" % DEFAULT_MODEL,
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        metavar="SECONDS",
        help="seconds to wait for the explainer (default: 60)",
    )
    parser.add_argument(
        "--diff-text-only",
        action="store_true",
        help="print only the machine-readable change list (used for the explainer)",
    )
    return parser


def build_diff_summary(result) -> str:
    """Paragraph-oriented change list fed to the explainer and printed by
    --diff-text-only."""
    lines = [result.summary, ""]
    for block in result.blocks:
        status = {
            "added": "+",
            "removed": "-",
            "unchanged": " ",
        }[block.status]
        lines.append("%s [%s %d] %s" % (status, block.side, block.number, block.text))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        with open(args.old_file, encoding="utf-8") as fh:
            old_text = fh.read()
        with open(args.new_file, encoding="utf-8") as fh:
            new_text = fh.read()
    except OSError as exc:
        print("error reading input files: %s" % exc, file=sys.stderr)
        return 2

    result = compute_diff(old_text, new_text, mode=args.mode)

    if args.diff_text_only:
        print(build_diff_summary(result))
        return 0

    print(render_terminal(result, args.old_file, args.new_file, colors=not args.no_color))

    if args.html:
        try:
            with open(args.html, "w", encoding="utf-8") as fh:
                fh.write(render_html(result, args.old_file, args.new_file))
        except OSError as exc:
            print("error writing HTML file: %s" % exc, file=sys.stderr)
        else:
            print("\nHTML report saved to %s" % args.html)

    if args.explain:
        print("")
        if not result.has_changes:
            print("Nothing to explain: the documents match.")
        else:
            try:
                answer = explain(
                    diff_text=build_diff_summary(result),
                    base_url=args.base_url,
                    model=args.model,
                    timeout=args.timeout,
                )
            except ExplainError as exc:
                print("Explainer unavailable (%s)." % exc, file=sys.stderr)
                print(
                    "The offline diff above is complete and unaffected. "
                    "Start Ollama, or point --base-url at another "
                    "OpenAI-compatible endpoint."
                )
            else:
                print("Plain-English explanation")
                print("-------------------------")
                print(answer)

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
