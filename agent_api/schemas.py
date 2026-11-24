from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class NewRun(BaseModel):
    email_text: str = Field(min_length=1)
    message_id: str | None = None


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


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatQuestion(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    question: str = Field(min_length=1, max_length=1000)
    history: list[ChatMessage] = Field(default_factory=list, max_length=20)


class ChatAnswer(BaseModel):
    answer: str
    known: bool
    tools_used: list[str]
    sources: list[str]
