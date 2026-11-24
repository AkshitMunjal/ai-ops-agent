from pathlib import Path

from pgvector import Vector

from rag.chunker import split_into_chunks
from rag.embedder import EmbeddingError, embed_texts
from rag.vector_db import VectorDbError, connect

KNOWLEDGE_FOLDER = Path("knowledge")
FILE_ENDINGS = (".md", ".txt")


def find_documents(folder):
    folder_path = Path(folder)
    files = []

    for file_path in sorted(folder_path.iterdir()):
        if file_path.suffix.lower() in FILE_ENDINGS:
            files.append(file_path)

    return files


def replace_chunks(connection, source, chunks, vectors):
    connection.execute("DELETE FROM document_chunks WHERE source = %s", (source,))

    for index, chunk in enumerate(chunks):
        connection.execute(
            "INSERT INTO document_chunks (source, chunk_index, content, embedding) "
            "VALUES (%s, %s, %s, %s)",
            (source, index, chunk, Vector(vectors[index])),
        )


def remove_deleted_documents(connection, current_sources):
    rows = connection.execute("SELECT DISTINCT source FROM document_chunks").fetchall()

    for row in rows:
        source = row[0]

        if source not in current_sources:
            connection.execute("DELETE FROM document_chunks WHERE source = %s", (source,))


def ingest_folder(folder=KNOWLEDGE_FOLDER):
    """Read every document in the folder and store its chunks. Safe to run again."""
    prepared = []

    # Embed everything first, so a failure leaves the database untouched.
    for file_path in find_documents(folder):
        text = file_path.read_text(encoding="utf-8")
        chunks = split_into_chunks(text)
        vectors = embed_texts(chunks)
        prepared.append((file_path.name, chunks, vectors))

    connection = connect()
    try:
        for source, chunks, vectors in prepared:
            replace_chunks(connection, source, chunks, vectors)

        current_sources = [source for source, _, _ in prepared]
        remove_deleted_documents(connection, current_sources)
        connection.commit()
    finally:
        connection.close()

    chunk_total = sum(len(chunks) for _, chunks, _ in prepared)
    return {"documents": len(prepared), "chunks": chunk_total}


if __name__ == "__main__":
    try:
        summary = ingest_folder()
    except (VectorDbError, EmbeddingError) as error:
        print(error)
    else:
        print(f"Stored {summary['chunks']} chunks from {summary['documents']} documents.")
