import os
from datetime import date

import anyio
from mcp import Client

from jobs.mcp_helpers import read_list
from jobs.summary_builder import build_summary
from mailer.smtp_sender import send_email
from mcp_server.server import build_server

summary_agent_key = "demo-key-summary"

lists_to_read = [
    "list_low_stock_products",
    "list_draft_reorders",
    "list_overdue_invoices",
    "list_follow_ups",
]


class DailySummaryError(Exception):
    pass


async def read_everything():
    server = build_server(summary_agent_key)
    results = {}
    read_problem = None

    async with Client(server) as mcp_client:
        for tool_name in lists_to_read:
            data, read_problem = await read_list(mcp_client, tool_name)

            if read_problem is not None:
                break

            results[tool_name] = data

    return results, read_problem


def make_and_send_daily_summary():
    results, read_problem = anyio.run(read_everything)

    if read_problem is not None:
        raise DailySummaryError(read_problem)

    summary = build_summary(
        results["list_low_stock_products"],
        results["list_draft_reorders"],
        results["list_overdue_invoices"],
        results["list_follow_ups"],
        date.today(),
    )

    recipient = os.environ.get("SUMMARY_RECIPIENT", "")

    if not recipient:
        return {"subject": summary["subject"], "body": summary["body"], "sent_to": None}

    send_email(recipient, summary["subject"], summary["body"], use_test_recipient=False)
    return {"subject": summary["subject"], "body": summary["body"], "sent_to": recipient}