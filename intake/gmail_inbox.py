import email
import imaplib
import os
from email import policy

from dotenv import load_dotenv

load_dotenv()

gmail_server = "imap.gmail.com"

skipped_sender_words = ["noreply", "no-reply", "donotreply"]


class GmailError(Exception):
    pass


def connect_to_gmail():
    address = os.environ.get("GMAIL_ADDRESS", "")
    app_password = os.environ.get("GMAIL_APP_PASSWORD", "").replace(" ", "")

    if not address or not app_password:
        raise GmailError("GMAIL_ADDRESS and GMAIL_APP_PASSWORD must be set in .env")

    connection = imaplib.IMAP4_SSL(gmail_server)

    try:
        connection.login(address, app_password)
    except imaplib.IMAP4.error as error:
        raise GmailError(f"Gmail login failed: {error}")

    return connection


def get_since_date():
    since_date = os.environ.get("GMAIL_SINCE", "")

    if not since_date:
        raise GmailError("GMAIL_SINCE must be set in .env, for example GMAIL_SINCE=01-Nov-2026")

    return since_date


def open_folder(connection, readonly=True):
    folder_name = os.environ.get("GMAIL_FOLDER", "INBOX")

    status, data = connection.select(f'"{folder_name}"', readonly=readonly)

    if status != "OK":
        raise GmailError(f"Could not open the Gmail folder or label '{folder_name}'")


def build_search_words(since_date):
    search_words = ["UNSEEN", "SINCE", since_date]

    for sender_word in skipped_sender_words:
        search_words.extend(["NOT", "FROM", sender_word])

    return search_words


def find_unread_uids(connection, limit):
    search_words = build_search_words(get_since_date())

    status, data = connection.uid("search", None, *search_words)
    all_uids = data[0].split()

    return all_uids[:limit]


def list_unread_headers(limit):
    connection = connect_to_gmail()
    open_folder(connection)
    first_uids = find_unread_uids(connection, limit)

    headers = []
    for uid in first_uids:
        status, parts = connection.uid("fetch", uid, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT MESSAGE-ID)])")
        raw_header = parts[0][1]
        message = email.message_from_bytes(raw_header, policy=policy.default)
        header = {
            "uid": uid.decode(),
            "from": message["from"],
            "subject": message["subject"],
            "message_id": message["message-id"],
        }
        headers.append(header)

    connection.logout()
    return headers


def fetch_unread_emails(limit):
    connection = connect_to_gmail()
    open_folder(connection)
    first_uids = find_unread_uids(connection, limit)

    emails = []
    for uid in first_uids:
        status, parts = connection.uid("fetch", uid, "(BODY.PEEK[])")
        raw_email = parts[0][1]
        message = email.message_from_bytes(raw_email, policy=policy.default)
        one_email = {
            "uid": uid.decode(),
            "message_id": message["message-id"],
            "raw_email": raw_email,
        }
        emails.append(one_email)

    connection.logout()
    return emails


def mark_as_read(uid):
    connection = connect_to_gmail()
    open_folder(connection, readonly=False)

    status, data = connection.uid("store", uid, "+FLAGS", "(\\Seen)")

    connection.logout()

    if status != "OK":
        raise GmailError(f"Could not mark email {uid} as read")


def mark_as_failed(uid):
    connection = connect_to_gmail()
    open_folder(connection, readonly=False)

    status, data = connection.uid("store", uid, "+X-GM-LABELS", "(orders-failed)")

    if status != "OK":
        connection.logout()
        raise GmailError(f"Could not add the orders-failed label to email {uid}")

    connection.uid("store", uid, "+FLAGS", "(\\Seen)")
    connection.logout()