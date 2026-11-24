import anyio
import httpx

from chat import assistant, tool_bridge
from chat.llm_tools import ChatLlmError
from cost_control.limit import SpendLimitReached


class FakeTool:
    def __init__(self, name):
        self.name = name
        self.description = f"Tool {name}"
        self.input_schema = {"type": "object", "properties": {}}


class FakeListed:
    tools = [FakeTool("list_low_stock_products"), FakeTool("get_order")]


class FakeResult:
    def __init__(self, data=None, error_text=None):
        self.is_error = error_text is not None
        self.structured_content = data
        self.content = [type("Text", (), {"text": error_text})()] if error_text else []


class FakeMcpClient:
    def __init__(self, results):
        self.results = results
        self.calls = []

    async def list_tools(self):
        return FakeListed()

    async def call_tool(self, name, arguments):
        self.calls.append((name, arguments))
        return self.results[name]


def tool_call(name, arguments="{}", call_id="call_1"):
    return {"id": call_id, "type": "function", "function": {"name": name, "arguments": arguments}}


def script_llm(monkeypatch, replies):
    """The fake AI gives these replies one after the other and remembers what it was sent."""
    sent = []
    remaining = list(replies)

    def fake_llm(messages, tools):
        sent.append({"messages": list(messages), "tools": tools})
        return remaining.pop(0)

    monkeypatch.setattr(assistant, "ask_llm_with_tools", fake_llm)
    return sent


def ask(mcp_client, question, history=None):
    async def run():
        return await assistant.answer_with_client(mcp_client, question, history)

    return anyio.run(run)


def test_a_data_question_is_answered_from_the_tool_result(monkeypatch):
    mcp_client = FakeMcpClient(
        {"list_low_stock_products": FakeResult({"result": [{"id": 3, "name": "Gloves"}]})}
    )
    sent = script_llm(
        monkeypatch,
        [
            {"content": None, "tool_calls": [tool_call("list_low_stock_products")]},
            {"content": "Gloves are low on stock."},
        ],
    )

    result = ask(mcp_client, "What is low on stock?")

    assert result["answer"] == "Gloves are low on stock."
    assert result["known"] is True
    assert result["tools_used"] == ["list_low_stock_products"]
    tool_message = sent[1]["messages"][-1]
    assert tool_message["role"] == "tool"
    assert "Gloves" in tool_message["content"]


def test_an_answer_without_any_tool_is_replaced_by_i_dont_know(monkeypatch):
    mcp_client = FakeMcpClient({})
    script_llm(monkeypatch, [{"content": "Paris is the capital of France."}])

    result = ask(mcp_client, "What is the capital of France?")

    assert result["answer"] == assistant.DONT_KNOW_TEXT
    assert result["known"] is False


def test_documents_with_no_close_match_give_i_dont_know(monkeypatch):
    monkeypatch.setattr(tool_bridge, "find_relevant_documents", lambda question: [])
    mcp_client = FakeMcpClient({})
    script_llm(
        monkeypatch,
        [
            {"content": None, "tool_calls": [tool_call("search_documents", '{"question": "weather"}')]},
            {"content": "It will be sunny."},
        ],
    )

    result = ask(mcp_client, "What is the weather?")

    assert result["answer"] == assistant.DONT_KNOW_TEXT
    assert result["known"] is False


def test_a_policy_answer_names_its_source_document(monkeypatch):
    matches = [
        {"source": "payment_terms.md", "chunk_index": 0, "content": "Pay within 30 days.", "similarity": 0.6}
    ]
    monkeypatch.setattr(tool_bridge, "find_relevant_documents", lambda question: matches)
    mcp_client = FakeMcpClient({})
    script_llm(
        monkeypatch,
        [
            {"content": None, "tool_calls": [tool_call("search_documents", '{"question": "pay"}')]},
            {"content": "Invoices are due in 30 days (payment_terms.md)."},
        ],
    )

    result = ask(mcp_client, "When must customers pay?")

    assert result["known"] is True
    assert result["sources"] == ["payment_terms.md"]


def test_an_empty_list_from_the_erp_is_a_real_answer(monkeypatch):
    mcp_client = FakeMcpClient({"list_low_stock_products": FakeResult({"result": []})})
    script_llm(
        monkeypatch,
        [
            {"content": None, "tool_calls": [tool_call("list_low_stock_products")]},
            {"content": "Nothing is low on stock."},
        ],
    )

    result = ask(mcp_client, "What is low on stock?")

    assert result["known"] is True
    assert result["answer"] == "Nothing is low on stock."


def test_a_tool_failure_is_reported_not_guessed(monkeypatch):
    mcp_client = FakeMcpClient({"get_order": FakeResult(error_text="The ERP is not reachable.")})
    script_llm(
        monkeypatch,
        [
            {"content": None, "tool_calls": [tool_call("get_order", '{"order_id": 1}')]},
            {"content": "Order 1 is approved."},
        ],
    )

    result = ask(mcp_client, "Status of order 1?")

    assert result["known"] is False
    assert "not reachable" in result["answer"]
    assert "approved" not in result["answer"]


def test_a_tool_that_raises_does_not_crash_the_chat(monkeypatch):
    class BrokenClient(FakeMcpClient):
        async def call_tool(self, name, arguments):
            raise RuntimeError("connection lost")

    script_llm(
        monkeypatch,
        [
            {"content": None, "tool_calls": [tool_call("get_order", '{"order_id": 1}')]},
            {"content": "Done."},
        ],
    )

    result = ask(BrokenClient({}), "Status of order 1?")

    assert result["known"] is False
    assert "connection lost" in result["answer"]


def test_bad_tool_arguments_are_given_back_to_the_ai(monkeypatch):
    mcp_client = FakeMcpClient({})
    sent = script_llm(
        monkeypatch,
        [
            {"content": None, "tool_calls": [tool_call("get_order", "not json")]},
            {"content": "Sorry."},
        ],
    )

    result = ask(mcp_client, "Status of order 1?")

    assert mcp_client.calls == []
    assert "not valid JSON" in sent[1]["messages"][-1]["content"]
    assert result["known"] is False


def test_the_spend_limit_gives_a_clear_message(monkeypatch):
    def limit_reached(messages, tools):
        raise SpendLimitReached("Daily spend limit of $1 reached")

    monkeypatch.setattr(assistant, "ask_llm_with_tools", limit_reached)

    result = ask(FakeMcpClient({}), "Anything?")

    assert "Daily spend limit" in result["answer"]
    assert result["known"] is False


def test_an_ai_service_failure_gives_a_clear_message(monkeypatch):
    def failing(messages, tools):
        raise ChatLlmError("The AI service failed: timeout")

    monkeypatch.setattr(assistant, "ask_llm_with_tools", failing)

    result = ask(FakeMcpClient({}), "Anything?")

    assert "could not answer right now" in result["answer"]


def test_the_ai_cannot_loop_forever(monkeypatch):
    mcp_client = FakeMcpClient({"list_low_stock_products": FakeResult({"result": []})})
    endless = [
        {"content": None, "tool_calls": [tool_call("list_low_stock_products")]}
        for _ in range(assistant.MAX_STEPS)
    ]
    script_llm(monkeypatch, endless)

    result = ask(mcp_client, "What is low on stock?")

    assert result["known"] is False
    assert len(mcp_client.calls) == assistant.MAX_STEPS


def test_only_the_last_few_plain_messages_are_sent_as_history(monkeypatch):
    sent = script_llm(monkeypatch, [{"content": "ok"}])
    history = [{"role": "user", "content": f"question {number}"} for number in range(10)]
    history.append({"role": "tool", "content": "should be dropped"})
    history.append({"role": "assistant", "content": ""})

    ask(FakeMcpClient({}), "latest question", history)

    messages = sent[0]["messages"]
    assert messages[0]["role"] == "system"
    assert messages[-1] == {"role": "user", "content": "latest question"}
    assert len(messages) == 1 + assistant.HISTORY_LIMIT + 1
    assert all(message["role"] != "tool" for message in messages)


def test_the_ai_gets_the_read_tools_and_the_document_tool(monkeypatch):
    sent = script_llm(monkeypatch, [{"content": "ok"}])

    ask(FakeMcpClient({}), "hello")

    names = [tool["function"]["name"] for tool in sent[0]["tools"]]
    assert names == ["list_low_stock_products", "get_order", "search_documents"]
