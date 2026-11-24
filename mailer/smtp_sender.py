import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv

load_dotenv()

gmail_smtp_server = "smtp.gmail.com"
gmail_smtp_port = 465


class MailError(Exception):
    pass


def send_email(to_address, subject, body, use_test_recipient=True):
    from_address = os.environ.get("GMAIL_ADDRESS", "")
    app_password = os.environ.get("GMAIL_APP_PASSWORD", "").replace(" ", "")

    if not from_address or not app_password:
        raise MailError("GMAIL_ADDRESS and GMAIL_APP_PASSWORD must be set in .env")

    test_recipient = os.environ.get("FOLLOW_UP_TEST_RECIPIENT", "")

    if test_recipient and use_test_recipient:
        subject = f"[TEST, meant for {to_address}] {subject}"
        to_address = test_recipient

    message = EmailMessage()
    message["From"] = from_address
    message["To"] = to_address
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP_SSL(gmail_smtp_server, gmail_smtp_port, timeout=30) as connection:
            connection.login(from_address, app_password)
            connection.send_message(message)
    except (smtplib.SMTPException, OSError) as error:
        raise MailError(f"The email could not be sent: {error}")