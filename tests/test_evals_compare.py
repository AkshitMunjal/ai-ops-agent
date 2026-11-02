from evals.compare import clean_lines, run_case
from extraction.extractor import ExtractionError
from extraction.schemas import ExtractedLine, ExtractedOrder

case = {
    "name": "sample",
    "email": "any email",
    "expected_customer": "Gupta Stores",
    "expected_lines": [("steel bolts M8", 40), ("copper wire 2.5mm", 3)],
}


def make_order(customer_name, lines):
    extracted_lines = []
    for product_name, quantity in lines:
        extracted_lines.append(ExtractedLine(product_name=product_name, quantity=quantity))

    return ExtractedOrder(customer_name=customer_name, lines=extracted_lines)


def fake_extractor_returning(order):
    def fake_extract_order(email_text):
        return order

    return fake_extract_order


def test_clean_lines_ignores_capitals_spaces_and_order():
    first = clean_lines([("Steel Bolts M8 ", 40), ("copper wire", 3)])
    second = clean_lines([("copper wire", 3), ("steel bolts m8", 40)])

    assert first == second


def test_a_matching_answer_passes(monkeypatch):
    order = make_order("gupta stores", [("Copper Wire 2.5mm", 3), ("Steel Bolts M8", 40)])
    monkeypatch.setattr("evals.compare.extract_order", fake_extractor_returning(order))

    passed, note = run_case(case)

    assert passed is True
    assert note == ""


def test_a_wrong_customer_fails(monkeypatch):
    order = make_order("Rakesh", [("steel bolts M8", 40), ("copper wire 2.5mm", 3)])
    monkeypatch.setattr("evals.compare.extract_order", fake_extractor_returning(order))

    passed, note = run_case(case)

    assert passed is False
    assert "customer" in note


def test_a_wrong_quantity_fails(monkeypatch):
    order = make_order("Gupta Stores", [("steel bolts M8", 4), ("copper wire 2.5mm", 3)])
    monkeypatch.setattr("evals.compare.extract_order", fake_extractor_returning(order))

    passed, note = run_case(case)

    assert passed is False
    assert "lines" in note


def test_a_missing_line_fails(monkeypatch):
    order = make_order("Gupta Stores", [("steel bolts M8", 40)])
    monkeypatch.setattr("evals.compare.extract_order", fake_extractor_returning(order))

    passed, note = run_case(case)

    assert passed is False


def test_an_unreadable_reply_fails_with_a_note(monkeypatch):
    def broken_extractor(email_text):
        raise ExtractionError("not json")

    monkeypatch.setattr("evals.compare.extract_order", broken_extractor)

    passed, note = run_case(case)

    assert passed is False
    assert "could not be read" in note