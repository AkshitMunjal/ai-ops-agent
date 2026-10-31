from mcp_server.erp_client import search_customers, search_products
from extraction.schemas import MatchedLine, MatchedOrder


def match_customer(customer_name):
    found_customers = search_customers(customer_name)

    if len(found_customers) == 1:
        return found_customers[0], None

    if len(found_customers) == 0:
        return None, f"No customer found for '{customer_name}'."

    return None, f"More than one customer matches '{customer_name}'."


def match_product(product_name):
    found_products = search_products(product_name)

    if len(found_products) == 1:
        return found_products[0], None

    if len(found_products) == 0:
        return None, f"No product found for '{product_name}'."

    return None, f"More than one product matches '{product_name}'."


def match_order(extracted_order):
    problems = []
    customer_id = None
    customer_name = None

    customer, customer_problem = match_customer(extracted_order.customer_name)
    if customer_problem:
        problems.append(customer_problem)
    else:
        customer_id = customer["id"]
        customer_name = customer["name"]

    matched_lines = []
    for line in extracted_order.lines:
        product, product_problem = match_product(line.product_name)
        if product_problem:
            problems.append(product_problem)
            continue

        matched_line = MatchedLine(
            product_id=product["id"],
            product_name=product["name"],
            quantity=line.quantity,
        )
        matched_lines.append(matched_line)

    return MatchedOrder(
        customer_id=customer_id,
        customer_name=customer_name,
        lines=matched_lines,
        problems=problems,
    )