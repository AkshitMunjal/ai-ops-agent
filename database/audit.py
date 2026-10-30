import json

from database.models import AuditLog
from database.session import open_session


def write_audit_log(who, tool_name, tool_input, outcome):
    tool_input_as_text = json.dumps(tool_input)

    audit_row = AuditLog(
        who=who,
        tool_name=tool_name,
        tool_input=tool_input_as_text,
        outcome=outcome,
    )

    with open_session() as database_session:
        database_session.add(audit_row)
        database_session.commit()