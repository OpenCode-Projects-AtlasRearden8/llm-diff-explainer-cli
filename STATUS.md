# STATUS.md -- llm-diff-explainer-cli

Last updated: 2026-10-29 (v0.1.0)

## What was built

`llm-diff-explainer` (`lldiff`): an offline diff viewer for drafts, configs, and
contract versions, with an optional plain-English explainer. Built for
beginner-friendly, local-first publishing by Asdale Dynamics, LLC.

Features:

- **Offline paragraph diff, always works.** Standard-library `difflib` only; no
  dependencies, no network needed. Blank-line-separated paragraphs are the
  default comparison unit; `--mode lines` compares single lines (useful for
  config files).
- **Terminal view.** Side-by-side colored columns: `-` red for removed, `+`
  green for added, dimmed for unchanged, wrapped so long paragraphs aren't cut
  off (`--no-color` for plain terminals/pipes).
- **HTML report.** `--html diff.html` writes a single self-contained file
  (embedded CSS, escaped content, light/dark aware) that can be emailed or
  archived. A generated sample is in `docs/example-diff.html`.
- **Optional plain-English explainer.** `--explain` sends only the change list
  to any OpenAI-compatible `chat/completions` endpoint -- default
  `http://localhost:11434/v1` (local Ollama), any `--base-url` works. Endpoint
  unreachable is a soft warning; the offline diff is never affected.
- **No secrets, ever.** Only a `base_url` is configured; the tool never asks
  for, stores, or sends API keys.
- Complements `doc-proofreader-cli`: proofread the writing, then diff old
  against new.

Layout:

```
llm_diff_explainer/
  diffcore.py   # stdlib diff engine (paragraphs/lines -> typed blocks)
  render.py     # terminal (ANSI) and standalone HTML renderers
  explain.py    # OpenAI-compatible client (stdlib urllib, no SDK)
  cli.py        # argparse entry point (console script: lldiff)
tests/          # pytest suite + text fixtures (contracts, configs)
docs/           # generated sample HTML diff
```

## How to run it

```bash
pip install .            # installs the `lldiff` console script (Python 3.9+)

lldiff draft-v1.txt draft-v2.txt                    # offline terminal diff
lldiff v1 v2 --html diff.html                       # + standalone HTML report
lldiff cfg-old.ini cfg-new.ini --mode lines         # line-by-line mode
lldiff v1 v2 --explain                              # + Ollama explanation
lldiff v1 v2 --explain --base-url http://host:11434/v1 --model mistral
```

Ollama users: `ollama serve`, `ollama pull llama3.2`, then `lldiff ... --explain`.

## Verification results

- `python3 -m pytest`: **40 passed**, 0 failed (offline; HTTP stubbed).
- `python3 -m pyflakes llm_diff_explainer tests`: clean.
- Manual run of the CLI against the bundled contract and config fixtures: diff,
  `--diff-text-only`, `--html`, and `--explain` fallback behavior all verified;
  exit codes 0 (success/soft-fallback) and 2 (unreadable inputs) verified.
- `pip install .` verified: the `lldiff` console script installs and runs.
- Explainer wire format verified against requests mimicking the
  `chat/completions` schema: `{model, stream, messages[system, user]}`.

## Known gaps

- The explainer only sees whole added/removed paragraphs/lines, not word-level
  rewording inside a "kept" paragraph; two versions of the same paragraph with
  changed numbers read as remove + add (which is honest, but coarse). A finer
  (token-level) mode could be added later.
- HTML columns are independent `<ol>` lists; rows are not pixel-aligned
  vertically (they align naturally in practice, but there is no row pairing).
- Terminal view assumes a monospace font and lights/dark themes both readable;
  colorblind users can rely on the `-`/`+` markers instead of color.
- The explainer has no retry/backoff and no streaming; a single request with a
  timeout.
- No Windows color handling beyond ANSI (fine for Windows 10+ terminals);
  `--no-color` is the safe fallback.
- No CI config in this repo (pytest can be pointed at by any runner).

## License and credits

MIT -- `LICENSE` with `Copyright (c) 2026 Asdale Dynamics, LLC`. README credits
Asdale Dynamics, LLC; hub: https://dylanasdale.github.io
