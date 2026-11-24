import anyio
from mcp import Client

from jobs.draft_reader import find_ordered_product_ids
from jobs.mcp_helpers import read_list
from jobs.stock_planner import make_reorder_plans
from mcp_server.server import build_server

stock_agent_key = "demo-key-stock"


class StockCheckError(Exception):
    pass


async def check_stock_and_draft_reorders():
    server = build_server(stock_agent_key)

    created = []
    failed = []
    read_problem = None

    async with Client(server) as mcp_client:
        low_stock_products, read_problem = await read_list(mcp_client, "list_low_stock_products")

        if read_problem is None:
            open_reorders, read_problem = await read_list(mcp_client, "list_open_reorders")

        if read_problem is None:
            ordered_product_ids = find_ordered_product_ids(open_reorders)
            plans = make_reorder_plans(low_stock_products, ordered_product_ids)

            for plan in plans:
                result = await mcp_client.call_tool("create_draft_reorder", plan)

                if result.is_error:
                    failure = {"supplier_id": plan["supplier_id"], "reason": result.content[0].text}
                    failed.append(failure)
                    continue

                created.append(result.structured_content)

    if read_problem is not None:
        raise StockCheckError(read_problem)

    return {"created": created, "failed": failed}


def run_stock_check():
    return anyio.run(check_stock_and_draft_reorders)