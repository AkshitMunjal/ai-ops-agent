from pathlib import Path

from streamlit.testing.v1 import AppTest

from ui import agent_api_client

PAGE = str(Path(__file__).resolve().parent.parent / "ui" / "pages" / "Ask_the_assistant.py")


def make_page():
    page = AppTest.from_file(PAGE, default_timeout=30)
    return page


def test_the_page_opens_with_an_empty_chat():
    page = make_page().run()

    assert not page.exception
    assert page.title[0].value == "Ask the assistant"
    assert len(page.chat_message) == 0


def test_a_question_shows_the_answer_and_what_was_looked_at(monkeypatch):
    def fake_ask(question, history):
        return {
            "answer": "Nothing is low on stock.",
            "known": True,
            "tools_used": ["list_low_stock_products"],
            "sources": [],
        }

    monkeypatch.setattr(agent_api_client, "ask_assistant", fake_ask)

    page = make_page().run()
    page.chat_input[0].set_value("What is low on stock?").run()

    assert not page.exception
    texts = [message.markdown[0].value for message in page.chat_message]
    assert texts == ["What is low on stock?", "Nothing is low on stock."]
    captions = [caption.value for caption in page.caption]
    assert "Looked at: list_low_stock_products" in captions


def test_an_unreachable_agent_service_shows_an_error_and_keeps_no_message(monkeypatch):
    import httpx

    def failing_ask(question, history):
        raise httpx.ConnectError("refused")

    monkeypatch.setattr(agent_api_client, "ask_assistant", failing_ask)

    page = make_page().run()
    page.chat_input[0].set_value("Hello?").run()

    assert not page.exception
    assert "could not be reached" in page.error[0].value
    assert page.session_state["messages"] == []
