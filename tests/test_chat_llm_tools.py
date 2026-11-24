import httpx
import pytest

from chat import llm_tools
from cost_control.limit import SpendLimitReached


class FakeResponse:
    def __init__(self, data):
        self.data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self.data


def test_the_message_and_the_tools_are_sent_and_the_usage_is_saved(monkeypatch):
    saved = []
    sent = {}
    monkeypatch.setattr(llm_tools, "check_spend_limit", lambda: None)
    monkeypatch.setattr(llm_tools, "record_usage", lambda model, usage: saved.append(usage))

    def fake_post(url, headers=None, json=None, timeout=None):
        sent["body"] = json
        return FakeResponse({"choices": [{"message": {"content": "hi"}}], "usage": {"cost": 0.001}})

    monkeypatch.setattr(llm_tools.httpx, "post", fake_post)

    message = llm_tools.ask_llm_with_tools([{"role": "user", "content": "x"}], [{"type": "function"}])

    assert message == {"content": "hi"}
    assert sent["body"]["tools"] == [{"type": "function"}]
    assert saved == [{"cost": 0.001}]


def test_the_spend_limit_stops_the_call(monkeypatch):
    def limit_reached():
        raise SpendLimitReached("limit")

    monkeypatch.setattr(llm_tools, "check_spend_limit", limit_reached)

    with pytest.raises(SpendLimitReached):
        llm_tools.ask_llm_with_tools([], [])


def test_a_web_error_becomes_a_chat_error(monkeypatch):
    monkeypatch.setattr(llm_tools, "check_spend_limit", lambda: None)

    def failing_post(*args, **kwargs):
        raise httpx.ReadTimeout("slow")

    monkeypatch.setattr(llm_tools.httpx, "post", failing_post)

    with pytest.raises(llm_tools.ChatLlmError):
        llm_tools.ask_llm_with_tools([], [])


def test_an_answer_without_choices_is_refused(monkeypatch):
    monkeypatch.setattr(llm_tools, "check_spend_limit", lambda: None)
    monkeypatch.setattr(llm_tools, "record_usage", lambda model, usage: None)
    monkeypatch.setattr(llm_tools.httpx, "post", lambda *a, **k: FakeResponse({"error": "bad"}))

    with pytest.raises(llm_tools.ChatLlmError):
        llm_tools.ask_llm_with_tools([], [])
