import os
import shutil
import sys
import time
from datetime import datetime

import httpx

from intake.email_reader import read_email_file
from intake.submit import submit_email_text

inbox_folder = "inbox"
done_folder = os.path.join("inbox", "done")
failed_folder = os.path.join("inbox", "failed")

emails_per_check = 3
seconds_between_checks = 10
max_failures_in_a_row = 3


def make_folders():
    os.makedirs(inbox_folder, exist_ok=True)
    os.makedirs(done_folder, exist_ok=True)
    os.makedirs(failed_folder, exist_ok=True)


def find_waiting_emails(limit):
    file_names = os.listdir(inbox_folder)

    email_paths = []
    for file_name in file_names:
        if file_name.lower().endswith(".eml"):
            email_paths.append(os.path.join(inbox_folder, file_name))

    email_paths.sort(key=os.path.getmtime)
    return email_paths[:limit]


def move_email(email_path, target_folder):
    time_stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    file_name = os.path.basename(email_path)
    new_path = os.path.join(target_folder, time_stamp + "_" + file_name)
    shutil.move(email_path, new_path)


def process_one_email(email_path):
    file_name = os.path.basename(email_path)

    try:
        email_text = read_email_file(email_path)
        run = submit_email_text(email_text)
    except httpx.ConnectError:
        print(f"{file_name}: the agent API is not reachable, left in inbox")
        return False
    except Exception as error:
        print(f"{file_name}: failed ({error}), moved to failed")
        move_email(email_path, failed_folder)
        return False

    print(f"{file_name}: run {run['id']} is {run['status']}, draft order {run['draft_order_id']}")
    move_email(email_path, done_folder)
    return True


def check_inbox_once():
    email_paths = find_waiting_emails(emails_per_check)
    failures_in_a_row = 0

    for email_path in email_paths:
        worked = process_one_email(email_path)

        if worked:
            failures_in_a_row = 0
        else:
            failures_in_a_row = failures_in_a_row + 1

        if failures_in_a_row >= max_failures_in_a_row:
            print("Too many failures in a row, stopping this check.")
            break

    return len(email_paths)


def watch_inbox():
    print(f"Watching {inbox_folder}, {emails_per_check} emails every {seconds_between_checks} seconds. Ctrl+C to stop.")
    while True:
        check_inbox_once()
        time.sleep(seconds_between_checks)


if __name__ == "__main__":
    make_folders()

    if "--watch" in sys.argv:
        try:
            watch_inbox()
        except KeyboardInterrupt:
            print("Stopped.")
    else:
        count = check_inbox_once()
        print(f"Checked {count} email(s).")