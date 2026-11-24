import httpx

from mcp_server import tools
from tests.test_mcp_permissions import call_tool_as, list_tool_names, read_audit_rows

all_keys = ["demo-key-reader", "demo-key-orders", "demo-key-finance", "demo-key-stock"]
stock_key = "demo-key-stock"
reorder_input = {"supplier_id": 1, "lines": [{"product_id": 1, "quantity": 35}]}


def test_stock_agent_menu_has_the_reorder_tool_but_no_other_write_tools():
    tool_names = list_tool_names(stock_key)

    assert "create_draft_reorder" in tool_names
    assert "list_draft_reorders" in tool_names
    assert "create_draft_order" not in tool_names
    assert "mark_invoice_paid" not in tool_names


def test_other_roles_cannot_see_the_reorder_tool_but_can_read_draft_reorders():
    for api_key in ["demo-key-reader", "demo-key-orders", "demo-key-finance"]:
        tool_names = list_tool_names(api_key)

        assert "create_draft_reorder" not in tool_names
        assert "list_draft_reorders" in tool_names


def test_no_agent_can_approve_or_cancel_a_purchase_order():
    for api_key in all_keys:
        tool_names = list_tool_names(api_key)

        assert "approve_purchase_order" not in tool_names
        assert "cancel_purchase_order" not in tool_names


def test_stock_agent_creates_a_draft_reorder_and_it_is_logged(client, monkeypatch):
    def fake_create_purchase_order(supplier_id, lines):
        return {"id": 1, "status": "draft"}

    monkeypatch.setattr(tools, "create_purchase_order", fake_create_purchase_order)

    result = call_tool_as(stock_key, "create_draft_reorder", reorder_input)
    audit_rows = read_audit_rows()

    assert result.is_error is False
    assert len(audit_rows) == 1
    assert audit_rows[0].who == "stock-bot"
    assert audit_rows[0].tool_name == "create_draft_reorder"
    assert audit_rows[0].outcome == "allowed"


def test_reader_cannot_create_a_draft_reorder_and_it_is_logged(client):
    result = call_tool_as("demo-key-reader", "create_draft_reorder", reorder_input)
    audit_rows = read_audit_rows()

    assert result.is_error is True
    assert len(audit_rows) == 1
    assert audit_rows[0].who == "reader-bot"
    assert audit_rows[0].outcome == "refused"


def test_an_erp_refusal_is_explained_to_the_agent(client, monkeypatch):
    def fake_create_refused(supplier_id, lines):
        request = httpx.Request("POST", "http://test/purchase-orders")
        response = httpx.Response(
            400,
            json={"detail": "Product does not belong to this supplier"},
            request=request,
        )
        raise httpx.HTTPStatusError("bad request", request=request, response=response)

    monkeypatch.setattr(tools, "create_purchase_order", fake_create_refused)

    result = call_tool_as(stock_key, "create_draft_reorder", reorder_input)
    audit_rows = read_audit_rows()

    assert result.is_error is True
    assert "does not belong to this supplier" in result.content[0].text
    assert audit_rows[0].outcome == "error"