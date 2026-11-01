import os
import shutil
from pathlib import Path

import httpx
import pytest

from intake import inbox_watcher

sample_email = Path(__file__).parent / "samples" / "email_plain.eml"


@pytest.fixture
def inbox(tmp_path, monkeypatch):
    inbox_path = tmp_path / "inbox"
    monkeypatch.setattr(inbox_watcher, "inbox_folder", str(inbox_path))
    monkeypatch.setattr(inbox_watcher, "done_folder", str(inbox_path / "done"))
    monkeypatch.setattr(inbox_watcher, "failed_folder", str(inbox_path / "failed"))
    monkeypatch.setattr(inbox_watcher, "emails_per_check", 3)
    inbox_watcher.make_folders()
    return inbox_path


def add_emails(inbox_path, count):
    for number in range(count):
        target = inbox_path / f"email_{number}.eml"
        shutil.copy(sample_email, target)
        os.utime(target, (1000 + number, 1000 + number))


def fake_submit_ok(email_text):
    return {"id": 1, "status": "waiting_for_approval", "draft_order_id": 5}


def fake_submit_api_down(email_text):
    raise httpx.ConnectError("down")


def fake_submit_error(email_text):
    raise ValueError("bad email")


def names_in(folder):
    return sorted(os.listdir(folder))


def test_good_email_moves_to_done(inbox, monkeypatch):
    monkeypatch.setattr(inbox_watcher, "submit_email_text", fake_submit_ok)
    add_emails(inbox, 1)
    inbox_watcher.check_inbox_once()
    assert len(names_in(inbox / "done")) == 1
    assert "email_0.eml" not in names_in(inbox)


def test_api_down_leaves_email_in_inbox(inbox, monkeypatch):
    monkeypatch.setattr(inbox_watcher, "submit_email_text", fake_submit_api_down)
    add_emails(inbox, 1)
    inbox_watcher.check_inbox_once()
    assert "email_0.eml" in names_in(inbox)
    assert names_in(inbox / "failed") == []


def test_other_error_moves_email_to_failed(inbox, monkeypatch):
    monkeypatch.setattr(inbox_watcher, "submit_email_text", fake_submit_error)
    add_emails(inbox, 1)
    inbox_watcher.check_inbox_once()
    assert len(names_in(inbox / "failed")) == 1
    assert "email_0.eml" not in names_in(inbox)


def test_only_three_emails_per_check_oldest_first(inbox, monkeypatch):
    monkeypatch.setattr(inbox_watcher, "submit_email_text", fake_submit_ok)
    add_emails(inbox, 5)
    inbox_watcher.check_inbox_once()
    assert len(names_in(inbox / "done")) == 3
    waiting = [name for name in names_in(inbox) if name.endswith(".eml")]
    assert waiting == ["email_3.eml", "email_4.eml"]


def test_stops_after_three_failures_in_a_row(inbox, monkeypatch):
    monkeypatch.setattr(inbox_watcher, "submit_email_text", fake_submit_error)
    monkeypatch.setattr(inbox_watcher, "emails_per_check", 5)
    add_emails(inbox, 5)
    inbox_watcher.check_inbox_once()
    assert len(names_in(inbox / "failed")) == 3
    waiting = [name for name in names_in(inbox) if name.endswith(".eml")]
    assert len(waiting) == 2


def test_files_that_are_not_eml_are_ignored(inbox, monkeypatch):
    monkeypatch.setattr(inbox_watcher, "submit_email_text", fake_submit_ok)
    (inbox / "notes.txt").write_text("hello")
    inbox_watcher.check_inbox_once()
    assert "notes.txt" in names_in(inbox)
    assert names_in(inbox / "done") == []