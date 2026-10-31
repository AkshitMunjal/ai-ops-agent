from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class NewRun(BaseModel):
    email_text: str = Field(min_length=1)


class Decision(BaseModel):
    decision: Literal["approve", "reject"]


class RunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email_text: str
    status: str
    problems: str
    draft_order_id: int | None
    created_at: datetime


class RunDetail(RunOut):
    understood: dict | None = None