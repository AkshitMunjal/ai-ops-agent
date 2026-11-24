from sqlalchemy import select

from api.routes import follow_ups
from database.models import Customer
from database.models import Invoice
from database.models import Order
from database.session import open_session
from mailer.smtp_sender import MailError


def find_unpaid_invoice():
    select_unpaid = select(Invoice).where(Invoice.status == "unpaid")

    with open_session() as database_session:
        invoice = database_session.scalars(select_unpaid).first()
        return invoice.id


def mark_invoice_paid_directly(invoice_id):
    with open_session() as database_session:
        invoice = database_session.get(Invoice, invoice_id)
        invoice.status = "paid"
        database_session.commit()


def customer_email_of(invoice_id):
    with open_session() as database_session:
        invoice = database_session.get(Invoice, invoice_id)
        order = database_session.get(Order, invoice.order_id)
        customer = database_session.get(Customer, order.customer_id)
        return customer.email


def post_follow_up(client, invoice_id, subject="Payment reminder", body="Please pay."):
    new_follow_up = {"invoice_id": invoice_id, "subject": subject, "body": body}
    return client.post("/follow-ups", json=new_follow_up)


def install_fake_mailer(monkeypatch):
    sent_emails = []

    def fake_send_email(to_address, subject, body):
        sent_emails.append({"to": to_address, "subject": subject, "body": body})

    monkeypatch.setattr(follow_ups, "send_email", fake_send_email)
    return sent_emails


def test_a_new_draft_is_addressed_to_the_invoice_customer(client):
    invoice_id = find_unpaid_invoice()

    response = post_follow_up(client, invoice_id)
    listed = client.get("/follow-ups").json()

    assert response.status_code == 201
    assert response.json()["status"] == "draft"
    assert listed[0]["to_email"] == customer_email_of(invoice_id)
    assert listed[0]["invoice_id"] == invoice_id


def test_unknown_invoice_is_refused(client):
    response = post_follow_up(client, 99999)

    assert response.status_code == 404


def test_paid_invoice_cannot_be_followed_up(client):
    invoice_id = find_unpaid_invoice()
    mark_invoice_paid_directly(invoice_id)

    response = post_follow_up(client, invoice_id)

    assert response.status_code == 409


def test_second_open_draft_for_the_same_invoice_is_refused(client):
    invoice_id = find_unpaid_invoice()
    post_follow_up(client, invoice_id)

    response = post_follow_up(client, invoice_id)

    assert response.status_code == 409


def test_list_can_be_filtered_by_status(client):
    invoice_id = find_unpaid_invoice()
    created = post_follow_up(client, invoice_id).json()
    client.post(f"/follow-ups/{created['id']}/cancel")

    drafts = client.get("/follow-ups", params={"status": "draft"}).json()
    cancelled = client.get("/follow-ups", params={"status": "cancelled"}).json()
    everything = client.get("/follow-ups").json()

    assert drafts == []
    assert len(cancelled) == 1
    assert len(everything) == 1


def test_cancel_works_once_and_only_for_drafts(client):
    invoice_id = find_unpaid_invoice()
    created = post_follow_up(client, invoice_id).json()

    first = client.post(f"/follow-ups/{created['id']}/cancel")
    second = client.post(f"/follow-ups/{created['id']}/cancel")

    assert first.json()["status"] == "cancelled"
    assert second.status_code == 409


def test_send_sends_the_email_and_marks_the_draft_sent(client, monkeypatch):
    sent_emails = install_fake_mailer(monkeypatch)
    invoice_id = find_unpaid_invoice()
    created = post_follow_up(client, invoice_id, "Reminder", "Dear customer").json()

    response = client.post(f"/follow-ups/{created['id']}/send")

    assert response.status_code == 200
    assert response.json()["status"] == "sent"
    assert len(sent_emails) == 1
    assert sent_emails[0]["to"] == customer_email_of(invoice_id)
    assert sent_emails[0]["subject"] == "Reminder"
    assert sent_emails[0]["body"] == "Dear customer"


def test_a_draft_cannot_be_sent_twice(client, monkeypatch):
    sent_emails = install_fake_mailer(monkeypatch)
    created = post_follow_up(client, find_unpaid_invoice()).json()
    client.post(f"/follow-ups/{created['id']}/send")

    second = client.post(f"/follow-ups/{created['id']}/send")

    assert second.status_code == 409
    assert len(sent_emails) == 1


def test_email_failure_keeps_the_draft_so_it_can_be_tried_again(client, monkeypatch):
    def broken_send_email(to_address, subject, body):
        raise MailError("The email could not be sent: network down")

    monkeypatch.setattr(follow_ups, "send_email", broken_send_email)
    created = post_follow_up(client, find_unpaid_invoice()).json()

    response = client.post(f"/follow-ups/{created['id']}/send")
    drafts = client.get("/follow-ups", params={"status": "draft"}).json()

    assert response.status_code == 502
    assert "network down" in response.json()["detail"]
    assert len(drafts) == 1


def test_nothing_is_sent_when_the_invoice_was_paid_in_the_meantime(client, monkeypatch):
    sent_emails = install_fake_mailer(monkeypatch)
    invoice_id = find_unpaid_invoice()
    created = post_follow_up(client, invoice_id).json()
    mark_invoice_paid_directly(invoice_id)

    response = client.post(f"/follow-ups/{created['id']}/send")

    assert response.status_code == 409
    assert sent_emails == []