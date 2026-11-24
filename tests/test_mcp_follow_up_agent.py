import httpx

from mcp_server import tools
from tests.test_mcp_permissions import call_tool_as, list_tool_names, read_audit_rows

all_keys = ["demo-key-reader", "demo-key-orders", "demo-key-finance", "demo-key-stock", "demo-key-followup"]
follow_up_key = "demo-key-followup"
follow_up_input = {"invoice_id": 1, "subject": "Payment reminder", "body": "Please pay."}


def test_follow_up_agent_can_create_drafts_but_nothing_else_that_writes():
    tool_names = list_tool_names(follow_up_key)

    assert "create_draft_follow_up" in tool_names
    assert "list_follow_ups" in tool_names
    assert "create_draft_order" not in tool_names
    assert "create_draft_reorder" not in tool_names
    assert "mark_invoice_paid" not in tool_names


def test_other_agents_cannot_create_follow_up_drafts_but_can_read_them():
    for api_key in ["demo-key-reader", "demo-key-orders", "demo-key-finance", "demo-key-stock"]:
        tool_names = list_tool_names(api_key)

        assert "create_draft_follow_up" not in tool_names
        assert "list_follow_ups" in tool_names


def test_no_agent_can_send_or_cancel_a_follow_up():
    for api_key in all_keys:
        tool_names = list_tool_names(api_key)

        assert "send_follow_up" not in tool_names
        assert "cancel_follow_up" not in tool_names
        assert "send_email" not in tool_names


def test_follow_up_agent_creates_a_draft_and_it_is_logged(client, monkeypatch):
    monkeypatch.setattr(tools, "create_follow_up", lambda invoice_id, subject, body: {"id": 1, "status": "draft"})

    result = call_tool_as(follow_up_key, "create_draft_follow_up", follow_up_input)
    audit_rows = read_audit_rows()

    assert result.is_error is False
    assert audit_rows[0].who == "followup-bot"
    assert audit_rows[0].tool_name == "create_draft_follow_up"
    assert audit_rows[0].outcome == "allowed"


def test_stock_agent_cannot_create_a_follow_up_and_it_is_logged(client):
    result = call_tool_as("demo-key-stock", "create_draft_follow_up", follow_up_input)
    audit_rows = read_audit_rows()

    assert result.is_error is True
    assert audit_rows[0].who == "stock-bot"
    assert audit_rows[0].outcome == "refused"


def test_an_erp_refusal_is_explained_to_the_agent(client, monkeypatch):
    def fake_create_refused(invoice_id, subject, body):
        request = httpx.Request("POST", "http://test/follow-ups")
        response = httpx.Response(409, json={"detail": "Only unpaid invoices can be followed up"}, request=request)
        raise httpx.HTTPStatusError("conflict", request=request, response=response)

    monkeypatch.setattr(tools, "create_follow_up", fake_create_refused)

    result = call_tool_as(follow_up_key, "create_draft_follow_up", follow_up_input)
    audit_rows = read_audit_rows()

    assert result.is_error is True
    assert "Only unpaid invoices can be followed up" in result.content[0].text
    assert audit_rows[0].outcome == "error"