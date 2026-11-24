from datetime import date, timedelta

import httpx
import pytest

from jobs import follow_up_writer
from jobs.follow_up_check import FollowUpCheckError, run_follow_up_check
from mcp_server import tools
from tests.test_mcp_permissions import read_audit_rows

days_ago_text = (date.today() - timedelta(days=20)).isoformat()


def make_invoice(invoice_id, amount=5000.0):
    return {
        "id": invoice_id,
        "order_id": invoice_id,
        "customer_name": "Gupta Stores",
        "customer_email": "gupta@example.com",
        "amount_in_rupees": amount,
        "due_date": days_ago_text,
        "status": "unpaid",
    }


def install_fakes(monkeypatch, overdue_invoices, follow_ups):
    saved_calls = []

    def fake_create_follow_up(invoice_id, subject, body):
        saved_calls.append({"invoice_id": invoice_id, "subject": subject, "body": body})
        return {"id": 200 + invoice_id, "status": "draft"}

    monkeypatch.setattr(tools, "get_overdue_invoices", lambda: overdue_invoices)
    monkeypatch.setattr(tools, "get_follow_ups", lambda: follow_ups)
    monkeypatch.setattr(tools, "create_follow_up", fake_create_follow_up)

    def ai_is_down(instruction, text):
        raise RuntimeError("no AI in tests")

    monkeypatch.setattr(follow_up_writer, "ask_llm", ai_is_down)

    return saved_calls


def test_one_draft_is_created_for_each_overdue_invoice(client, monkeypatch):
    saved_calls = install_fakes(monkeypatch, [make_invoice(1), make_invoice(2, 900.0)], [])

    outcome = run_follow_up_check()

    assert len(outcome["created"]) == 2
    assert outcome["failed"] == []
    assert saved_calls[0]["invoice_id"] == 1
    assert "Dear Gupta Stores" in saved_calls[0]["body"]
    assert "5,000.00" in saved_calls[0]["body"]
    assert saved_calls[1]["invoice_id"] == 2
    assert outcome["created"][0]["written_by"] == "template"


def test_invoices_with_a_recent_or_open_follow_up_are_skipped(client, monkeypatch):
    today_text = date.today().isoformat()
    follow_ups = [
        {"id": 1, "invoice_id": 1, "status": "sent", "created_on": today_text},
        {"id": 2, "invoice_id": 2, "status": "draft", "created_on": "2026-01-01"},
    ]
    saved_calls = install_fakes(monkeypatch, [make_invoice(1), make_invoice(2), make_invoice(3)], follow_ups)

    run_follow_up_check()

    assert [call["invoice_id"] for call in saved_calls] == [3]


def test_nothing_overdue_means_no_drafts(client, monkeypatch):
    saved_calls = install_fakes(monkeypatch, [], [])

    outcome = run_follow_up_check()

    assert outcome == {"created": [], "failed": []}
    assert saved_calls == []


def test_one_refused_draft_does_not_stop_the_others(client, monkeypatch):
    saved_calls = install_fakes(monkeypatch, [make_invoice(1), make_invoice(2)], [])

    def fake_create_with_one_refusal(invoice_id, subject, body):
        if invoice_id == 1:
            request = httpx.Request("POST", "http://test/follow-ups")
            response = httpx.Response(409, json={"detail": "already has a draft"}, request=request)
            raise httpx.HTTPStatusError("conflict", request=request, response=response)

        saved_calls.append({"invoice_id": invoice_id})
        return {"id": 202, "status": "draft"}

    monkeypatch.setattr(tools, "create_follow_up", fake_create_with_one_refusal)

    outcome = run_follow_up_check()

    assert len(outcome["created"]) == 1
    assert outcome["failed"][0]["invoice_id"] == 1
    assert "already has a draft" in outcome["failed"][0]["reason"]


def test_erp_down_stops_the_job_with_a_clear_error(client, monkeypatch):
    saved_calls = install_fakes(monkeypatch, [], [])

    def erp_is_down():
        raise httpx.ConnectError("down")

    monkeypatch.setattr(tools, "get_overdue_invoices", erp_is_down)

    with pytest.raises(FollowUpCheckError) as error_info:
        run_follow_up_check()

    assert "not reachable" in str(error_info.value)
    assert saved_calls == []


def test_every_step_is_logged_as_the_follow_up_bot(client, monkeypatch):
    install_fakes(monkeypatch, [make_invoice(1)], [])

    run_follow_up_check()
    audit_rows = read_audit_rows()

    tool_names = []
    for audit_row in audit_rows:
        assert audit_row.who == "followup-bot"
        assert audit_row.outcome == "allowed"
        tool_names.append(audit_row.tool_name)

    assert tool_names == ["list_overdue_invoices", "list_follow_ups", "create_draft_follow_up"]