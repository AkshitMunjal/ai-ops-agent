from fastapi import FastAPI

from agent_api.create_tables import create_agent_tables
from agent_api.routes import chat, review, runs

create_agent_tables()

app = FastAPI(title="Agent API")
app.include_router(runs.router)
app.include_router(review.router)
app.include_router(chat.router)