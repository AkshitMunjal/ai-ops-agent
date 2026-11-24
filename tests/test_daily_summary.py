import httpx
import pytest

from jobs import daily_summary
from jobs.daily_summary import DailySummaryError, make_and_send_daily_summary
from mailer.smtp_sender import MailError
from mcp_server import tools
from tests.test_mcp_permissions import read_audit_rows


def install_fakes(monkeypatch):
    sent_emails = []

    def fake_send_email(to_address, subject, body, use_test_recipient=True):
        sent_emails.append(
            {"to": to_address, "subject": subject, "body": body, "use_test_recipient": use_test_recipient}
        )

    monkeypatch.setattr(tools, "get_low_stock_products", lambda: [])
    monkeypatch.setattr(tools, "get_purchase_orders", lambda status: [])
    monkeypatch.setattr(tools, "get_overdue_invoices", lambda: [])
    monkeypatch.setattr(tools, "get_follow_ups", lambda: [])
    monkeypatch.setattr(daily_summary, "send_email", fake_send_email)

    return sent_emails


def test_summary_is_emailed_to_the_owner(client, monkeypatch):
    sent_emails = install_fakes(monkeypatch)
    monkeypatch.setenv("SUMMARY_RECIPIENT", "owner@example.com")

    outcome = make_and_send_daily_summary()

    assert outcome["sent_to"] == "owner@example.com"
    assert len(sent_emails) == 1
    assert sent_emails[0]["to"] == "owner@example.com"
    assert sent_emails[0]["subject"].startswith("Daily summary")
    assert sent_emails[0]["use_test_recipient"] is False


def test_nothing_is_emailed_when_no_owner_address_is_set(client, monkeypatch):
    sent_emails = install_fakes(monkeypatch)
    monkeypatch.delenv("SUMMARY_RECIPIENT", raising=False)

    outcome = make_and_send_daily_summary()

    assert outcome["sent_to"] is None
    assert "Daily summary for" in outcome["body"]
    assert sent_emails == []


def test_erp_down_stops_the_summary_with_a_clear_error(client, monkeypatch):
    sent_emails = install_fakes(monkeypatch)
    monkeypatch.setenv("SUMMARY_RECIPIENT", "owner@example.com")

    def erp_is_down():
        raise httpx.ConnectError("down")

    monkeypatch.setattr(tools, "get_overdue_invoices", erp_is_down)

    with pytest.raises(DailySummaryError) as error_info:
        make_and_send_daily_summary()

    assert "not reachable" in str(error_info.value)
    assert sent_emails == []


def test_a_mail_failure_is_not_hidden(client, monkeypatch):
    install_fakes(monkeypatch)
    monkeypatch.setenv("SUMMARY_RECIPIENT", "owner@example.com")

    def broken_send_email(to_address, subject, body, use_test_recipient=True):
        raise MailError("The email could not be sent: network down")

    monkeypatch.setattr(daily_summary, "send_email", broken_send_email)

    with pytest.raises(MailError):
        make_and_send_daily_summary()


def test_the_summary_only_reads_and_is_logged_as_the_summary_bot(client, monkeypatch):
    install_fakes(monkeypatch)
    monkeypatch.delenv("SUMMARY_RECIPIENT", raising=False)

    make_and_send_daily_summary()
    audit_rows = read_audit_rows()

    tool_names = []
    for audit_row in audit_rows:
        assert audit_row.who == "summary-bot"
        assert audit_row.outcome == "allowed"
        tool_names.append(audit_row.tool_name)

    assert tool_names == [
        "list_low_stock_products",
        "list_draft_reorders",
        "list_overdue_invoices",
        "list_follow_ups",
    ]