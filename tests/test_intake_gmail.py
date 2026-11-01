import imaplib
from pathlib import Path

import httpx
import pytest

from intake import gmail_inbox, gmail_watcher

sample_email = Path(__file__).parent / "samples" / "email_plain.eml"


class FakeConnection:
    def __init__(self, unread_uids=b"7 8 9", folder_status="OK"):
        self.unread_uids = unread_uids
        self.folder_status = folder_status
        self.selected_readonly = None
        self.calls = []

    def select(self, folder, readonly=False):
        self.selected_readonly = readonly
        return self.folder_status, [b"1"]

    def uid(self, command, *args):
        self.calls.append((command, args))
        if command == "search":
            return "OK", [self.unread_uids]
        if command == "fetch":
            raw_email = sample_email.read_bytes()
            return "OK", [(b"1 (UID 7 BODY[] {5}", raw_email), b")"]
        return "OK", [b"done"]

    def logout(self):
        pass


@pytest.fixture
def gmail_settings(monkeypatch):
    monkeypatch.setenv("GMAIL_ADDRESS", "test@example.com")
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "abcd efgh ijkl mnop")
    monkeypatch.setenv("GMAIL_SINCE", "01-Nov-2026")
    monkeypatch.setenv("GMAIL_FOLDER", "orders")


@pytest.fixture
def fake_connection(gmail_settings, monkeypatch):
    connection = FakeConnection()
    monkeypatch.setattr(gmail_inbox, "connect_to_gmail", lambda: connection)
    return connection


def test_search_words_ask_for_unread_since_the_date_and_skip_noreply():
    words = gmail_inbox.build_search_words("01-Nov-2026")

    assert words[:3] == ["UNSEEN", "SINCE", "01-Nov-2026"]
    assert "NOT" in words
    assert "noreply" in words


def test_missing_since_date_is_refused(gmail_settings, monkeypatch):
    monkeypatch.delenv("GMAIL_SINCE")

    with pytest.raises(gmail_inbox.GmailError):
        gmail_inbox.get_since_date()


def test_missing_login_settings_are_refused(gmail_settings, monkeypatch):
    monkeypatch.delenv("GMAIL_APP_PASSWORD")

    with pytest.raises(gmail_inbox.GmailError):
        gmail_inbox.connect_to_gmail()


def test_wrong_password_gives_a_clear_error(gmail_settings, monkeypatch):
    class FakeServer:
        def __init__(self, server_name):
            pass

        def login(self, address, password):
            raise imaplib.IMAP4.error("bad password")

    monkeypatch.setattr(imaplib, "IMAP4_SSL", FakeServer)

    with pytest.raises(gmail_inbox.GmailError):
        gmail_inbox.connect_to_gmail()


def test_unknown_label_is_refused(gmail_settings):
    connection = FakeConnection(folder_status="NO")

    with pytest.raises(gmail_inbox.GmailError):
        gmail_inbox.open_folder(connection)


def test_fetch_takes_only_the_limit_and_does_not_mark_as_read(fake_connection):
    emails = gmail_inbox.fetch_unread_emails(2)

    assert [one_email["uid"] for one_email in emails] == ["7", "8"]
    assert fake_connection.selected_readonly is True
    fetch_calls = [call for call in fake_connection.calls if call[0] == "fetch"]
    assert all("PEEK" in call[1][1] for call in fetch_calls)


def test_mark_as_read_opens_the_label_for_writing(fake_connection):
    gmail_inbox.mark_as_read("7")

    assert fake_connection.selected_readonly is False
    assert ("store", ("7", "+FLAGS", "(\\Seen)")) in fake_connection.calls


def test_mark_as_failed_adds_the_label_and_marks_as_read(fake_connection):
    gmail_inbox.mark_as_failed("7")

    assert ("store", ("7", "+X-GM-LABELS", "(orders-failed)")) in fake_connection.calls
    assert ("store", ("7", "+FLAGS", "(\\Seen)")) in fake_connection.calls


def make_email(uid):
    raw_email = sample_email.read_bytes()
    return {"uid": str(uid), "message_id": f"<{uid}@example.com>", "raw_email": raw_email}


@pytest.fixture
def watcher_log(monkeypatch):
    log = {"read": [], "failed": []}
    monkeypatch.setattr(gmail_watcher, "mark_as_read", lambda uid: log["read"].append(uid))
    monkeypatch.setattr(gmail_watcher, "mark_as_failed", lambda uid: log["failed"].append(uid))
    return log


def test_handled_emails_are_marked_as_read(watcher_log, monkeypatch):
    monkeypatch.setattr(gmail_watcher, "fetch_unread_emails", lambda limit: [make_email(1), make_email(2)])
    answers = iter([
        {"id": 5, "status": "waiting_for_approval", "draft_order_id": 9, "already_seen": False},
        {"id": 5, "status": "waiting_for_approval", "draft_order_id": 9, "already_seen": True},
    ])
    monkeypatch.setattr(gmail_watcher, "submit_email_text", lambda text, message_id=None: next(answers))

    gmail_watcher.check_gmail_once()

    assert watcher_log["read"] == ["1", "2"]
    assert watcher_log["failed"] == []


def test_the_message_id_is_sent_with_the_text(watcher_log, monkeypatch):
    sent = {}

    def fake_submit(text, message_id=None):
        sent["message_id"] = message_id
        sent["text"] = text
        return {"id": 1, "status": "waiting_for_approval", "draft_order_id": 9, "already_seen": False}

    monkeypatch.setattr(gmail_watcher, "fetch_unread_emails", lambda limit: [make_email(1)])
    monkeypatch.setattr(gmail_watcher, "submit_email_text", fake_submit)

    gmail_watcher.check_gmail_once()

    assert sent["message_id"] == "<1@example.com>"
    assert "40 steel bolts M8" in sent["text"]


def test_api_down_leaves_the_email_unread(watcher_log, monkeypatch):
    def api_down(text, message_id=None):
        raise httpx.ConnectError("down")

    monkeypatch.setattr(gmail_watcher, "fetch_unread_emails", lambda limit: [make_email(1)])
    monkeypatch.setattr(gmail_watcher, "submit_email_text", api_down)

    gmail_watcher.check_gmail_once()

    assert watcher_log["read"] == []
    assert watcher_log["failed"] == []


def test_other_error_labels_the_email_as_failed(watcher_log, monkeypatch):
    def broken(text, message_id=None):
        raise ValueError("bad email")

    monkeypatch.setattr(gmail_watcher, "fetch_unread_emails", lambda limit: [make_email(1)])
    monkeypatch.setattr(gmail_watcher, "submit_email_text", broken)

    gmail_watcher.check_gmail_once()

    assert watcher_log["failed"] == ["1"]
    assert watcher_log["read"] == []


def test_stops_after_three_failures_in_a_row(watcher_log, monkeypatch):
    def broken(text, message_id=None):
        raise ValueError("bad email")

    monkeypatch.setattr(gmail_watcher, "fetch_unread_emails", lambda limit: [make_email(n) for n in range(5)])
    monkeypatch.setattr(gmail_watcher, "submit_email_text", broken)

    gmail_watcher.check_gmail_once()

    assert watcher_log["failed"] == ["0", "1", "2"]


def test_gmail_unreachable_does_not_crash(watcher_log, monkeypatch):
    def gmail_down(limit):
        raise RuntimeError("login failed")

    monkeypatch.setattr(gmail_watcher, "fetch_unread_emails", gmail_down)

    assert gmail_watcher.check_gmail_once() == 0