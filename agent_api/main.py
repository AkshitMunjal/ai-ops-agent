from fastapi import FastAPI

from agent_api.create_tables import create_agent_tables
from agent_api.routes import runs

create_agent_tables()

app = FastAPI(title="Agent API")
app.include_router(runs.router)