from jobs import follow_up_writer

invoice = {
    "id": 7,
    "customer_name": "Gupta Stores",
    "amount_in_rupees": 12500.0,
    "due_date": "2026-11-06",
}

good_ai_body = (
    "Dear Gupta Stores,\n\nInvoice 7 for Rs 12,500 was due on 06 Nov 2026. "
    "Please pay it, or reply if you already have.\n\nAccounts Team"
)


def test_a_correct_ai_text_is_used(monkeypatch):
    monkeypatch.setattr(follow_up_writer, "ask_llm", lambda instruction, text: good_ai_body)

    email = follow_up_writer.write_follow_up_email(invoice)

    assert email["written_by"] == "ai"
    assert email["body"] == good_ai_body
    assert email["subject"] == "Payment reminder: invoice 7"


def test_the_ai_is_given_the_real_facts(monkeypatch):
    seen = {}

    def fake_ask_llm(instruction, text):
        seen["text"] = text
        return good_ai_body

    monkeypatch.setattr(follow_up_writer, "ask_llm", fake_ask_llm)

    follow_up_writer.write_follow_up_email(invoice)

    assert "Invoice number: 7" in seen["text"]
    assert "Rs 12,500.00" in seen["text"]
    assert "06 Nov 2026" in seen["text"]


def test_a_wrong_amount_in_the_ai_text_falls_back_to_the_fixed_text(monkeypatch):
    wrong_body = good_ai_body.replace("12,500", "15,000")
    monkeypatch.setattr(follow_up_writer, "ask_llm", lambda instruction, text: wrong_body)

    email = follow_up_writer.write_follow_up_email(invoice)

    assert email["written_by"] == "template"
    assert "12,500.00" in email["body"]


def test_a_missing_due_date_in_the_ai_text_falls_back_to_the_fixed_text(monkeypatch):
    vague_body = "Dear Gupta Stores,\n\nInvoice 7 for Rs 12500 is late. Please pay.\n\nAccounts Team"
    monkeypatch.setattr(follow_up_writer, "ask_llm", lambda instruction, text: vague_body)

    email = follow_up_writer.write_follow_up_email(invoice)

    assert email["written_by"] == "template"


def test_an_ai_failure_falls_back_to_the_fixed_text(monkeypatch):
    def broken_ask_llm(instruction, text):
        raise RuntimeError("daily limit reached")

    monkeypatch.setattr(follow_up_writer, "ask_llm", broken_ask_llm)

    email = follow_up_writer.write_follow_up_email(invoice)

    assert email["written_by"] == "template"
    assert follow_up_writer.facts_are_in_text(invoice, email["body"])


def test_amount_check_accepts_different_writing_but_not_wrong_numbers():
    assert follow_up_writer.amount_is_in_text(12500.0, "Rs. 12,500.00")
    assert follow_up_writer.amount_is_in_text(12500.0, "INR 12500")
    assert follow_up_writer.amount_is_in_text(1250.5, "Rs 1,250.50")
    assert not follow_up_writer.amount_is_in_text(12500.0, "Rs 112,500")
    assert not follow_up_writer.amount_is_in_text(12500.0, "Rs 12,501")