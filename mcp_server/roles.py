read_tools = [
    "find_customer",
    "find_product",
    "get_order",
    "list_low_stock_products",
    "list_overdue_invoices",
    "get_invoice",
]

role_permissions = {
    "reader": read_tools,
    "order_agent": read_tools + ["create_draft_order"],
    "finance_agent": read_tools + ["mark_invoice_paid"],
}

agents_by_key = {
    "demo-key-reader": {"name": "reader-bot", "role": "reader"},
    "demo-key-orders": {"name": "order-bot", "role": "order_agent"},
    "demo-key-finance": {"name": "finance-bot", "role": "finance_agent"},
}


def find_agent(api_key):
    return agents_by_key.get(api_key)


def is_tool_allowed(role, tool_name):
    allowed_tools = role_permissions.get(role, [])
    return tool_name in allowed_tools