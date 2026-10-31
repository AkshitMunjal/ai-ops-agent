from agent_api import models  # noqa: F401  (importing it registers the Run table)
from agent_api.database import Base, database_engine


def create_agent_tables():
    Base.metadata.create_all(database_engine)
    print("Tables in the agent database:", list(Base.metadata.tables))


if __name__ == "__main__":
    create_agent_tables()