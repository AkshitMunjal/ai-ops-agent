import httpx
import pytest

from ui import agent_api_client


def make_response(status_code, body):
    request = httpx.Request("POST", "http://test/chat")
    return httpx.Response(status_code, json=body, request=request)


def test_the_question_and_history_are_posted_to_the_chat_address(monkeypatch):
    sent = {}

    def fake_post(url, json=None, timeout=None):
        sent["url"] = url
        sent["json"] = json
        sent["timeout"] = timeout
        return make_response(200, {"answer": "ok", "known": True, "tools_used": [], "sources": []})

    monkeypatch.setattr(httpx, "post", fake_post)

    answer = agent_api_client.ask_assistant("What is low?", [{"role": "user", "content": "hi"}])

    assert answer["answer"] == "ok"
    assert sent["url"].endswith("/chat")
    assert sent["json"] == {"question": "What is low?", "history": [{"role": "user", "content": "hi"}]}
    assert sent["timeout"] >= 60


def test_an_error_answer_raises(monkeypatch):
    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: make_response(500, {"detail": "boom"}))

    with pytest.raises(httpx.HTTPStatusError):
        agent_api_client.ask_assistant("What is low?", [])
