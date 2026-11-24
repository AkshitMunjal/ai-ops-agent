from datetime import date

from jobs.follow_up_planner import choose_invoices_to_chase

today = date(2026, 11, 24)


def make_invoice(invoice_id):
    return {"id": invoice_id, "customer_name": "Gupta Stores", "amount_in_rupees": 5000.0, "due_date": "2026-11-01"}


def make_follow_up(invoice_id, status, created_on):
    return {"id": 1, "invoice_id": invoice_id, "status": status, "created_on": created_on}


def test_invoice_without_any_follow_up_is_chased():
    chosen = choose_invoices_to_chase([make_invoice(1)], [], today, 7)

    assert [invoice["id"] for invoice in chosen] == [1]


def test_invoice_with_an_open_draft_is_left_alone_even_if_the_draft_is_old():
    follow_ups = [make_follow_up(1, "draft", "2026-10-01")]

    chosen = choose_invoices_to_chase([make_invoice(1)], follow_ups, today, 7)

    assert chosen == []


def test_invoice_reminded_recently_is_left_alone():
    follow_ups = [make_follow_up(1, "sent", "2026-11-20"), make_follow_up(2, "cancelled", "2026-11-23")]

    chosen = choose_invoices_to_chase([make_invoice(1), make_invoice(2)], follow_ups, today, 7)

    assert chosen == []


def test_invoice_is_chased_again_after_the_waiting_days():
    follow_ups = [make_follow_up(1, "sent", "2026-11-17")]

    chosen = choose_invoices_to_chase([make_invoice(1)], follow_ups, today, 7)

    assert [invoice["id"] for invoice in chosen] == [1]