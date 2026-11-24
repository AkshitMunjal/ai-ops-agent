import pytest

from rag import retriever
from rag.settings import EMBEDDING_SIZE


class FakeResult:
    def __init__(self, rows):
        self.rows = rows

    def fetchall(self):
        return self.rows


class FakeConnection:
    def __init__(self, rows):
        self.rows = rows
        self.closed = False
        self.last_params = None

    def execute(self, sql, params=None):
        self.last_params = params
        return FakeResult(self.rows)

    def close(self):
        self.closed = True


@pytest.fixture
def database(monkeypatch):
    rows = [
        ("payment_terms.md", 0, "Payment terms: Standard terms\n- 30 days", 0.62),
        ("delivery_policy.md", 1, "Delivery policy: Charges\n- 150 rupees", 0.21),
    ]
    connection = FakeConnection(rows)
    monkeypatch.setattr(retriever, "embed_texts", lambda texts: [[0.0] * EMBEDDING_SIZE])
    monkeypatch.setattr(retriever, "connect", lambda: connection)
    monkeypatch.delenv("RAG_MIN_SIMILARITY", raising=False)
    return connection


def test_search_returns_every_match_with_its_similarity(database):
    matches = retriever.search_documents("When must I pay?")

    assert [match["source"] for match in matches] == ["payment_terms.md", "delivery_policy.md"]
    assert matches[0]["similarity"] == 0.62
    assert database.closed is True


def test_only_close_matches_count_as_relevant(database):
    relevant = retriever.find_relevant_documents("When must I pay?")

    assert [match["source"] for match in relevant] == ["payment_terms.md"]


def test_nothing_close_gives_an_empty_list(database, monkeypatch):
    monkeypatch.setenv("RAG_MIN_SIMILARITY", "0.9")

    assert retriever.find_relevant_documents("What is the weather?") == []


def test_the_limit_is_passed_to_the_query(database):
    retriever.search_documents("anything", limit=2)

    assert database.last_params[2] == 2
