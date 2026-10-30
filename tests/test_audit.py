from sqlalchemy import select

from database.audit import write_audit_log
from database.models import AuditLog
from database.session import open_session


def test_write_audit_log_saves_one_row(client):
    write_audit_log("order_agent", "create_draft_order", {"customer_id": 1}, "allowed")

    select_all_rows = select(AuditLog)

    with open_session() as database_session:
        audit_rows = database_session.scalars(select_all_rows)
        audit_list = list(audit_rows)

    assert len(audit_list) == 1

    first_row = audit_list[0]

    assert first_row.who == "order_agent"
    assert first_row.tool_name == "create_draft_order"
    assert first_row.tool_input == '{"customer_id": 1}'
    assert first_row.outcome == "allowed"
    assert first_row.created_at is not None