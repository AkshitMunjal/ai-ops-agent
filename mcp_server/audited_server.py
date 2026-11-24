from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from database.audit import write_audit_log


class AuditedServer(MCPServer):
    def __init__(self, name, agent_name, role):
        super().__init__(name)
        self.audit_agent_name = agent_name
        self.audit_role = role
        self.visible_tool_names = []

    def add_visible_tool(self, tool_function):
        self.visible_tool_names.append(tool_function.__name__)
        self.tool()(tool_function)

    async def call_tool(self, name, arguments, context=None):
        if name not in self.visible_tool_names:
            write_audit_log(self.audit_agent_name, name, arguments, "refused")
            raise ToolError(f"The role '{self.audit_role}' is not allowed to use {name}.")

        return await super().call_tool(name, arguments, context)