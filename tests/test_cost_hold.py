import os

import pytest

from intake import gmail_watcher, inbox_watcher, submit
from intake.submit import TryLaterError
from tests.test_intake_gmail import make_email, watcher_log
from tests.test_intake_watcher import add_emails, inbox


class FakeLimitResponse:
    status_code = 429

    def json(self):
        return {"detail": "Daily spend limit of $1 reached"}


def always_try_later(text, message_id=None):
    raise TryLaterError("Daily spend limit of $1 reached")


def test_a_429_from_the_api_becomes_a_try_later_error(monkeypatch):
    monkeypatch.setattr(submit.httpx, "post", lambda *args, **kwargs: FakeLimitResponse())

    with pytest.raises(TryLaterError) as error:
        submit.submit_email_text("any email", "<a@example.com>")

    assert "Daily spend limit" in str(error.value)


def test_gmail_email_stays_unread_when_the_limit_is_reached(watcher_log, monkeypatch):
    monkeypatch.setattr(gmail_watcher, "fetch_unread_emails", lambda limit: [make_email(1)])
    monkeypatch.setattr(gmail_watcher, "submit_email_text", always_try_later)

    gmail_watcher.check_gmail_once()

    assert watcher_log["read"] == []
    assert watcher_log["failed"] == []


def test_folder_email_stays_in_the_inbox_when_the_limit_is_reached(inbox, monkeypatch):
    monkeypatch.setattr(inbox_watcher, "submit_email_text", always_try_later)
    add_emails(inbox, 1)

    inbox_watcher.check_inbox_once()

    assert "email_0.eml" in os.listdir(inbox)
    assert os.listdir(inbox / "done") == []
    assert os.listdir(inbox / "failed") == []