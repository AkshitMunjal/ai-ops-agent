from datetime import date

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from database.base import Base


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    amount_in_rupees: Mapped[float] = mapped_column()
    due_date: Mapped[date] = mapped_column()
    status: Mapped[str] = mapped_column(default="unpaid")