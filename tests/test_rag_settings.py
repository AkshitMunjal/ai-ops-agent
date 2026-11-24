import psycopg
import pytest

from rag import vector_db
from rag.settings import DEFAULT_VECTOR_URL, get_embedding_model, get_vector_url


def test_vector_url_has_a_default(monkeypatch):
    monkeypatch.delenv("VECTOR_DATABASE_URL", raising=False)
    assert get_vector_url() == DEFAULT_VECTOR_URL


def test_vector_url_can_be_set(monkeypatch):
    monkeypatch.setenv("VECTOR_DATABASE_URL", "postgresql://u:p@vectordb:5432/x")
    assert get_vector_url() == "postgresql://u:p@vectordb:5432/x"


def test_embedding_model_default_and_override(monkeypatch):
    monkeypatch.delenv("EMBEDDING_MODEL", raising=False)
    assert get_embedding_model() == "openai/text-embedding-3-small"
    monkeypatch.setenv("EMBEDDING_MODEL", "other/model")
    assert get_embedding_model() == "other/model"


def test_connect_gives_a_clear_error_when_database_is_down(monkeypatch):
    def refuse(*args, **kwargs):
        raise psycopg.OperationalError("connection refused")

    monkeypatch.setattr(vector_db.psycopg, "connect", refuse)

    with pytest.raises(vector_db.VectorDbError) as error:
        vector_db.connect()

    assert "Docker Desktop" in str(error.value)
