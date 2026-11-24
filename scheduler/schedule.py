from celery.schedules import crontab

stock_check_task = "scheduler.tasks.stock_check"
follow_up_check_task = "scheduler.tasks.follow_up_check"
daily_summary_task = "scheduler.tasks.daily_summary"


def build_schedule(mode):
    if mode == "test":
        every_two_minutes = crontab(minute="*/2")

        return {
            "stock-check": {"task": stock_check_task, "schedule": every_two_minutes},
            "follow-up-check": {"task": follow_up_check_task, "schedule": every_two_minutes},
            "daily-summary": {"task": daily_summary_task, "schedule": every_two_minutes},
        }

    return {
        "stock-check": {"task": stock_check_task, "schedule": crontab(hour=8, minute=0)},
        "follow-up-check": {"task": follow_up_check_task, "schedule": crontab(hour=8, minute=10)},
        "daily-summary": {"task": daily_summary_task, "schedule": crontab(hour=8, minute=30)},
    }