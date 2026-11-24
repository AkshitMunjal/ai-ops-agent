import pytest

from rag import ingest
from rag.embedder import EmbeddingError
from rag.settings import EMBEDDING_SIZE


class FakeResult:
    def __init__(self, rows):
        self.rows = rows

    def fetchall(self):
        return self.rows


class FakeConnection:
    def __init__(self, old_sources=()):
        self.statements = []
        self.old_sources = old_sources
        self.committed = False
        self.closed = False

    def execute(self, sql, params=None):
        self.statements.append((sql, params))
        if sql.startswith("SELECT DISTINCT source"):
            return FakeResult([(source,) for source in self.old_sources])
        return FakeResult([])

    def commit(self):
        self.committed = True

    def close(self):
        self.closed = True

    def statements_starting_with(self, start):
        return [item for item in self.statements if item[0].startswith(start)]


def fake_embed(texts):
    return [[0.0] * EMBEDDING_SIZE for _ in texts]


@pytest.fixture
def knowledge(tmp_path):
    (tmp_path / "payment.md").write_text(
        "# Payment\n\n## Terms\n- 30 days\n\n## Reminders\n- Every 7 days\n", encoding="utf-8"
    )
    (tmp_path / "returns.txt").write_text("# Returns\n\n## Rule\n- 7 days\n", encoding="utf-8")
    (tmp_path / "image.png").write_bytes(b"not a document")
    return tmp_path


def test_only_md_and_txt_files_are_read(knowledge):
    names = [path.name for path in ingest.find_documents(knowledge)]

    assert names == ["payment.md", "returns.txt"]


def test_documents_are_stored_and_committed(knowledge, monkeypatch):
    connection = FakeConnection()
    monkeypatch.setattr(ingest, "embed_texts", fake_embed)
    monkeypatch.setattr(ingest, "connect", lambda: connection)

    summary = ingest.ingest_folder(knowledge)

    assert summary == {"documents": 2, "chunks": 3}
    assert len(connection.statements_starting_with("INSERT")) == 3
    assert len(connection.statements_starting_with("DELETE")) >= 2
    assert connection.committed is True
    assert connection.closed is True


def test_chunk_numbers_start_at_zero_for_each_document(knowledge, monkeypatch):
    connection = FakeConnection()
    monkeypatch.setattr(ingest, "embed_texts", fake_embed)
    monkeypatch.setattr(ingest, "connect", lambda: connection)

    ingest.ingest_folder(knowledge)

    inserts = connection.statements_starting_with("INSERT")
    payment_numbers = [params[1] for sql, params in inserts if params[0] == "payment.md"]
    assert payment_numbers == [0, 1]


def test_a_document_that_was_deleted_is_removed(knowledge, monkeypatch):
    connection = FakeConnection(old_sources=["payment.md", "old_policy.md"])
    monkeypatch.setattr(ingest, "embed_texts", fake_embed)
    monkeypatch.setattr(ingest, "connect", lambda: connection)

    ingest.ingest_folder(knowledge)

    deletes = connection.statements_starting_with("DELETE")
    deleted_sources = [params[0] for sql, params in deletes]
    assert "old_policy.md" in deleted_sources


def test_if_embedding_fails_the_database_is_not_touched(knowledge, monkeypatch):
    opened = []

    def failing_embed(texts):
        raise EmbeddingError("service down")

    monkeypatch.setattr(ingest, "embed_texts", failing_embed)
    monkeypatch.setattr(ingest, "connect", lambda: opened.append(True))

    with pytest.raises(EmbeddingError):
        ingest.ingest_folder(knowledge)

    assert opened == []
