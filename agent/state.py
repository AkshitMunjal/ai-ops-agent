from typing import TypedDict


class AgentState(TypedDict, total=False):
    email_text: str
    extracted_order: dict
    matched_order: dict
    problems: list[str]
    draft_order: dict
    decision: str
    status: str