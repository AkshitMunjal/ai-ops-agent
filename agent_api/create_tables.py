from agent_api import models  # noqa: F401  (importing it registers the Run table)
from cost_control import models as cost_models  # noqa: F401  (registers the llm_usage table)
from agent_api.database import Base, database_engine


def create_agent_tables():
    Base.metadata.create_all(database_engine)
    print("Tables in the agent database:", list(Base.metadata.tables))


if __name__ == "__main__":
    create_agent_tables()