from jobs.daily_summary import DailySummaryError
from jobs.follow_up_check import FollowUpCheckError
from jobs.stock_check import StockCheckError
from mailer.smtp_sender import MailError
from scheduler import tasks


def test_stock_task_runs_the_job_and_reports_counts(monkeypatch):
    fake_outcome = {"created": [{"id": 1}, {"id": 2}], "failed": [{"supplier_id": 3}]}
    monkeypatch.setattr(tasks, "run_stock_check", lambda: fake_outcome)

    result = tasks.stock_check.apply()

    assert result.get() == {"created": 2, "failed": 1}


def test_follow_up_task_runs_the_job_and_reports_counts(monkeypatch):
    fake_outcome = {"created": [{"id": 1}], "failed": []}
    monkeypatch.setattr(tasks, "run_follow_up_check", lambda: fake_outcome)

    result = tasks.follow_up_check.apply()

    assert result.get() == {"created": 1, "failed": 0}


def test_summary_task_reports_where_it_was_sent(monkeypatch):
    fake_outcome = {"subject": "Daily summary, 24 Nov 2026", "body": "text", "sent_to": "owner@example.com"}
    monkeypatch.setattr(tasks, "make_and_send_daily_summary", lambda: fake_outcome)

    result = tasks.daily_summary.apply()

    assert result.get() == {"subject": "Daily summary, 24 Nov 2026", "sent_to": "owner@example.com"}


def test_each_task_tries_again_later_when_the_erp_or_mail_is_down():
    assert StockCheckError in tasks.stock_check.autoretry_for
    assert FollowUpCheckError in tasks.follow_up_check.autoretry_for
    assert DailySummaryError in tasks.daily_summary.autoretry_for
    assert MailError in tasks.daily_summary.autoretry_for


def test_tasks_stop_trying_after_three_retries():
    assert tasks.stock_check.retry_kwargs["max_retries"] == 3
    assert tasks.follow_up_check.retry_kwargs["max_retries"] == 3
    assert tasks.daily_summary.retry_kwargs["max_retries"] == 3