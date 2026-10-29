"""llm-diff-explainer: offline diff viewer with optional friendly explainer.

MIT licensed. Made by Asdale Dynamics, LLC.
"""

from .diffcore import ADDED, REMOVED, UNCHANGED, Block, DiffResult, compute_diff
from .explain import ExplainError, explain
from .render import render_html, render_terminal

__version__ = "0.1.0"
__all__ = [
    "ADDED",
    "REMOVED",
    "UNCHANGED",
    "Block",
    "DiffResult",
    "ExplainError",
    "compute_diff",
    "explain",
    "render_html",
    "render_terminal",
]
