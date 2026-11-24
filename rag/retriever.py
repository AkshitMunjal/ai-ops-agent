import os

from pgvector import Vector

from rag.embedder import embed_texts
from rag.vector_db import connect

# Cosine distance is 0 for the same meaning. 1 minus the distance is the similarity.
SEARCH_SQL = (
    "SELECT source, chunk_index, content, 1 - (embedding <=> %s) AS similarity "
    "FROM document_chunks "
    "ORDER BY embedding <=> %s "
    "LIMIT %s"
)


def get_min_similarity():
    return float(os.environ.get("RAG_MIN_SIMILARITY", "0.35"))


def search_documents(question, limit=4):
    """Return the closest chunks with their similarity, close or not."""
    question_vector = Vector(embed_texts([question])[0])

    connection = connect()
    try:
        rows = connection.execute(
            SEARCH_SQL, (question_vector, question_vector, limit)
        ).fetchall()
    finally:
        connection.close()

    matches = []
    for source, chunk_index, content, similarity in rows:
        matches.append(
            {
                "source": source,
                "chunk_index": chunk_index,
                "content": content,
                "similarity": float(similarity),
            }
        )

    return matches


def find_relevant_documents(question, limit=4):
    """Return only chunks that are close enough. An empty list means: we don't know."""
    min_similarity = get_min_similarity()
    matches = search_documents(question, limit)

    return [match for match in matches if match["similarity"] >= min_similarity]
