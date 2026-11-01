import sys
import time

import httpx

from intake.email_reader import read_email_bytes
from intake.gmail_inbox import fetch_unread_emails, mark_as_failed, mark_as_read
from intake.submit import submit_email_text

emails_per_check = 3
seconds_between_checks = 10
max_failures_in_a_row = 3


def try_mark_as_read(uid):
    try:
        mark_as_read(uid)
    except Exception as error:
        print(f"email {uid}: handled, but could not mark it as read ({error})")


def try_mark_as_failed(uid):
    try:
        mark_as_failed(uid)
    except Exception as error:
        print(f"email {uid}: could not label it orders-failed ({error})")


def process_one_email(one_email):
    uid = one_email["uid"]

    try:
        email_text = read_email_bytes(one_email["raw_email"])
        run = submit_email_text(email_text, one_email["message_id"])
    except httpx.ConnectError:
        print(f"email {uid}: the agent API is not reachable, left unread")
        return False
    except Exception as error:
        print(f"email {uid}: failed ({error}), labelled orders-failed")
        try_mark_as_failed(uid)
        return False

    if run["already_seen"]:
        print(f"email {uid}: already handled as run {run['id']}, marked as read")
    else:
        print(f"email {uid}: run {run['id']} is {run['status']}, draft order {run['draft_order_id']}")

    try_mark_as_read(uid)
    return True


def check_gmail_once():
    try:
        waiting_emails = fetch_unread_emails(emails_per_check)
    except Exception as error:
        print(f"Could not read Gmail: {error}")
        return 0

    failures_in_a_row = 0

    for one_email in waiting_emails:
        worked = process_one_email(one_email)

        if worked:
            failures_in_a_row = 0
        else:
            failures_in_a_row = failures_in_a_row + 1

        if failures_in_a_row >= max_failures_in_a_row:
            print("Too many failures in a row, stopping this check.")
            break

    return len(waiting_emails)


def watch_gmail():
    print(f"Watching Gmail, {emails_per_check} emails every {seconds_between_checks} seconds. Ctrl+C to stop.")
    while True:
        check_gmail_once()
        time.sleep(seconds_between_checks)


if __name__ == "__main__":
    if "--watch" in sys.argv:
        try:
            watch_gmail()
        except KeyboardInterrupt:
            print("Stopped.")
    else:
        count = check_gmail_once()
        print(f"Checked {count} email(s).")