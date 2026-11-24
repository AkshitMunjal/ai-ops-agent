import smtplib

import pytest

from mailer import smtp_sender


class FakeSmtpConnection:
    sent_messages = []
    logins = []

    def __init__(self, server, port, timeout=None):
        pass

    def __enter__(self):
        return self

    def __exit__(self, error_type, error, traceback):
        return False

    def login(self, address, password):
        FakeSmtpConnection.logins.append((address, password))

    def send_message(self, message):
        FakeSmtpConnection.sent_messages.append(message)


def prepare_settings(monkeypatch):
    FakeSmtpConnection.sent_messages = []
    FakeSmtpConnection.logins = []
    monkeypatch.setenv("GMAIL_ADDRESS", "accounts@example.com")
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "abcd efgh ijkl mnop")
    monkeypatch.delenv("FOLLOW_UP_TEST_RECIPIENT", raising=False)
    monkeypatch.setattr(smtplib, "SMTP_SSL", FakeSmtpConnection)


def test_email_is_sent_to_the_customer(monkeypatch):
    prepare_settings(monkeypatch)

    smtp_sender.send_email("customer@example.com", "Reminder", "Dear customer")

    message = FakeSmtpConnection.sent_messages[0]
    assert message["To"] == "customer@example.com"
    assert message["From"] == "accounts@example.com"
    assert message["Subject"] == "Reminder"
    assert "Dear customer" in message.get_content()
    assert FakeSmtpConnection.logins == [("accounts@example.com", "abcdefghijklmnop")]


def test_test_recipient_catches_every_email(monkeypatch):
    prepare_settings(monkeypatch)
    monkeypatch.setenv("FOLLOW_UP_TEST_RECIPIENT", "me@example.com")

    smtp_sender.send_email("customer@example.com", "Reminder", "Dear customer")

    message = FakeSmtpConnection.sent_messages[0]
    assert message["To"] == "me@example.com"
    assert "customer@example.com" in message["Subject"]


def test_missing_login_settings_are_refused(monkeypatch):
    prepare_settings(monkeypatch)
    monkeypatch.delenv("GMAIL_APP_PASSWORD")

    with pytest.raises(smtp_sender.MailError):
        smtp_sender.send_email("customer@example.com", "Reminder", "Dear customer")

    assert FakeSmtpConnection.sent_messages == []


def test_a_failing_mail_server_gives_a_clear_error(monkeypatch):
    prepare_settings(monkeypatch)

    def broken_login(self, address, password):
        raise smtplib.SMTPAuthenticationError(535, b"bad password")

    monkeypatch.setattr(FakeSmtpConnection, "login", broken_login)

    with pytest.raises(smtp_sender.MailError) as error_info:
        smtp_sender.send_email("customer@example.com", "Reminder", "Dear customer")

    assert "could not be sent" in str(error_info.value)