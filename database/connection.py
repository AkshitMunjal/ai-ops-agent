import os

from sqlalchemy import create_engine

default_database_address = "sqlite:///erp.db"
database_address = os.environ.get("DATABASE_URL", default_database_address)
database_engine = create_engine(database_address)