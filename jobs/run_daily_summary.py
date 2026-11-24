from jobs.daily_summary import DailySummaryError, make_and_send_daily_summary
from mailer.smtp_sender import MailError


def main():
    try:
        outcome = make_and_send_daily_summary()
    except (DailySummaryError, MailError) as error:
        print("The daily summary was not sent:", error)
        return

    print(outcome["body"])
    print()

    if outcome["sent_to"] is None:
        print("SUMMARY_RECIPIENT is not set in .env, so nothing was emailed.")
    else:
        print("Emailed to", outcome["sent_to"])


if __name__ == "__main__":
    main()