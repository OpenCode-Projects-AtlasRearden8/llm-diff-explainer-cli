# llm-diff-explainer

**Offline diff viewer with an optional plain-English explainer.**

Compare two drafts, configs, or contract versions and see add/remove highlights,
paragraph by paragraph, in your terminal and in a standalone HTML file. When you
want a friendlier read on *what changed and why it matters*, ask any
OpenAI-compatible endpoint -- by default your own local Ollama server, so your
text never has to leave your machine for the diff to work.

The diff itself always works offline: it uses only the Python standard library
(`difflib`), no dependencies, no network, no accounts.

Made by **Asdale Dynamics, LLC**. Part of a beginner-friendly family of tools:
this one complements [doc-proofreader-cli](https://github.com/dylanasdale/doc-proofreader-cli)
(document fix-ups: spelling, grammar, and clarity) -- proofread your writing,
then diff old against new.

MIT licensed. Copyright (c) 2026 Asdale Dynamics, LLC.

## Why this exists

Legal and technical documents change in ways that deserve a second look. This
tool gives you two things:

1. **A trustworthy offline diff** -- paragraph-level add/remove highlighting, in
   the terminal or in a single HTML page you can save, print, or email.
2. **A kind summary (optional)** -- "what actually changed, and one or two
   sentences on why it might matter," in plain English, from a model you choose.

## Install

Any recent Python 3 (3.9+) works. No third-party packages.

```bash
pip install .
```

## Usage

```bash
# The offline diff, always works (terminal, colored)
lldiff draft-v1.txt draft-v2.txt

# Also save a standalone HTML report with highlights
lldiff draft-v1.txt draft-v2.txt --html diff.html

# Compare configs or code line by line instead of paragraph by paragraph
lldiff config-old.ini config-new.ini --mode lines

# Plain-English explanation via local Ollama (or any other endpoint)
lldiff draft-v1.txt draft-v2.txt --explain

# Point the explainer at a different OpenAI-compatible endpoint
lldiff --explain drafts/v1.md drafts/v2.md --base-url http://192.168.1.10:11434/v1 --model mistral
```

| Option | Purpose |
| --- | --- |
| `--mode paragraphs\|lines` | Compare blank-line-separated paragraphs (default) or single lines |
| `--html FILE` | Also write a standalone HTML page with add/remove highlights |
| `--explain` | Ask an OpenAI-compatible endpoint for a friendly change summary |
| `--base-url URL` | Endpoint base URL; default `http://localhost:11434/v1` (Ollama) |
| `--model NAME` | Model name at the endpoint; default `llama3.2` |
| `--no-color` | Turn off terminal colors |
| `--diff-text-only` | Print just the machine-readable change list |

## How the explainer works

`--explain` sends only the *change list* (added/removed paragraphs) -- never the
API keys -- to a chat-completions-style endpoint and asks for a short, friendly
explanation. The default endpoint is your own computer:

- Start Ollama (`ollama serve`) and make sure you have a model
  (`ollama pull llama3.2`).
- The tool posts to `http://localhost:11434/v1/chat/completions`, the standard
  OpenAI-compatible format.
- If the endpoint is unreachable, you get a gentle warning -- the diff above it
  is complete and unaffected. Offline always works.

**Privacy note:** only a `base_url` is configurable. This tool never asks for,
stores, or transmits API keys. Keep the endpoint local (Ollama) or put an
authenticated proxy in front of a remote provider and point `--base-url` at
that proxy.

## Tests

```bash
python -m pytest
```

The suite is offline and self-contained; the HTTP layer is exercised through
stubbed handlers, never the network.

## Tools from Asdale Dynamics, LLC

| Tool | What it does |
| --- | --- |
| [doc-proofreader-cli](https://github.com/dylanasdale/doc-proofreader-cli) | Document fix-ups: spelling, grammar, and clarity |
| [llm-diff-explainer](https://github.com/dylanasdale/llm-diff-explainer-cli) | You are here: offline diff viewer with optional plain-English explainer |

Check out the book and more free guides at [dylanasdale.github.io](https://dylanasdale.github.io).

## License

MIT -- see [LICENSE](LICENSE).
