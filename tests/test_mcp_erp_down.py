import httpx

from mcp_server import tools
from tests.test_mcp_permissions import call_tool_as, read_audit_rows


def test_erp_down_gives_a_clear_message_and_an_error_row(client, monkeypatch):
    def erp_is_off(order_id):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(tools, "get_order_by_id", erp_is_off)

    result = call_tool_as("demo-key-reader", "get_order", {"order_id": 1})
    audit_rows = read_audit_rows()

    assert result.is_error is True
    assert "not reachable" in result.content[0].text
    assert len(audit_rows) == 1
    assert audit_rows[0].outcome == "error"


def test_erp_timeout_gives_the_same_clear_message(client, monkeypatch):
    def erp_is_too_slow(order_id):
        raise httpx.ReadTimeout("took too long")

    monkeypatch.setattr(tools, "get_order_by_id", erp_is_too_slow)

    result = call_tool_as("demo-key-reader", "get_order", {"order_id": 1})

    assert result.is_error is True
    assert "not reachable" in result.content[0].text