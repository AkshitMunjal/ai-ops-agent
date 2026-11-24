from rag.settings import EMBEDDING_SIZE
from rag.vector_db import VectorDbError, connect

CREATE_CHUNKS_TABLE = f"""
CREATE TABLE IF NOT EXISTS document_chunks (
    id SERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector({EMBEDDING_SIZE}) NOT NULL,
    UNIQUE (source, chunk_index)
)
"""

CREATE_VECTOR_INDEX = """
CREATE INDEX IF NOT EXISTS document_chunks_embedding_index
ON document_chunks USING hnsw (embedding vector_cosine_ops)
"""


def create_tables():
    connection = connect()
    connection.execute(CREATE_CHUNKS_TABLE)
    connection.execute(CREATE_VECTOR_INDEX)
    connection.commit()

    row = connection.execute("SELECT COUNT(*) FROM document_chunks").fetchone()
    connection.close()
    return row[0]


if __name__ == "__main__":
    try:
        chunk_count = create_tables()
    except VectorDbError as error:
        print(error)
    else:
        print(f"Vector table is ready. Chunks stored: {chunk_count}")
