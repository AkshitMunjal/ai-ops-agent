import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session

default_database_address = "sqlite:///agent.db"
database_address = os.environ.get("AGENT_DATABASE_URL", default_database_address)
database_engine = create_engine(database_address)


class Base(DeclarativeBase):
    pass


def open_session():
    return Session(database_engine)