from jobs.daily_summary import DailySummaryError
from jobs.daily_summary import make_and_send_daily_summary
from jobs.follow_up_check import FollowUpCheckError
from jobs.follow_up_check import run_follow_up_check
from jobs.stock_check import StockCheckError
from jobs.stock_check import run_stock_check
from mailer.smtp_sender import MailError
from scheduler.celery_app import celery_app

retry_wait_seconds = 300
retry_times = 3


@celery_app.task(
    name="scheduler.tasks.stock_check",
    autoretry_for=(StockCheckError,),
    retry_backoff=retry_wait_seconds,
    retry_kwargs={"max_retries": retry_times},
)
def stock_check():
    outcome = run_stock_check()
    return {"created": len(outcome["created"]), "failed": len(outcome["failed"])}


@celery_app.task(
    name="scheduler.tasks.follow_up_check",
    autoretry_for=(FollowUpCheckError,),
    retry_backoff=retry_wait_seconds,
    retry_kwargs={"max_retries": retry_times},
)
def follow_up_check():
    outcome = run_follow_up_check()
    return {"created": len(outcome["created"]), "failed": len(outcome["failed"])}


@celery_app.task(
    name="scheduler.tasks.daily_summary",
    autoretry_for=(DailySummaryError, MailError),
    retry_backoff=retry_wait_seconds,
    retry_kwargs={"max_retries": retry_times},
)
def daily_summary():
    outcome = make_and_send_daily_summary()
    return {"subject": outcome["subject"], "sent_to": outcome["sent_to"]}