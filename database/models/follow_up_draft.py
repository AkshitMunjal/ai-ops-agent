from datetime import date

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from database.base import Base


class FollowUpDraft(Base):
    __tablename__ = "follow_up_drafts"

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"))
    to_email: Mapped[str] = mapped_column()
    subject: Mapped[str] = mapped_column()
    body: Mapped[str] = mapped_column()
    status: Mapped[str] = mapped_column(default="draft")
    created_on: Mapped[date] = mapped_column(default=date.today)