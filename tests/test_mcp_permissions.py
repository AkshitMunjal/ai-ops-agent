import anyio
import httpx
import pytest
from mcp import Client
from mcp.server.mcpserver.exceptions import ToolError
from sqlalchemy import select

from database.models import AuditLog
from database.session import open_session
from mcp_server import tools
from mcp_server.audit_wrapper import wrap_tool_with_audit
from mcp_server.server import build_server


def list_tool_names(api_key):
    async def ask_for_menu():
        server = build_server(api_key)

        async with Client(server) as mcp_client:
            tools_result = await mcp_client.list_tools()

            tool_names = []
            for tool in tools_result.tools:
                tool_names.append(tool.name)

            return tool_names

    return anyio.run(ask_for_menu)


def call_tool_as(api_key, tool_name, tool_input):
    async def make_the_call():
        server = build_server(api_key)

        async with Client(server) as mcp_client:
            return await mcp_client.call_tool(tool_name, tool_input)

    return anyio.run(make_the_call)


def read_audit_rows():
    select_all_rows = select(AuditLog)

    with open_session() as database_session:
        audit_rows = database_session.scalars(select_all_rows)
        audit_list = list(audit_rows)

    return audit_list


def test_reader_menu_has_no_write_tools():
    tool_names = list_tool_names("demo-key-reader")

    assert "get_order" in tool_names
    assert "create_draft_order" not in tool_names
    assert "mark_invoice_paid" not in tool_names


def test_order_agent_menu_has_create_but_not_mark_paid():
    tool_names = list_tool_names("demo-key-orders")

    assert "create_draft_order" in tool_names
    assert "mark_invoice_paid" not in tool_names


def test_finance_agent_menu_has_mark_paid_but_not_create():
    tool_names = list_tool_names("demo-key-finance")

    assert "mark_invoice_paid" in tool_names
    assert "create_draft_order" not in tool_names


def test_no_agent_can_see_approve_order():
    for api_key in ["demo-key-reader", "demo-key-orders", "demo-key-finance"]:
        tool_names = list_tool_names(api_key)

        assert "approve_order" not in tool_names


def test_unknown_key_cannot_start_a_server():
    with pytest.raises(ValueError):
        build_server("wrong-key")


def test_allowed_call_writes_an_audit_row(client, monkeypatch):
    def fake_get_order_by_id(order_id):
        return {"id": order_id, "status": "approved"}

    monkeypatch.setattr(tools, "get_order_by_id", fake_get_order_by_id)

    result = call_tool_as("demo-key-reader", "get_order", {"order_id": 1})
    audit_rows = read_audit_rows()

    assert result.is_error is False
    assert len(audit_rows) == 1

    first_row = audit_rows[0]

    assert first_row.who == "reader-bot"
    assert first_row.tool_name == "get_order"
    assert first_row.outcome == "allowed"


def test_failing_call_writes_an_error_row(client, monkeypatch):
    def broken_get_order_by_id(order_id):
        raise RuntimeError("the ERP exploded")

    monkeypatch.setattr(tools, "get_order_by_id", broken_get_order_by_id)

    result = call_tool_as("demo-key-reader", "get_order", {"order_id": 1})
    audit_rows = read_audit_rows()

    assert result.is_error is True
    assert len(audit_rows) == 1

    first_row = audit_rows[0]

    assert first_row.outcome == "error"


def test_wrapper_refuses_a_tool_outside_the_role_and_logs_it(client):
    sneaky_tool = wrap_tool_with_audit(tools.mark_invoice_paid, "order-bot", "order_agent")

    with pytest.raises(ToolError):
        sneaky_tool(invoice_id=1)

    audit_rows = read_audit_rows()

    assert len(audit_rows) == 1

    first_row = audit_rows[0]

    assert first_row.who == "order-bot"
    assert first_row.tool_name == "mark_invoice_paid"
    assert first_row.outcome == "refused"