from datetime import date

from fastapi import APIRouter
from fastapi import HTTPException
from sqlalchemy import select

from database.models import Customer
from database.models import Invoice
from database.models import Order
from database.session import open_session

router = APIRouter()


def invoice_to_dictionary(database_session, invoice):
    order = database_session.get(Order, invoice.order_id)
    customer = database_session.get(Customer, order.customer_id)

    return {
        "id": invoice.id,
        "order_id": invoice.order_id,
        "customer_name": customer.name,
        "customer_email": customer.email,
        "amount_in_rupees": invoice.amount_in_rupees,
        "due_date": invoice.due_date,
        "status": invoice.status,
    }


@router.get("/invoices")
def list_invoices():
    select_all_invoices = select(Invoice)
    invoices_as_dictionaries = []

    with open_session() as database_session:
        invoice_rows = database_session.scalars(select_all_invoices)

        for invoice in invoice_rows:
            invoice_dictionary = invoice_to_dictionary(database_session, invoice)
            invoices_as_dictionaries.append(invoice_dictionary)

    return invoices_as_dictionaries


@router.get("/invoices/overdue")
def list_overdue_invoices():
    today = date.today()

    select_overdue = select(Invoice)
    select_overdue = select_overdue.where(Invoice.status == "unpaid")
    select_overdue = select_overdue.where(Invoice.due_date < today)

    overdue_as_dictionaries = []

    with open_session() as database_session:
        invoice_rows = database_session.scalars(select_overdue)

        for invoice in invoice_rows:
            invoice_dictionary = invoice_to_dictionary(database_session, invoice)
            overdue_as_dictionaries.append(invoice_dictionary)

    return overdue_as_dictionaries


@router.get("/invoices/{invoice_id}")
def get_one_invoice(invoice_id: int):
    with open_session() as database_session:
        invoice = database_session.get(Invoice, invoice_id)

        if invoice is None:
            raise HTTPException(status_code=404, detail="Invoice not found")

        invoice_dictionary = invoice_to_dictionary(database_session, invoice)

    return invoice_dictionary


@router.post("/invoices/{invoice_id}/mark-paid")
def mark_invoice_paid(invoice_id: int):
    with open_session() as database_session:
        invoice = database_session.get(Invoice, invoice_id)

        if invoice is None:
            raise HTTPException(status_code=404, detail="Invoice not found")

        if invoice.status != "unpaid":
            raise HTTPException(status_code=409, detail="Only unpaid invoices can be marked as paid")

        invoice.status = "paid"
        database_session.commit()

        paid_invoice_id = invoice.id
        paid_invoice_status = invoice.status

    return {"id": paid_invoice_id, "status": paid_invoice_status}