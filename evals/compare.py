from extraction.extractor import ExtractionError, extract_order


def clean_lines(lines):
    cleaned_lines = []
    for product_name, quantity in lines:
        cleaned_name = product_name.strip().lower()
        cleaned_lines.append((cleaned_name, quantity))

    cleaned_lines.sort()
    return cleaned_lines


def run_case(case):
    try:
        order = extract_order(case["email"])
    except ExtractionError as error:
        return False, f"the reply could not be read: {error}"

    got_customer = order.customer_name.strip().lower()
    expected_customer = case["expected_customer"].strip().lower()

    got_lines = []
    for line in order.lines:
        got_lines.append((line.product_name, line.quantity))

    if got_customer != expected_customer:
        return False, f"customer: expected {case['expected_customer']}, got {order.customer_name}"

    if clean_lines(got_lines) != clean_lines(case["expected_lines"]):
        return False, f"lines: expected {case['expected_lines']}, got {got_lines}"

    return True, ""