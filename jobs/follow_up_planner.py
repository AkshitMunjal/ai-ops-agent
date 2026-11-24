from datetime import date


def choose_invoices_to_chase(overdue_invoices, follow_ups, today, days_between_reminders):
    invoice_ids_to_leave_alone = []

    for follow_up in follow_ups:
        invoice_id = follow_up["invoice_id"]

        if follow_up["status"] == "draft":
            invoice_ids_to_leave_alone.append(invoice_id)
            continue

        created_on = date.fromisoformat(follow_up["created_on"])
        days_since_follow_up = (today - created_on).days

        if days_since_follow_up < days_between_reminders:
            invoice_ids_to_leave_alone.append(invoice_id)

    invoices_to_chase = []

    for invoice in overdue_invoices:
        if invoice["id"] in invoice_ids_to_leave_alone:
            continue

        invoices_to_chase.append(invoice)

    return invoices_to_chase