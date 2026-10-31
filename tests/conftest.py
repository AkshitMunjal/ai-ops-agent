import os

os.environ["DATABASE_URL"] = "sqlite:///test_erp.db"
os.environ["AGENT_DATABASE_URL"] = "sqlite:///test_agent.db"
os.environ["CHECKPOINT_DB"] = "test_agent_checkpoints.db"

import pytest
from fastapi.testclient import TestClient

from api.main import app
from database.base import Base
from database.connection import database_engine
from database.create_tables import create_all_tables
from database.seed_data import seed_sample_data


@pytest.fixture
def client():
    Base.metadata.drop_all(database_engine)
    create_all_tables()
    seed_sample_data()

    test_client = TestClient(app)
    return test_client