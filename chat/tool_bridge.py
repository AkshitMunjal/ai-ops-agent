import json

import anyio

from rag.embedder import EmbeddingError
from rag.retriever import find_relevant_documents
from rag.vector_db import VectorDbError

DOCUMENT_TOOL_NAME = "search_documents"

# Tool results longer than this are cut, so one big answer cannot cost too much.
MAX_RESULT_CHARS = 6000

DOCUMENT_TOOL = {
    "type": "function",
    "function": {
        "name": DOCUMENT_TOOL_NAME,
        "description": (
            "Search the company's written policies: payment terms, returns and refunds, "
            "delivery, stock reorders, and supplier terms. Use it for questions about rules "
            "and policies. It does not know live numbers such as stock or invoices."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "What to look for, in plain words."}
            },
            "required": ["question"],
        },
    },
}


def make_llm_tools(mcp_tools):
    """Turn the MCP tools into the tool format the AI service expects."""
    llm_tools = []

    for mcp_tool in mcp_tools:
        llm_tool = {
            "type": "function",
            "function": {
                "name": mcp_tool.name,
                "description": mcp_tool.description or "",
                "parameters": mcp_tool.input_schema,
            },
        }
        llm_tools.append(llm_tool)

    llm_tools.append(DOCUMENT_TOOL)
    return llm_tools


def cut_text(text):
    if len(text) <= MAX_RESULT_CHARS:
        return text

    return text[:MAX_RESULT_CHARS] + "\n[The rest was cut because it is too long.]"


def read_arguments(call):
    """Read the tool arguments the AI wrote. Returns (arguments, problem)."""
    raw_arguments = call["function"].get("arguments") or "{}"

    try:
        arguments = json.loads(raw_arguments)
    except json.JSONDecodeError:
        return None, "The tool arguments were not valid JSON."

    if not isinstance(arguments, dict):
        return None, "The tool arguments must be a JSON object."

    return arguments, None


def make_outcome(text, kind, sources=()):
    """kind is 'data' (a real answer), 'none' (nothing found) or 'problem' (it failed)."""
    return {"text": cut_text(text), "kind": kind, "sources": list(sources)}


def read_mcp_result(result):
    if result.is_error:
        message = result.content[0].text
        return make_outcome(f"The tool failed: {message}", "problem")

    data = result.structured_content

    if isinstance(data, dict) and list(data.keys()) == ["result"]:
        data = data["result"]

    return make_outcome(json.dumps(data, default=str), "data")


def search_documents_outcome(question):
    try:
        matches = find_relevant_documents(question)
    except (VectorDbError, EmbeddingError) as error:
        return make_outcome(f"The documents could not be searched: {error}", "problem")

    if not matches:
        return make_outcome("No document is close enough to this question.", "none")

    parts = []
    sources = []

    for match in matches:
        parts.append(f"[{match['source']}]\n{match['content']}")

        if match["source"] not in sources:
            sources.append(match["source"])

    return make_outcome("\n\n".join(parts), "data", sources)


async def run_tool(mcp_client, call):
    """Run one tool call. Never raises: a failure becomes a 'problem' outcome."""
    tool_name = call["function"]["name"]
    arguments, problem = read_arguments(call)

    if problem is not None:
        return make_outcome(problem, "problem")

    if tool_name == DOCUMENT_TOOL_NAME:
        question = arguments.get("question", "")
        return await anyio.to_thread.run_sync(search_documents_outcome, question)

    try:
        result = await mcp_client.call_tool(tool_name, arguments)
    except Exception as error:
        return make_outcome(f"The tool could not be used: {error}", "problem")

    return read_mcp_result(result)
