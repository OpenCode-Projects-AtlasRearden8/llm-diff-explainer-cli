"""Tests for the OpenAI-compatible explainer client.

The HTTP layer is exercised with stubbed urllib handlers only: the test suite
never touches the network.
"""

import io
import json
import urllib.error
import urllib.request

import pytest

from llm_diff_explainer.explain import (
    DEFAULT_BASE_URL,
    ExplainError,
    explain,
)


class FakeResponse:
    def __init__(self, body: bytes, status: int = 200):
        self.body = body
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.body


def call_body(calls):
    return calls["data"]


def completion(text="All good!"):
    return json.dumps(
        {
            "choices": [
                {"message": {"role": "assistant", "content": text}}
            ]
        }
    ).encode("utf-8")


@pytest.fixture
def stub_urlopen(monkeypatch):
    calls = {}

    def _install(handler):
        def fake_urlopen(request, timeout=None):
            calls["url"] = request.full_url
            calls["data"] = request.data
            calls["headers"] = request.headers
            calls["timeout"] = timeout
            return handler(request)

        monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
        return calls

    return _install


def test_explain_sends_openai_format(stub_urlopen):
    calls = stub_urlopen(lambda req: FakeResponse(completion("Friendly answer.")))

    answer = explain("LATE FEES paragraph added.", base_url=DEFAULT_BASE_URL, model="llama3.2")

    assert answer == "Friendly answer."
    assert calls["url"] == DEFAULT_BASE_URL + "/chat/completions"
    payload = json.loads(calls["data"].decode("utf-8"))
    assert payload["model"] == "llama3.2"
    assert payload["stream"] is False
    roles = [m["role"] for m in payload["messages"]]
    assert roles == ["system", "user"]
    assert "LATE FEES paragraph added." in payload["messages"][-1]["content"]


def test_explain_strips_trailing_slash(stub_urlopen):
    calls = stub_urlopen(lambda req: FakeResponse(completion("ok")))
    explain("x", base_url=DEFAULT_BASE_URL + "/")
    assert calls["url"] == DEFAULT_BASE_URL + "/chat/completions"


def test_explain_rejects_empty_diff(stub_urlopen):
    stub_urlopen(lambda req: FakeResponse(completion("ok")))
    with pytest.raises(ExplainError, match="no changes"):
        explain("   \n")


def test_explain_http_error_is_soft(stub_urlopen):
    def raise_http(req):
        raise urllib.error.HTTPError(req.full_url, 500, "boom", None, io.BytesIO(b""))

    stub_urlopen(raise_http)
    with pytest.raises(ExplainError, match=r"HTTP 500"):
        explain("changes", base_url=DEFAULT_BASE_URL)


def test_explain_unreachable_is_soft(stub_urlopen):
    def raise_url_error(req):
        raise urllib.error.URLError("connection refused")

    stub_urlopen(raise_url_error)
    with pytest.raises(ExplainError, match="Could not reach"):
        explain("changes")


def test_explain_malformed_reply_is_soft(stub_urlopen):
    stub_urlopen(lambda req: FakeResponse(b"not json at all"))
    with pytest.raises(ExplainError):
        explain("changes")


def test_explain_missing_choices_is_soft(stub_urlopen):
    stub_urlopen(lambda req: FakeResponse(json.dumps({"foo": 1}).encode()))
    with pytest.raises(ExplainError, match="chat completion"):
        explain("changes")


def test_explain_empty_answer_is_soft(stub_urlopen):
    stub_urlopen(lambda req: FakeResponse(completion("  ")))
    with pytest.raises(ExplainError, match="empty"):
        explain("changes")


def test_explain_prompt_mentions_two_versions(stub_urlopen):
    calls = stub_urlopen(lambda req: FakeResponse(completion("ok")))
    explain("one paragraph added")
    payload = json.loads(calls["data"].decode())
    user_text = payload["messages"][-1]["content"]
    assert "what actually changed" in user_text
    assert "one paragraph added" in user_text
