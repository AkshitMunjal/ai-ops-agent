from jobs.text_format import format_amount
from jobs.text_format import format_date


def make_stock_lines(low_stock_products, draft_reorders):
    lines = ["STOCK"]

    if len(low_stock_products) == 0:
        lines.append("- No product is at or below its reorder level.")
    else:
        lines.append(f"- {len(low_stock_products)} product(s) at or below the reorder level:")
        for product in low_stock_products:
            lines.append(f"  - {product['name']}: {product['stock_quantity']} left (reorder level {product['reorder_level']})")

    lines.append(f"- {len(draft_reorders)} draft reorder(s) waiting for approval.")
    return lines


def make_invoice_lines(overdue_invoices):
    lines = ["INVOICES"]

    if len(overdue_invoices) == 0:
        lines.append("- No invoice is overdue.")
        return lines

    total_amount = 0.0
    for invoice in overdue_invoices:
        total_amount = total_amount + invoice["amount_in_rupees"]

    lines.append(f"- {len(overdue_invoices)} overdue invoice(s), Rs {format_amount(total_amount)} in total:")

    for invoice in overdue_invoices:
        amount_text = format_amount(invoice["amount_in_rupees"])
        due_text = format_date(invoice["due_date"])
        lines.append(f"  - Invoice {invoice['id']}, {invoice['customer_name']}, Rs {amount_text}, due {due_text}")

    return lines


def make_reminder_lines(follow_ups):
    waiting_count = 0

    for follow_up in follow_ups:
        if follow_up["status"] == "draft":
            waiting_count = waiting_count + 1

    return ["PAYMENT REMINDERS", f"- {waiting_count} reminder draft(s) waiting to be sent."]


def build_summary(low_stock_products, draft_reorders, overdue_invoices, follow_ups, today):
    waiting_for_a_person = len(draft_reorders)

    for follow_up in follow_ups:
        if follow_up["status"] == "draft":
            waiting_for_a_person = waiting_for_a_person + 1

    lines = [f"Daily summary for {today.strftime('%d %b %Y')}", ""]
    lines.append(f"Waiting for a person to decide: {waiting_for_a_person}")
    lines.append("")
    lines.extend(make_stock_lines(low_stock_products, draft_reorders))
    lines.append("")
    lines.extend(make_invoice_lines(overdue_invoices))
    lines.append("")
    lines.extend(make_reminder_lines(follow_ups))

    subject = f"Daily summary, {today.strftime('%d %b %Y')}"
    body = "\n".join(lines)
    return {"subject": subject, "body": body}