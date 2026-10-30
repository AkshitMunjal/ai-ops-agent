from datetime import datetime

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from database.base import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    who: Mapped[str] = mapped_column()
    tool_name: Mapped[str] = mapped_column()
    tool_input: Mapped[str] = mapped_column()
    outcome: Mapped[str] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)