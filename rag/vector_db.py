import psycopg
from pgvector.psycopg import register_vector

from rag.settings import get_vector_url


class VectorDbError(Exception):
    """The vector database could not be reached."""


def connect():
    url = get_vector_url()
    try:
        connection = psycopg.connect(url, connect_timeout=5)
    except psycopg.OperationalError as error:
        raise VectorDbError(
            "Cannot reach the vector database. Is Docker Desktop open "
            "and is the vectordb container running?"
        ) from error

    # The extension must exist before the vector type can be registered.
    connection.execute("CREATE EXTENSION IF NOT EXISTS vector")
    connection.commit()
    register_vector(connection)
    return connection
