"""Optional plain-English explainer, backed by any OpenAI-compatible chat API.

The client speaks the standard OpenAI "chat.completions" wire format using only
urllib, so there are no dependencies and no bundled SDKs.  The default target is
a local Ollama server (http://localhost:11434/v1), which needs no API key.

Only a base_url is ever configured.  This tool never asks for, stores, or sends
API keys: Ollama and other local runtimes reject or ignore keys, and remote
providers that do require keys are outside this tool's threat model.  If a user
wants a key-gated endpoint they should put an authenticated proxy in front of it
and point --base-url at the proxy.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

DEFAULT_BASE_URL = "http://localhost:11434/v1"
DEFAULT_MODEL = "llama3.2"
DEFAULT_TIMEOUT = 60.0

EXPLAIN_PROMPT = """You are a friendly explainer. Two versions of a document were \
compared, and the machine-generated summary of the changes is below. In plain \
English, like you are talking to a friend: (1) describe what actually changed, \
(2) explain in a sentence or two why that change might matter. Be kind and \
never condescending. Keep it short: at most six sentences. Do not invent \
changes that are not in the summary.

CHANGES:
{diff_text}
"""


class ExplainError(RuntimeError):
    """Raised when the explainer endpoint could not produce an answer."""


def explain(
    diff_text: str,
    base_url: str = DEFAULT_BASE_URL,
    model: str = DEFAULT_MODEL,
    timeout: float = DEFAULT_TIMEOUT,
) -> str:
    """Ask the configured endpoint for a friendly summary of the changes.

    Raises ExplainError with a human-readable message when anything goes
    wrong; callers should catch it and fall back to the offline-only view.
    """
    if not diff_text.strip():
        raise ExplainError("There are no changes to explain.")
    if base_url.endswith("/"):
        base_url = base_url[:-1]
    url = base_url + "/chat/completions"

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You explain text changes in plain, warm English. "
                "You are concise and accurate.",
            },
            {"role": "user", "content": EXPLAIN_PROMPT.format(diff_text=diff_text)},
        ],
        "stream": False,
    }
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise ExplainError(
            "The endpoint returned HTTP %d. Make sure %s is running and the "
            "path is correct." % (exc.code, base_url)
        ) from exc
    except urllib.error.URLError as exc:
        raise ExplainError(
            "Could not reach %s (%s). Start Ollama or pass --base-url to a "
            "different OpenAI-compatible endpoint." % (base_url, exc.reason)
        ) from exc
    except (TimeoutError, json.JSONDecodeError) as exc:
        raise ExplainError("The endpoint replied with something unreadable: %s" % exc) from exc

    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ExplainError(
            "The reply did not contain a chat completion message."
        ) from exc

    if not isinstance(content, str) or not content.strip():
        raise ExplainError("The endpoint returned an empty answer.")
    return content.strip()
