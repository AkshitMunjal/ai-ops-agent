from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column

from agent_api.database import Base


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    email_text: Mapped[str]
    message_id: Mapped[str | None] = mapped_column(default=None, index=True)
    status: Mapped[str] = mapped_column(default="received")
    problems: Mapped[str] = mapped_column(default="")
    draft_order_id: Mapped[int | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)