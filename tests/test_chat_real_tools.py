import anyio
import httpx
from mcp import Client

from chat import assistant
from mcp_server import tools
from mcp_server.server import build_server


def tool_call(name, arguments="{}"):
    return {"id": "call_1", "type": "function", "function": {"name": name, "arguments": arguments}}


def run_chat(question, replies, monkeypatch):
    remaining = list(replies)
    monkeypatch.setattr(assistant, "ask_llm_with_tools", lambda messages, llm_tools: remaining.pop(0))

    async def run():
        server = build_server(assistant.chat_agent_key)

        async with Client(server) as mcp_client:
            return await assistant.answer_with_client(mcp_client, question)

    return anyio.run(run)


def test_the_chat_bot_reads_the_erp_through_the_real_mcp_server(client, monkeypatch):
    monkeypatch.setattr(
        tools, "get_low_stock_products", lambda: [{"id": 7, "name": "Notebook", "stock_quantity": 2}]
    )

    result = run_chat(
        "What is low on stock?",
        [
            {"content": None, "tool_calls": [tool_call("list_low_stock_products")]},
            {"content": "Notebook is low."},
        ],
        monkeypatch,
    )

    assert result["known"] is True
    assert result["tools_used"] == ["list_low_stock_products"]


def test_the_chat_bot_cannot_use_a_write_tool(client, monkeypatch):
    result = run_chat(
        "Mark invoice 1 as paid",
        [
            {"content": None, "tool_calls": [tool_call("mark_invoice_paid", '{"invoice_id": 1}')]},
            {"content": "Done, it is paid."},
        ],
        monkeypatch,
    )

    assert result["known"] is False
    assert "Done" not in result["answer"]


def test_the_chat_bot_sees_only_read_tools():
    async def list_names():
        server = build_server(assistant.chat_agent_key)

        async with Client(server) as mcp_client:
            listed = await mcp_client.list_tools()
            return [tool.name for tool in listed.tools]

    names = anyio.run(list_names)

    assert "list_low_stock_products" in names
    assert "get_invoice" in names
    assert not any(name.startswith("create_") or name.startswith("mark_") for name in names)


def test_an_erp_that_is_down_gives_a_clear_answer_not_a_guess(client, monkeypatch):
    def erp_down(order_id):
        raise httpx.ConnectError("refused")

    monkeypatch.setattr(tools, "get_order_by_id", erp_down)

    result = run_chat(
        "Status of order 1?",
        [
            {"content": None, "tool_calls": [tool_call("get_order", '{"order_id": 1}')]},
            {"content": "Order 1 is shipped."},
        ],
        monkeypatch,
    )

    assert result["known"] is False
    assert "shipped" not in result["answer"]
