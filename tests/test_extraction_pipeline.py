from mcp.server.mcpserver.exceptions import ToolError

from extraction.extractor import ExtractionError
from extraction.pipeline import process_email
from extraction.schemas import ExtractedOrder, MatchedLine, MatchedOrder

extracted_order = ExtractedOrder(
    customer_name="Gupta Stores",
    lines=[{"product_name": "bolts", "quantity": 5}],
)

ready_order = MatchedOrder(
    customer_id=2,
    customer_name="Gupta Stores",
    lines=[MatchedLine(product_id=1, product_name="Steel Bolts", quantity=5)],
    problems=[],
)

order_with_problem = MatchedOrder(
    customer_id=2,
    customer_name="Gupta Stores",
    lines=[],
    problems=["No product found for 'gold bars'."],
)


def fake_extract(email_text):
    return extracted_order


def fake_match_ready(order):
    return ready_order


def fake_match_with_problem(order):
    return order_with_problem


def test_good_email_creates_a_draft(monkeypatch):
    create_calls = []

    def fake_create(**tool_input):
        create_calls.append(tool_input)
        return {"id": 3, "status": "draft"}

    monkeypatch.setattr("extraction.pipeline.extract_order", fake_extract)
    monkeypatch.setattr("extraction.pipeline.match_order", fake_match_ready)
    monkeypatch.setattr("extraction.pipeline.audited_create_draft_order", fake_create)

    result = process_email("any email text")

    assert result["status"] == "draft_created"
    assert result["order"]["id"] == 3
    assert len(create_calls) == 1
    assert create_calls[0]["customer_id"] == 2
    assert create_calls[0]["lines"][0].product_id == 1
    assert create_calls[0]["lines"][0].quantity == 5


def test_email_with_a_problem_needs_review_and_creates_nothing(monkeypatch):
    create_calls = []

    def fake_create(**tool_input):
        create_calls.append(tool_input)
        return {"id": 3, "status": "draft"}

    monkeypatch.setattr("extraction.pipeline.extract_order", fake_extract)
    monkeypatch.setattr("extraction.pipeline.match_order", fake_match_with_problem)
    monkeypatch.setattr("extraction.pipeline.audited_create_draft_order", fake_create)

    result = process_email("any email text")

    assert result["status"] == "needs_review"
    assert "gold bars" in result["problems"][0]
    assert create_calls == []


def test_failed_extraction_needs_review(monkeypatch):
    def fake_extract_fails(email_text):
        raise ExtractionError("The model reply was not a valid order")

    monkeypatch.setattr("extraction.pipeline.extract_order", fake_extract_fails)

    result = process_email("any email text")

    assert result["status"] == "needs_review"
    assert "not a valid order" in result["problems"][0]


def test_refused_draft_creation_needs_review(monkeypatch):
    def fake_create_refused(**tool_input):
        raise ToolError("The ERP said no.")

    monkeypatch.setattr("extraction.pipeline.extract_order", fake_extract)
    monkeypatch.setattr("extraction.pipeline.match_order", fake_match_ready)
    monkeypatch.setattr("extraction.pipeline.audited_create_draft_order", fake_create_refused)

    result = process_email("any email text")

    assert result["status"] == "needs_review"
    assert "The ERP said no." in result["problems"][0]