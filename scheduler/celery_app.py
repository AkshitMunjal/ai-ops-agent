import os

from celery import Celery
from dotenv import load_dotenv

from scheduler.schedule import build_schedule

load_dotenv()

redis_url = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")
schedule_mode = os.environ.get("SCHEDULE_MODE", "daily")
schedule_timezone = os.environ.get("SCHEDULE_TIMEZONE", "Asia/Kolkata")

celery_app = Celery(
    "ai_ops_agent",
    broker=redis_url,
    backend=redis_url,
    include=["scheduler.tasks"],
)

celery_app.conf.timezone = schedule_timezone
celery_app.conf.beat_schedule = build_schedule(schedule_mode)
celery_app.conf.broker_connection_retry_on_startup = True