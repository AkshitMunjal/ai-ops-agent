import httpx
import pytest

from cost_control.limit import SpendLimitReached
from rag import embedder
from rag.settings import EMBEDDING_SIZE


class FakeResponse:
    def __init__(self, data):
        self.data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self.data


def make_vector(value):
    return [value] * EMBEDDING_SIZE


@pytest.fixture
def calls(monkeypatch):
    """Fake the spend check, the usage saving and the web call."""
    recorded = {"posts": [], "usage": []}

    monkeypatch.setattr(embedder, "check_spend_limit", lambda: None)
    monkeypatch.setattr(embedder, "record_usage", lambda model, usage: recorded["usage"].append(usage))

    def fake_post(url, headers=None, json=None, timeout=None):
        recorded["posts"].append(json)
        items = []
        for position, _ in enumerate(json["input"]):
            items.append({"index": position, "embedding": make_vector(float(position))})
        return FakeResponse({"data": items, "usage": {"prompt_tokens": 5, "cost": 0.0001}})

    monkeypatch.setattr(embedder.httpx, "post", fake_post)
    return recorded


def test_vectors_come_back_in_order(calls):
    vectors = embedder.embed_texts(["a", "b", "c"])

    assert len(vectors) == 3
    assert vectors[0][0] == 0.0
    assert vectors[2][0] == 2.0


def test_many_texts_are_sent_in_batches(calls):
    texts = [f"text {number}" for number in range(120)]

    vectors = embedder.embed_texts(texts)

    assert len(vectors) == 120
    assert len(calls["posts"]) == 3
    assert len(calls["posts"][0]["input"]) == embedder.BATCH_SIZE


def test_the_usage_is_saved(calls):
    embedder.embed_texts(["a"])

    assert calls["usage"] == [{"prompt_tokens": 5, "cost": 0.0001}]


def test_a_failure_while_saving_usage_does_not_break_the_answer(calls, monkeypatch):
    def broken_record(model, usage):
        raise RuntimeError("database locked")

    monkeypatch.setattr(embedder, "record_usage", broken_record)

    assert len(embedder.embed_texts(["a"])) == 1


def test_no_texts_means_no_web_call(calls):
    assert embedder.embed_texts([]) == []
    assert calls["posts"] == []


def test_the_spend_limit_stops_the_call(calls, monkeypatch):
    def limit_reached():
        raise SpendLimitReached("Daily spend limit of $1 reached")

    monkeypatch.setattr(embedder, "check_spend_limit", limit_reached)

    with pytest.raises(SpendLimitReached):
        embedder.embed_texts(["a"])

    assert calls["posts"] == []


def test_a_web_error_becomes_a_clear_error(monkeypatch):
    monkeypatch.setattr(embedder, "check_spend_limit", lambda: None)

    def failing_post(*args, **kwargs):
        raise httpx.ConnectError("no network")

    monkeypatch.setattr(embedder.httpx, "post", failing_post)

    with pytest.raises(embedder.EmbeddingError):
        embedder.embed_texts(["a"])


def test_the_wrong_vector_size_is_refused(monkeypatch):
    monkeypatch.setattr(embedder, "check_spend_limit", lambda: None)
    monkeypatch.setattr(embedder, "record_usage", lambda model, usage: None)

    def short_post(url, headers=None, json=None, timeout=None):
        return FakeResponse({"data": [{"index": 0, "embedding": [0.1, 0.2]}]})

    monkeypatch.setattr(embedder.httpx, "post", short_post)

    with pytest.raises(embedder.EmbeddingError) as error:
        embedder.embed_texts(["a"])

    assert "EMBEDDING_MODEL" in str(error.value)


def test_an_answer_without_data_is_refused(monkeypatch):
    monkeypatch.setattr(embedder, "check_spend_limit", lambda: None)
    monkeypatch.setattr(embedder, "record_usage", lambda model, usage: None)
    monkeypatch.setattr(
        embedder.httpx, "post", lambda *args, **kwargs: FakeResponse({"error": "bad"})
    )

    with pytest.raises(embedder.EmbeddingError):
        embedder.embed_texts(["a"])
