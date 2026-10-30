import functools

from mcp.server.mcpserver.exceptions import ToolError

from database.audit import write_audit_log
from mcp_server.roles import is_tool_allowed


def wrap_tool_with_audit(tool_function, agent_name, role):
    tool_name = tool_function.__name__

    @functools.wraps(tool_function)
    def wrapped_tool(**tool_input):
        if not is_tool_allowed(role, tool_name):
            write_audit_log(agent_name, tool_name, tool_input, "refused")
            raise ToolError(f"The role '{role}' is not allowed to use {tool_name}.")

        try:
            result = tool_function(**tool_input)
        except Exception:
            write_audit_log(agent_name, tool_name, tool_input, "error")
            raise

        write_audit_log(agent_name, tool_name, tool_input, "allowed")
        return result

    return wrapped_tool