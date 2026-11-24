from jobs.follow_up_check import run_follow_up_check


def main():
    outcome = run_follow_up_check()

    print("Draft follow-ups created:", len(outcome["created"]))
    for created_follow_up in outcome["created"]:
        print("  draft follow-up id", created_follow_up["id"], "written by", created_follow_up["written_by"])

    print("Invoices that failed:", len(outcome["failed"]))
    for failure in outcome["failed"]:
        print("  invoice", failure["invoice_id"], "-", failure["reason"])


if __name__ == "__main__":
    main()