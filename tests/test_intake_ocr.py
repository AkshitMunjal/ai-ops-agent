from email.message import EmailMessage
from pathlib import Path

import httpx
import pypdfium2 as pdfium
import pytest

from cost_control.limit import SpendLimitReached
from intake import pdf_reader
from intake.email_reader import read_email_bytes
from intake.pdf_reader import PdfTextError, read_pdf_bytes
from intake.submit import TryLaterError

samples_folder = Path(__file__).parent / "samples"


def make_scanned_pdf(tmp_path, pages=1):
    source_document = pdfium.PdfDocument(str(samples_folder / "order_gupta.pdf"))
    source_page = source_document[0]
    page_picture = source_page.render(scale=1).to_pil().convert("RGB")

    all_pictures = [page_picture] * pages
    scanned_path = tmp_path / "scanned.pdf"
    all_pictures[0].save(scanned_path, save_all=True, append_images=all_pictures[1:])

    return scanned_path.read_bytes()


@pytest.fixture
def fake_ai(monkeypatch):
    calls = []

    def fake_ask(instruction, picture_links):
        calls.append(picture_links)
        return "Steel Bolts M8 x 25"

    monkeypatch.setattr(pdf_reader, "ask_llm_with_pictures", fake_ask)
    return calls


def make_ai_fail(monkeypatch, error):
    def failing_ask(instruction, picture_links):
        raise error

    monkeypatch.setattr(pdf_reader, "ask_llm_with_pictures", failing_ask)


def make_status_error(status_code):
    request = httpx.Request("POST", "http://test/ai")
    response = httpx.Response(status_code, request=request)
    return httpx.HTTPStatusError("bad status", request=request, response=response)


def test_a_scanned_pdf_is_read_by_the_ai(tmp_path, fake_ai):
    text = read_pdf_bytes(make_scanned_pdf(tmp_path))

    assert text == "Steel Bolts M8 x 25"
    assert len(fake_ai) == 1
    assert fake_ai[0][0].startswith("data:image/jpeg;base64,")


def test_every_page_of_a_scanned_pdf_is_sent(tmp_path, fake_ai):
    read_pdf_bytes(make_scanned_pdf(tmp_path, pages=3))

    assert len(fake_ai[0]) == 3


def test_a_normal_pdf_never_calls_the_ai(fake_ai):
    pdf_bytes = (samples_folder / "order_gupta.pdf").read_bytes()

    text = read_pdf_bytes(pdf_bytes)

    assert "Gupta" in text
    assert fake_ai == []


def test_a_scanned_pdf_with_too_many_pages_is_refused_without_calling_the_ai(tmp_path, fake_ai):
    with pytest.raises(PdfTextError) as error:
        read_pdf_bytes(make_scanned_pdf(tmp_path, pages=6))

    assert "6 pages" in str(error.value)
    assert fake_ai == []


def test_code_fences_around_the_text_are_removed(tmp_path, monkeypatch):
    def fenced_ask(instruction, picture_links):
        return "```\nSteel Bolts M8 x 25\n```"

    monkeypatch.setattr(pdf_reader, "ask_llm_with_pictures", fenced_ask)

    assert read_pdf_bytes(make_scanned_pdf(tmp_path)) == "Steel Bolts M8 x 25"


def test_an_empty_ai_reply_is_an_error(tmp_path, monkeypatch):
    def empty_ask(instruction, picture_links):
        return "   "

    monkeypatch.setattr(pdf_reader, "ask_llm_with_pictures", empty_ask)

    with pytest.raises(PdfTextError):
        read_pdf_bytes(make_scanned_pdf(tmp_path))


def test_the_spend_limit_means_try_later(tmp_path, monkeypatch):
    make_ai_fail(monkeypatch, SpendLimitReached("Daily spend limit of $1 reached"))

    with pytest.raises(TryLaterError):
        read_pdf_bytes(make_scanned_pdf(tmp_path))


def test_the_ai_service_being_down_means_try_later(tmp_path, monkeypatch):
    make_ai_fail(monkeypatch, httpx.ConnectError("connection refused"))

    with pytest.raises(TryLaterError):
        read_pdf_bytes(make_scanned_pdf(tmp_path))


def test_a_429_from_the_ai_service_means_try_later(tmp_path, monkeypatch):
    make_ai_fail(monkeypatch, make_status_error(429))

    with pytest.raises(TryLaterError):
        read_pdf_bytes(make_scanned_pdf(tmp_path))


def test_a_401_from_the_ai_service_is_a_normal_error(tmp_path, monkeypatch):
    make_ai_fail(monkeypatch, make_status_error(401))

    with pytest.raises(PdfTextError):
        read_pdf_bytes(make_scanned_pdf(tmp_path))


def build_email_with_pdf(pdf_bytes):
    message = EmailMessage()
    message["From"] = "rakesh@example.com"
    message["Subject"] = "Order"
    message.set_content("Please see the attached order.")
    message.add_attachment(pdf_bytes, maintype="application", subtype="pdf", filename="scan.pdf")
    return message.as_bytes()


def test_an_email_with_a_scanned_pdf_includes_the_ai_text(tmp_path, fake_ai):
    raw_email = build_email_with_pdf(make_scanned_pdf(tmp_path))

    text = read_email_bytes(raw_email)

    assert "Attachment scan.pdf:" in text
    assert "Steel Bolts M8 x 25" in text


def test_try_later_travels_out_of_the_email_reader(tmp_path, monkeypatch):
    make_ai_fail(monkeypatch, SpendLimitReached("Daily spend limit of $1 reached"))
    raw_email = build_email_with_pdf(make_scanned_pdf(tmp_path))

    with pytest.raises(TryLaterError):
        read_email_bytes(raw_email)