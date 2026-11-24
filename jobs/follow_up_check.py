import os
from datetime import date

import anyio
from mcp import Client

from jobs.follow_up_planner import choose_invoices_to_chase
from jobs.follow_up_writer import write_follow_up_email
from jobs.mcp_helpers import read_list
from mcp_server.server import build_server

follow_up_agent_key = "demo-key-followup"


class FollowUpCheckError(Exception):
    pass


def get_days_between_reminders():
    days_text = os.environ.get("FOLLOW_UP_EVERY_DAYS", "7")
    return int(days_text)


async def check_invoices_and_draft_follow_ups():
    server = build_server(follow_up_agent_key)

    created = []
    failed = []
    read_problem = None

    async with Client(server) as mcp_client:
        overdue_invoices, read_problem = await read_list(mcp_client, "list_overdue_invoices")

        if read_problem is None:
            follow_ups, read_problem = await read_list(mcp_client, "list_follow_ups")

        if read_problem is None:
            invoices_to_chase = choose_invoices_to_chase(
                overdue_invoices,
                follow_ups,
                date.today(),
                get_days_between_reminders(),
            )

            for invoice in invoices_to_chase:
                email = write_follow_up_email(invoice)

                tool_input = {
                    "invoice_id": invoice["id"],
                    "subject": email["subject"],
                    "body": email["body"],
                }
                result = await mcp_client.call_tool("create_draft_follow_up", tool_input)

                if result.is_error:
                    failure = {"invoice_id": invoice["id"], "reason": result.content[0].text}
                    failed.append(failure)
                    continue

                created_follow_up = dict(result.structured_content)
                created_follow_up["written_by"] = email["written_by"]
                created.append(created_follow_up)

    if read_problem is not None:
        raise FollowUpCheckError(read_problem)

    return {"created": created, "failed": failed}


def run_follow_up_check():
    return anyio.run(check_invoices_and_draft_follow_ups)