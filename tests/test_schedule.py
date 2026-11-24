from scheduler import tasks
from scheduler.celery_app import celery_app
from scheduler.schedule import build_schedule


def hours_and_minutes(schedule_entry):
    crontab_schedule = schedule_entry["schedule"]
    return list(crontab_schedule.hour), list(crontab_schedule.minute)


def test_daily_schedule_runs_each_job_once_a_day_in_the_right_order():
    schedule = build_schedule("daily")

    assert hours_and_minutes(schedule["stock-check"]) == ([8], [0])
    assert hours_and_minutes(schedule["follow-up-check"]) == ([8], [10])
    assert hours_and_minutes(schedule["daily-summary"]) == ([8], [30])


def test_the_summary_runs_after_the_jobs_that_create_drafts():
    schedule = build_schedule("daily")

    stock_minute = hours_and_minutes(schedule["stock-check"])[1][0]
    follow_up_minute = hours_and_minutes(schedule["follow-up-check"])[1][0]
    summary_minute = hours_and_minutes(schedule["daily-summary"])[1][0]

    assert summary_minute > follow_up_minute > stock_minute


def test_test_mode_runs_every_two_minutes():
    schedule = build_schedule("test")

    for entry in schedule.values():
        minutes = hours_and_minutes(entry)[1]
        assert minutes == list(range(0, 60, 2))


def test_every_scheduled_task_exists():
    for entry in build_schedule("daily").values():
        assert entry["task"] in celery_app.tasks


def test_the_app_uses_the_schedule_and_the_kolkata_timezone():
    assert celery_app.conf.timezone == "Asia/Kolkata"
    assert set(celery_app.conf.beat_schedule) == {"stock-check", "follow-up-check", "daily-summary"}