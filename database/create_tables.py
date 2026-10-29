from sqlalchemy import inspect

import database.models
from database.base import Base
from database.connection import database_engine


def create_all_tables():
    Base.metadata.create_all(database_engine)

    table_inspector = inspect(database_engine)
    table_names = table_inspector.get_table_names()
    print("Tables in the database:", table_names)


if __name__ == "__main__":
    create_all_tables()