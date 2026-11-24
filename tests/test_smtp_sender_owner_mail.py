from mailer import smtp_sender
from tests.test_smtp_sender import FakeSmtpConnection, prepare_settings


def test_owner_mail_ignores_the_test_recipient_setting(monkeypatch):
    prepare_settings(monkeypatch)
    monkeypatch.setenv("FOLLOW_UP_TEST_RECIPIENT", "me@example.com")

    smtp_sender.send_email("owner@example.com", "Daily summary", "Numbers", use_test_recipient=False)

    message = FakeSmtpConnection.sent_messages[0]
    assert message["To"] == "owner@example.com"
    assert message["Subject"] == "Daily summary"