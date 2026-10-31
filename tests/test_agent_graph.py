import httpx
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from agent.graph import build_graph
from extraction.extractor import ExtractionError
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


def install_fakes(monkeypatch, match_function=fake_match_ready):
    calls = {"create": [], "approve": []}

    def fake_create(**tool_input):
        calls["create"].append(tool_input)
        return {"id": 7, "status": "draft"}

    def fake_approve(order_id):
        calls["approve"].append(order_id)
        return {"id": order_id, "status": "approved"}

    monkeypatch.setattr("agent.nodes.extract_order", fake_extract)
    monkeypatch.setattr("agent.nodes.match_order", match_function)
    monkeypatch.setattr("agent.nodes.audited_create_draft_order", fake_create)
    monkeypatch.setattr("agent.nodes.approve_order_in_erp", fake_approve)
    return calls


def start_flow():
    graph = build_graph(InMemorySaver())
    config = {"configurable": {"thread_id": "test-email"}}
    first_result = graph.invoke({"email_text": "any email"}, config)
    return graph, config, first_result


def test_flow_pauses_for_a_human_after_creating_the_draft(monkeypatch):
    calls = install_fakes(monkeypatch)

    graph, config, first_result = start_flow()

    waiting_item = first_result["__interrupt__"][0]
    assert waiting_item.value["draft_order"]["id"] == 7
    assert len(calls["create"]) == 1
    assert calls["approve"] == []


def test_approve_answer_approves_the_order(monkeypatch):
    calls = install_fakes(monkeypatch)
    graph, config, first_result = start_flow()

    final_result = graph.invoke(Command(resume="approve"), config)

    assert final_result["status"] == "approved"
    assert calls["approve"] == [7]
    assert len(calls["create"]) == 1


def test_reject_answer_does_not_approve(monkeypatch):
    calls = install_fakes(monkeypatch)
    graph, config, first_result = start_flow()

    final_result = graph.invoke(Command(resume="reject"), config)

    assert final_result["status"] == "rejected"
    assert calls["approve"] == []


def test_unclear_answer_does_not_approve(monkeypatch):
    calls = install_fakes(monkeypatch)
    graph, config, first_result = start_flow()

    final_result = graph.invoke(Command(resume="maybe"), config)

    assert final_result["status"] == "rejected"
    assert calls["approve"] == []


def test_order_with_a_problem_stops_without_asking_or_creating(monkeypatch):
    calls = install_fakes(monkeypatch, match_function=fake_match_with_problem)

    graph, config, first_result = start_flow()

    assert "__interrupt__" not in first_result
    assert first_result["status"] == "needs_review"
    assert "gold bars" in first_result["problems"][0]
    assert calls["create"] == []


def test_failed_extraction_stops_with_needs_review(monkeypatch):
    calls = install_fakes(monkeypatch)

    def fake_extract_fails(email_text):
        raise ExtractionError("The model reply was not a valid order")

    monkeypatch.setattr("agent.nodes.extract_order", fake_extract_fails)

    graph, config, first_result = start_flow()

    assert "__interrupt__" not in first_result
    assert first_result["status"] == "needs_review"
    assert calls["create"] == []


def test_failed_approval_is_reported(monkeypatch):
    install_fakes(monkeypatch)

    def fake_approve_fails(order_id):
        request = httpx.Request("POST", "http://test/orders/7/approve")
        response = httpx.Response(409, request=request)
        raise httpx.HTTPStatusError("conflict", request=request, response=response)

    monkeypatch.setattr("agent.nodes.approve_order_in_erp", fake_approve_fails)
    graph, config, first_result = start_flow()

    final_result = graph.invoke(Command(resume="approve"), config)

    assert final_result["status"] == "approval_failed"