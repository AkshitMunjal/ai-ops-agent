from mcp_server import tools
from mcp_server.audit_wrapper import wrap_tool_with_audit
from mcp_server.audited_server import AuditedServer
from mcp_server.roles import find_agent
from mcp_server.roles import is_tool_allowed

all_tools = [
    tools.find_customer,
    tools.find_product,
    tools.list_low_stock_products,
    tools.list_overdue_invoices,
    tools.list_draft_reorders,
    tools.list_open_reorders,
    tools.list_follow_ups,
    tools.get_order,
    tools.get_invoice,
    tools.create_draft_order,
    tools.create_draft_reorder,
    tools.create_draft_follow_up,
    tools.mark_invoice_paid,
]


def build_server(api_key):
    agent = find_agent(api_key)

    if agent is None:
        raise ValueError("Unknown agent key. The server will not start.")

    agent_name = agent["name"]
    role = agent["role"]

    server = AuditedServer("ERP", agent_name, role)

    for tool_function in all_tools:
        tool_name = tool_function.__name__

        if not is_tool_allowed(role, tool_name):
            continue

        wrapped_tool = wrap_tool_with_audit(tool_function, agent_name, role)
        server.add_visible_tool(wrapped_tool)

    return server