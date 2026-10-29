from sqlalchemy.orm import Session

from database.connection import database_engine


def open_session():
    return Session(database_engine)