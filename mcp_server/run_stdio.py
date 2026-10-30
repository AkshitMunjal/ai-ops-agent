import os

from dotenv import load_dotenv

from mcp_server.server import build_server

load_dotenv()

agent_api_key = os.environ.get("AGENT_API_KEY", "")

server = build_server(agent_api_key)
server.run("stdio")