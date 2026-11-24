from datetime import date

from sqlalchemy import select

from database.models import Invoice
from database.models import Order
from database.session import open_session

invoices_to_add = [
    {"amount_in_rupees": 18500.0, "due_date": date(2026, 11, 2)},
    {"amount_in_rupees": 6250.5, "due_date": date(2026, 11, 10)},
]


def add_overdue_invoices():
    with open_session() as database_session:
        select_unpaid = select(Invoice).where(Invoice.status == "unpaid")
        existing_unpaid = database_session.scalars(select_unpaid).first()

        if existing_unpaid is not None:
            print("An unpaid invoice already exists. Nothing was added.")
            return

        orders = database_session.scalars(select(Order).order_by(Order.id)).all()

        if len(orders) == 0:
            print("There are no orders, so no invoice can be added.")
            return

        for position, invoice_details in enumerate(invoices_to_add):
            order = orders[position % len(orders)]

            invoice = Invoice(
                order_id=order.id,
                amount_in_rupees=invoice_details["amount_in_rupees"],
                due_date=invoice_details["due_date"],
                status="unpaid",
            )
            database_session.add(invoice)

        database_session.commit()

    print("Added 2 unpaid invoices with past due dates.")


if __name__ == "__main__":
    add_overdue_invoices()