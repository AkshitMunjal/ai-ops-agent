from datetime import date

from jobs.summary_builder import build_summary

today = date(2026, 11, 24)

low_stock = [{"name": "PVC Pipe", "stock_quantity": 5, "reorder_level": 20}]
overdue = [
    {"id": 2, "customer_name": "Gupta Stores", "amount_in_rupees": 18500.0, "due_date": "2026-11-02"},
    {"id": 3, "customer_name": "Sharma Traders", "amount_in_rupees": 6250.5, "due_date": "2026-11-10"},
]
follow_ups = [{"status": "draft"}, {"status": "sent"}, {"status": "cancelled"}]


def test_subject_has_the_date():
    summary = build_summary([], [], [], [], today)

    assert summary["subject"] == "Daily summary, 24 Nov 2026"


def test_stock_part_lists_low_products_and_waiting_reorders():
    summary = build_summary(low_stock, [{"id": 1}], [], [], today)

    assert "1 product(s) at or below the reorder level" in summary["body"]
    assert "PVC Pipe: 5 left (reorder level 20)" in summary["body"]
    assert "1 draft reorder(s) waiting for approval" in summary["body"]


def test_invoice_part_shows_count_total_and_each_invoice():
    summary = build_summary([], [], overdue, [], today)

    assert "2 overdue invoice(s), Rs 24,750.50 in total" in summary["body"]
    assert "Invoice 2, Gupta Stores, Rs 18,500.00, due 02 Nov 2026" in summary["body"]


def test_only_draft_reminders_count_as_waiting():
    summary = build_summary([], [], [], follow_ups, today)

    assert "1 reminder draft(s) waiting to be sent" in summary["body"]


def test_waiting_for_a_person_adds_reorders_and_reminders():
    summary = build_summary(low_stock, [{"id": 1}, {"id": 2}], overdue, follow_ups, today)

    assert "Waiting for a person to decide: 3" in summary["body"]


def test_a_quiet_day_says_so():
    summary = build_summary([], [], [], [], today)

    assert "No product is at or below its reorder level" in summary["body"]
    assert "No invoice is overdue" in summary["body"]
    assert "Waiting for a person to decide: 0" in summary["body"]