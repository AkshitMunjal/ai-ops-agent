import pytest

from extraction.extractor import ExtractionError, extract_order

good_reply = '{"customer_name": "Gupta Stores", "lines": [{"product_name": "bolts", "quantity": 5}]}'


def fake_llm_returning(reply_text):
    def fake_ask_llm(system_instruction, user_text):
        return reply_text

    return fake_ask_llm


def test_reads_a_good_reply(monkeypatch):
    monkeypatch.setattr("extraction.extractor.ask_llm", fake_llm_returning(good_reply))

    order = extract_order("any email text")

    assert order.customer_name == "Gupta Stores"
    assert order.lines[0].product_name == "bolts"
    assert order.lines[0].quantity == 5


def test_reads_a_reply_wrapped_in_code_fences(monkeypatch):
    fenced_reply = "```json\n" + good_reply + "\n```"
    monkeypatch.setattr("extraction.extractor.ask_llm", fake_llm_returning(fenced_reply))

    order = extract_order("any email text")

    assert order.customer_name == "Gupta Stores"


def test_refuses_a_reply_that_is_not_json(monkeypatch):
    bad_reply = "Sorry, I could not find an order in this email."
    monkeypatch.setattr("extraction.extractor.ask_llm", fake_llm_returning(bad_reply))

    with pytest.raises(ExtractionError):
        extract_order("any email text")


def test_refuses_a_quantity_of_zero(monkeypatch):
    zero_reply = '{"customer_name": "Gupta Stores", "lines": [{"product_name": "bolts", "quantity": 0}]}'
    monkeypatch.setattr("extraction.extractor.ask_llm", fake_llm_returning(zero_reply))

    with pytest.raises(ExtractionError):
        extract_order("any email text")