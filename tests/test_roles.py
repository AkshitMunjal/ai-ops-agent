from mcp_server.roles import find_agent
from mcp_server.roles import is_tool_allowed
from mcp_server.roles import role_permissions


def test_reader_can_read_but_not_write():
    assert is_tool_allowed("reader", "get_order") is True
    assert is_tool_allowed("reader", "create_draft_order") is False
    assert is_tool_allowed("reader", "mark_invoice_paid") is False


def test_order_agent_can_create_draft_order_but_not_mark_paid():
    assert is_tool_allowed("order_agent", "create_draft_order") is True
    assert is_tool_allowed("order_agent", "mark_invoice_paid") is False


def test_finance_agent_can_mark_paid_but_not_create_order():
    assert is_tool_allowed("finance_agent", "mark_invoice_paid") is True
    assert is_tool_allowed("finance_agent", "create_draft_order") is False


def test_no_role_can_approve_orders():
    for role_name in role_permissions:
        assert is_tool_allowed(role_name, "approve_order") is False


def test_unknown_key_finds_no_agent():
    assert find_agent("wrong-key") is None


def test_unknown_role_gets_nothing():
    assert is_tool_allowed("hacker", "get_order") is False