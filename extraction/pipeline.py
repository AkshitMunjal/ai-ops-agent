from mcp.server.mcpserver.exceptions import ToolError

from extraction.extractor import ExtractionError, extract_order
from extraction.matcher import match_order
from mcp_server.audit_wrapper import wrap_tool_with_audit
from mcp_server.tools import OrderLineInput, create_draft_order

audited_create_draft_order = wrap_tool_with_audit(
    create_draft_order, "order-bot", "order_agent"
)


def process_email(email_text):
    try:
        extracted_order = extract_order(email_text)
    except ExtractionError as error:
        return {"status": "needs_review", "problems": [str(error)]}

    matched_order = match_order(extracted_order)
    if not matched_order.is_ready():
        return {"status": "needs_review", "problems": matched_order.problems}

    order_lines = []
    for line in matched_order.lines:
        order_line = OrderLineInput(
            product_id=line.product_id,
            quantity=line.quantity,
        )
        order_lines.append(order_line)

    try:
        draft = audited_create_draft_order(
            customer_id=matched_order.customer_id,
            lines=order_lines,
        )
    except ToolError as error:
        return {"status": "needs_review", "problems": [str(error)]}

    return {"status": "draft_created", "order": draft}