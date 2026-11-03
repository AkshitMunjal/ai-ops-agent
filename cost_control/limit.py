import os
from datetime import datetime

from sqlalchemy import func, select

from agent_api.database import open_session
from cost_control.models import LlmUsage


class SpendLimitReached(Exception):
    pass


def get_daily_limit():
    limit_text = os.environ.get("DAILY_SPEND_LIMIT_USD", "1.00")
    return float(limit_text)


def spent_today():
    now = datetime.now()
    start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    total_cost = func.coalesce(func.sum(LlmUsage.cost), 0.0)
    statement = select(total_cost).where(LlmUsage.created_at >= start_of_today)

    with open_session() as database_session:
        spent = database_session.scalar(statement)

    return spent


def check_spend_limit():
    daily_limit = get_daily_limit()
    spent = spent_today()

    if spent >= daily_limit:
        raise SpendLimitReached(f"Daily spend limit of ${daily_limit:g} reached (spent ${spent:.4f} today)")