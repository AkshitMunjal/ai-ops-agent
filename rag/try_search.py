import sys

from cost_control.limit import SpendLimitReached
from rag.embedder import EmbeddingError
from rag.retriever import get_min_similarity, search_documents
from rag.vector_db import VectorDbError


def main():
    if len(sys.argv) < 2:
        print('Usage: python -m rag.try_search "your question"')
        return

    question = " ".join(sys.argv[1:])
    min_similarity = get_min_similarity()

    try:
        matches = search_documents(question)
    except (VectorDbError, EmbeddingError, SpendLimitReached) as error:
        print(error)
        return

    print(f"Question: {question}")
    print(f"Minimum similarity to count as an answer: {min_similarity}")
    print()

    for match in matches:
        if match["similarity"] >= min_similarity:
            verdict = "USED"
        else:
            verdict = "too far"

        first_line = match["content"].splitlines()[0]
        print(f"{match['similarity']:.3f}  {verdict:8}  {match['source']}  |  {first_line}")

    if not any(match["similarity"] >= min_similarity for match in matches):
        print()
        print("Nothing is close enough: the assistant would say it does not know.")


if __name__ == "__main__":
    main()
