from typing import Any

import httpx
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import BaseModel

from mcp_server.erp_client import create_order
from mcp_server.erp_client import get_invoice_by_id
from mcp_server.erp_client import get_low_stock_products
from mcp_server.erp_client import get_order_by_id
from mcp_server.erp_client import get_overdue_invoices
from mcp_server.erp_client import mark_paid_in_erp
from mcp_server.erp_client import search_customers
from mcp_server.erp_client import search_products


class OrderLineInput(BaseModel):
    product_id: int
    quantity: int


def find_customer(name: str) -> list[dict]:
    """Find customers whose name contains the given text. Returns each customer's id, name and email."""
    customers = search_customers(name)
    return customers


def find_product(name: str) -> list[dict]:
    """Find products whose name contains the given text. Returns each product's id, name, price, stock quantity, reorder level and supplier id."""
    products = search_products(name)
    return products


def list_low_stock_products() -> list[dict]:
    """List products whose stock is at or below their reorder level. Returns each product's id, name, stock quantity, reorder level and supplier id."""
    products = get_low_stock_products()
    return products


def list_overdue_invoices() -> list[dict]:
    """List unpaid invoices that are past their due date. Returns each invoice's id, order id, customer name and email, amount and due date."""
    invoices = get_overdue_invoices()
    return invoices


def get_order(order_id: int) -> dict[str, Any]:
    """Get one order by its id. Returns its status, customer name, order lines and order total."""
    try:
        order = get_order_by_id(order_id)
    except httpx.HTTPStatusError as error:
        if error.response.status_code == 404:
            raise ToolError(f"Order {order_id} was not found.")
        raise ToolError("The ERP API returned an error.")
    return order


def get_invoice(invoice_id: int) -> dict[str, Any]:
    """Get one invoice by its id. Returns its order id, customer name and email, amount, due date and status."""
    try:
        invoice = get_invoice_by_id(invoice_id)
    except httpx.HTTPStatusError as error:
        if error.response.status_code == 404:
            raise ToolError(f"Invoice {invoice_id} was not found.")
        raise ToolError("The ERP API returned an error.")
    return invoice


def create_draft_order(customer_id: int, lines: list[OrderLineInput]) -> dict[str, Any]:
    """Create a DRAFT order for a customer. A person must approve it before it counts. Each line needs a product id and a quantity. Prices come from the ERP and cannot be set here."""
    lines_as_dictionaries = []

    for line in lines:
        line_dictionary = line.model_dump()
        lines_as_dictionaries.append(line_dictionary)

    try:
        created_order = create_order(customer_id, lines_as_dictionaries)
    except httpx.HTTPStatusError as error:
        response_body = error.response.json()
        detail = response_body.get("detail")
        raise ToolError(f"The ERP refused the order: {detail}")

    return created_order


def mark_invoice_paid(invoice_id: int) -> dict[str, Any]:
    """Mark an UNPAID invoice as paid, after the payment has been received. Only unpaid invoices can be changed."""
    try:
        paid_invoice = mark_paid_in_erp(invoice_id)
    except httpx.HTTPStatusError as error:
        response_body = error.response.json()
        detail = response_body.get("detail")
        raise ToolError(f"The ERP refused the change: {detail}")
    return paid_invoice