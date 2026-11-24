import sys

from scheduler.tasks import daily_summary
from scheduler.tasks import follow_up_check
from scheduler.tasks import stock_check

tasks_by_name = {
    "stock-check": stock_check,
    "follow-up-check": follow_up_check,
    "daily-summary": daily_summary,
}


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in tasks_by_name:
        print("Use one of:", ", ".join(tasks_by_name))
        return

    task_name = sys.argv[1]
    result = tasks_by_name[task_name].delay()
    print("Sent to the worker:", task_name, "(task id", result.id + ")")
    print("Look at the worker window to see it run.")


if __name__ == "__main__":
    main()