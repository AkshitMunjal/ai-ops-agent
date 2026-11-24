from jobs.stock_check import run_stock_check


def main():
    outcome = run_stock_check()

    print("Draft reorders created:", len(outcome["created"]))
    for created_reorder in outcome["created"]:
        print("  draft reorder id", created_reorder["id"])

    print("Suppliers that failed:", len(outcome["failed"]))
    for failure in outcome["failed"]:
        print("  supplier", failure["supplier_id"], "-", failure["reason"])


if __name__ == "__main__":
    main()