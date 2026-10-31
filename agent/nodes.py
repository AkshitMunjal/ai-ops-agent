import httpx
from langgraph.types import interrupt
from mcp.server.mcpserver.exceptions import ToolError
from agent.human_actions import approve_order_in_erp
from extraction.extractor import ExtractionError, extract_order
from extraction.matcher import match_order
from extraction.pipeline import audited_create_draft_order
from extraction.schemas import ExtractedOrder
from mcp_server.tools import OrderLineInput


def extract_node(state):
    try:
        extracted_order = extract_order(state["email_text"])
    except ExtractionError as error:
        return {"problems": [str(error)], "status": "needs_review"}

    return {"extracted_order": extracted_order.model_dump()}


def match_node(state):
    extracted_order = ExtractedOrder(**state["extracted_order"])
    matched_order = match_order(extracted_order)

    if matched_order.is_ready():
        status = "ready"
    else:
        status = "needs_review"

    return {
        "matched_order": matched_order.model_dump(),
        "problems": matched_order.problems,
        "status": status,
    }


def create_draft_node(state):
    matched_order = state["matched_order"]

    order_lines = []
    for line in matched_order["lines"]:
        order_line = OrderLineInput(
            product_id=line["product_id"],
            quantity=line["quantity"],
        )
        order_lines.append(order_line)

    try:
        draft_order = audited_create_draft_order(
            customer_id=matched_order["customer_id"],
            lines=order_lines,
        )
    except ToolError as error:
        return {"problems": [str(error)], "status": "needs_review"}

    return {"draft_order": draft_order, "status": "draft_created"}


def human_approval_node(state):
    question = {
        "question": "Approve this draft order?",
        "draft_order": state["draft_order"],
        "matched_order": state["matched_order"],
    }
    decision = interrupt(question)
    return {"decision": decision}


def approve_order_node(state):
    draft_order_id = state["draft_order"]["id"]

    try:
        approved_order = approve_order_in_erp(draft_order_id)
    except httpx.HTTPStatusError as error:
        return {"problems": [str(error)], "status": "approval_failed"}

    return {"draft_order": approved_order, "status": "approved"}


def reject_node(state):
    return {"status": "rejected"}