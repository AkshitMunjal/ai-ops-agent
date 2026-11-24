from fastapi import APIRouter
from fastapi import HTTPException
from sqlalchemy import select

from api.schemas import NewFollowUp
from database.models import Customer
from database.models import FollowUpDraft
from database.models import Invoice
from database.models import Order
from database.session import open_session
from mailer.smtp_sender import MailError
from mailer.smtp_sender import send_email

router = APIRouter()


def describe_follow_up(follow_up):
    return {
        "id": follow_up.id,
        "invoice_id": follow_up.invoice_id,
        "to_email": follow_up.to_email,
        "subject": follow_up.subject,
        "body": follow_up.body,
        "status": follow_up.status,
        "created_on": follow_up.created_on,
    }


@router.post("/follow-ups", status_code=201)
def create_draft_follow_up(new_follow_up: NewFollowUp):
    with open_session() as database_session:
        invoice = database_session.get(Invoice, new_follow_up.invoice_id)

        if invoice is None:
            raise HTTPException(status_code=404, detail="Invoice not found")

        if invoice.status != "unpaid":
            raise HTTPException(status_code=409, detail="Only unpaid invoices can be followed up")

        select_open_draft = select(FollowUpDraft)
        select_open_draft = select_open_draft.where(FollowUpDraft.invoice_id == invoice.id)
        select_open_draft = select_open_draft.where(FollowUpDraft.status == "draft")
        open_draft = database_session.scalars(select_open_draft).first()

        if open_draft is not None:
            raise HTTPException(status_code=409, detail="This invoice already has a draft follow-up")

        order = database_session.get(Order, invoice.order_id)
        customer = database_session.get(Customer, order.customer_id)

        follow_up_to_save = FollowUpDraft(
            invoice_id=invoice.id,
            to_email=customer.email,
            subject=new_follow_up.subject,
            body=new_follow_up.body,
        )
        database_session.add(follow_up_to_save)
        database_session.commit()

        saved_id = follow_up_to_save.id
        saved_status = follow_up_to_save.status

    return {"id": saved_id, "status": saved_status}


@router.get("/follow-ups")
def list_follow_ups(status: str | None = None):
    select_follow_ups = select(FollowUpDraft).order_by(FollowUpDraft.id)

    if status is not None:
        select_follow_ups = select_follow_ups.where(FollowUpDraft.status == status)

    with open_session() as database_session:
        found_follow_ups = database_session.scalars(select_follow_ups).all()

        follow_ups_as_dictionaries = []
        for follow_up in found_follow_ups:
            follow_up_dictionary = describe_follow_up(follow_up)
            follow_ups_as_dictionaries.append(follow_up_dictionary)

    return follow_ups_as_dictionaries


@router.post("/follow-ups/{follow_up_id}/cancel")
def cancel_follow_up(follow_up_id: int):
    with open_session() as database_session:
        follow_up = database_session.get(FollowUpDraft, follow_up_id)

        if follow_up is None:
            raise HTTPException(status_code=404, detail="Follow-up not found")

        if follow_up.status != "draft":
            raise HTTPException(status_code=409, detail="Only draft follow-ups can be cancelled")

        follow_up.status = "cancelled"
        database_session.commit()

        changed_id = follow_up.id
        changed_status = follow_up.status

    return {"id": changed_id, "status": changed_status}


@router.post("/follow-ups/{follow_up_id}/send")
def send_follow_up(follow_up_id: int):
    with open_session() as database_session:
        follow_up = database_session.get(FollowUpDraft, follow_up_id)

        if follow_up is None:
            raise HTTPException(status_code=404, detail="Follow-up not found")

        if follow_up.status != "draft":
            raise HTTPException(status_code=409, detail="Only draft follow-ups can be sent")

        invoice = database_session.get(Invoice, follow_up.invoice_id)

        if invoice.status != "unpaid":
            raise HTTPException(status_code=409, detail="The invoice is no longer unpaid. Cancel this draft")

        try:
            send_email(follow_up.to_email, follow_up.subject, follow_up.body)
        except MailError as error:
            raise HTTPException(status_code=502, detail=str(error))

        follow_up.status = "sent"
        database_session.commit()

        changed_id = follow_up.id
        changed_status = follow_up.status

    return {"id": changed_id, "status": changed_status}